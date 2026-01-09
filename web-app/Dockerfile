FROM python:3.11-slim

# curl インストール（healthcheckやデバッグ用）
RUN apt-get update && apt-get install -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# コンテナ内作業ディレクトリ
WORKDIR /web-app

# requirements をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# uvicorn で FastAPI を起動
# モジュール名を web-app.py に変更したので web_app:app にする
CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8080"]
