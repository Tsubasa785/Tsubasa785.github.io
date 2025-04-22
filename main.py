from flask import Flask, request
import os
import requests
import openai
from langdetect import detect

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")

# 簡易履歴保存（ユーザー単位で持たせるなら辞書化が必要）
chat_history = []

def detect_language(text):
    try:
        lang = detect(text)
        return lang if lang in ["en", "es", "ja"] else "other"
    except:
        return "other"

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    print("=== Webhook Received ===")
    print(body)

    for event in body.get("events", []):
        if event["type"] == "message" and event["message"]["type"] == "text":
            msg = event["message"]["text"]
            lang = detect_language(msg)

            # 翻訳の対象と言語設定
            if lang == "en":
                system_prompt = "You are a professional translator. Translate from English to Spanish only. Do not explain."
            elif lang == "es":
                system_prompt = "You are a professional translator. Translate from Spanish to English only. Do not explain."
            elif lang == "ja":
                system_prompt = "You are a professional translator. Translate from Japanese to English and Spanish only. Do not explain."
            else:
                reply = {"type": "text", "text": "Only Japanese, English, and Spanish are supported."}
                reply_data = {
                    "replyToken": event["replyToken"],
                    "messages": [reply]
                }
                headers = {
                    "Authorization": f"Bearer {LINE_TOKEN}",
                    "Content-Type": "application/json"
                }
                requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=reply_data)
                continue

            # チャット履歴構築（翻訳コンテキスト保持）
            chat_history.clear()
            chat_history.append({"role": "system", "content": system_prompt})
            chat_history.append({"role": "user", "content": msg})

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=chat_history
                )
                translated = response.choices[0].message["content"].strip()
            except Exception as e:
                translated = f"[Translation error]\n{str(e)}"

            reply = {"type": "text", "text": translated}

            reply_data = {
                "replyToken": event["replyToken"],
                "messages": [reply]
            }

            headers = {
                "Authorization": f"Bearer {LINE_TOKEN}",
                "Content-Type": "application/json"
            }

            requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=reply_data)

    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
