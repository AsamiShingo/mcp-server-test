from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import requests
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

@app.post("/chat")
def chat(req: ChatRequest):
    user_id = req.user_id
    user_message = req.message

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # 最新メッセージを追加
    conversation_history[user_id].append({"role": "user", "content": user_message})

    # 履歴を MAX_HISTORY 件に制限
    if len(conversation_history[user_id]) > MAX_HISTORY:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]

    # Ollama に送信
    payload = {
        "model": MODEL_NAME,
        "messages": conversation_history[user_id],
        "stream": False
    }

    try:
        resp = requests.post(BRIDGE_URL, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        ai_message = result.get('message', {}).get('content', 'AIから応答が返っていません')

        # AI の応答も履歴に追加
        conversation_history[user_id].append({"role": "assistant", "content": ai_message})

        # 応答追加後に再度件数制限
        if len(conversation_history[user_id]) > MAX_HISTORY:
            conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]

        return {"reply": ai_message}

    except Exception as e:
        print("error " + str(e))
        return {"reply": f"エラー: {e}"}

@app.get("/")
def root():
    return FileResponse("index.html")
