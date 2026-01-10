## 前提
- テストでアクセスしているサイトにアクセスできる権限があること
- 組織情報にアクセスできる権限があること

## セットアップ
- mcp-bridge/mcp-server/config配下に対象サイトにアクセスするための中間証明書をブラウザから取得し、`intermediate.crt`として保存
- mcp-bridge/mcp-server/config配下に`logininfo.json`として保存
```
{
    "ENGAGE_CODE": "${会社名小文字}",
    "USER_ID": "${ログインユーザID}",
    "PASSWORD": "${ログインパスワード}"
}
```
- mcp-bridge/mcp-server/config配下に`url.json`として保存
```
{
    "LOGIN": "${ログイン用URL}$",
    "GET_DIVISION_MASTER": "${事業部マスタ取得用URL}",
    "GET_DEPARTMENT_MASTER": "${部門マスタ取得用URL}",
    "GET_GROUP_MASTER": "${グループマスタ取得用URL}"
}
```
- sudo docker compose up -d --build
- sudo docker compose exec ollama ollama pull okamototk/llama-swallow:8b
- sudo docker compose down

## 起動
- sudo docker compose up -d

## アクセス
- http://localhost:8080

## 開発環境利用
- sudo docker compose up -d
- sudo docker exec -it python-dev bash