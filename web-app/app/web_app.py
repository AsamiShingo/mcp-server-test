from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import requests
import uuid
import json
from typing import Dict, List

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 環境変数
BRIDGE_URL = os.environ.get('OLLAMA_BRIDGE_URL', 'http://mcp-bridge:8000/api/chat')
MODEL_NAME = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')

# ユーザーごとの会話履歴を保持
conversation_history: Dict[str, List[Dict]] = {}

# 保持する最大件数
MAX_HISTORY =10

class ChatRequest(BaseModel):
    user_id: str
    message: str

def get_or_create_session_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax",
        )
    return session_id

def add_conversation_history(request_key: str, role: str, message: str):
    if request_key not in conversation_history:
        conversation_history[request_key] = []

    conversation_history[request_key].append({"role": role, "content": message})

    if len(conversation_history[request_key]) > MAX_HISTORY:
        conversation_history[request_key] = conversation_history[request_key][-MAX_HISTORY:]

@app.post("/chat")
def chat(req: ChatRequest, request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    request_key = f"{session_id}_{req.user_id}"

    add_conversation_history(request_key, "user", req.message)
    
    request_messages = [
        *conversation_history[request_key],
    ]

    # Ollama に送信
    payload = {
        "model": MODEL_NAME,
        "messages": request_messages,
        "stream": False
    }

    try:
        resp = requests.post(BRIDGE_URL, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        ai_message = result.get('message', {}).get('content', 'AIから応答が返っていません')

        add_conversation_history(request_key, "assistant", ai_message)

        return {"reply": ai_message}

    except Exception as e:
        print(f"web-error: {e}")
        return {"reply": f"エラー: {e}"}

def stream_ollama(request_key: str, message: str):
    add_conversation_history(request_key, "user", message)

    request_messages = [
        *conversation_history[request_key],
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": request_messages,
        "stream": True
    }

    full_reply = ""
    with requests.post(BRIDGE_URL, json=payload, stream=True, timeout=120) as r:
        r.raise_for_status()

        for line in r.iter_lines():
            if not line:
                continue

            data = json.loads(line.decode("utf-8"))

            content = data.get("message", {}).get("content")
            if content:
                full_reply += content
                yield f"data: {json.dumps(content)}\n\n"

        yield "data: [DONE]\n\n"

    add_conversation_history(request_key, "assistant", full_reply)

@app.post("/chat/stream")
def chat_stream(req: ChatRequest, request: Request, response: Response):
    session_id = get_or_create_session_id(request, response)
    request_key = f"{session_id}_{req.user_id}"

    return StreamingResponse(
        stream_ollama(request_key, req.message),
        media_type="text/event-stream"
    )

@app.get("/")
def root():
    return FileResponse("index.html")
