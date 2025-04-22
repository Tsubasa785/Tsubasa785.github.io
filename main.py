from flask import Flask, request
import os
import requests
import openai

app = Flask(__name__)

# OpenAI APIキーを環境変数から取得（v0.28形式）
openai.api_key = os.getenv("OPENAI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    print("=== Webhook Received ===")
    print(body)  # デバッグ用

    for event in body.get("events", []):
        if event["type"] == "message" and event["message"]["type"] == "text":
            msg = event["message"]["text"]

            # 英語かスペイン語かの判定（ASCII文字なら英語とみなす）
            lang = "es" if any(ord(c) < 128 for c in msg) else "en"
            prompt = f"Translate this to {'Spanish' if lang == 'es' else 'English'}:\n{msg}"

            try:
                res = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                translated = res.choices[0].message["content"].strip()
            except Exception as e:
                translated = f"[Translation error]\n{str(e)}"

            reply = {
                "replyToken": event["replyToken"],
                "messages": [{"type": "text", "text": translated}]
            }

            headers = {
                "Authorization": f"Bearer {LINE_TOKEN}",
                "Content-Type": "application/json"
            }

            requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=reply)

    return "OK"

# Renderで必要なFlask起動設定
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
