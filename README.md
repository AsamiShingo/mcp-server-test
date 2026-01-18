## 前提
- アクセスしているサイトにアクセスできる権限があること
- 取得対象の情報を参照できる権限があること
- 会社情報の取り方をぼかすため、あえてURL等のアクセスに必要な情報は分からないようにしています

## セットアップ
- mcp-newarp/config配下に対象サイトにアクセスするための中間証明書をブラウザから取得し、`intermediate.crt`として保存
- mcp-newarp/config配下に`logininfo.json`として保存
```
{
    "ENGAGE_CODE": "${会社名小文字}",
    "USER_ID": "${ログインユーザID}",
    "PASSWORD": "${ログインパスワード}",
    "PROC_USER_KEY": "${利用者のユーザキー}"
    "FB_INTERVIEW_YEAR_MONTH": [ "${FB面談対象年月yyyymm}", "${FB面談対象年月yyyymm}" ]
}
```
- mcp-newarp/config配下に`url.json`として保存
```
{
    "LOGIN": "${ログイン用URL}",
    "GET_DIVISION_MASTER": "${事業部マスタ取得用URL}",
    "GET_DIVISION_MASTER_REFERER": "${事業部マスタ取得用RefererURL}",
    "GET_DEPARTMENT_MASTER": "${部門マスタ取得用URL}",
    "GET_DEPARTMENT_MASTER_REFERER": "${部門マスタ取得用RefererURL}",
    "GET_GROUP_MASTER": "${グループマスタ取得用URL}",
    "GET_GROUP_MASTER_REFERER": "${グループマスタ取得用RefererURL}",
    "GET_USER_MASTER": "${ユーザマスタ取得用URL}",
    "GET_USER_MASTER_REFERER": "${ユーザマスタ取得用RefererURL}"
    "GET_USER_MASTER": "${ユーザマスタ取得用URL}",
    "GET_USER_MASTER_REFERER": "${ユーザマスタ取得用RefererURL}",
    "GET_FB_INTERVIEW_SHEET": "${FB面談シート取得用URL}",
    "GET_FB_INTERVIEW_SHEET_REFERER": "${FB面談シート取得用RefererURL}",
    "GET_EVALUATION": "${評価ABC取得用URL}",
    "GET_EVALUATION_REFERER": "${評価ABC取得用URL}"
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
- sudo docker compose up -d python-dev
- sudo docker exec -it python-dev bash
- docker内でコンパイル等実施
- sudo docker compose down python-dev