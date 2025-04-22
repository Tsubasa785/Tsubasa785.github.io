from flask import Flask, request
import os
import requests
import openai

app = Flask(__name__)

# OpenAIクライアント初期化（v1系）
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LINE_TOKEN = os.getenv("LINE_TOKEN")

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    print("=== Webhook Received ===")
    print(body)

    for event in body.get("events", []):
        if event["type"] == "message" and event["message"]["type"] == "text":
            msg = event["message"]["text"]

            # 日本語か英語かの判定（ASCII範囲でチェック）
            lang = "es" if any(ord(c) < 128 for c in msg) else "en"
            prompt = f"Translate this to {'Spanish' if lang == 'es' else 'English'}:\n{msg}"

            # OpenAI API呼び出し
            res = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            translated = res.choices[0].message.content.strip()

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


# Flask起動設定（Renderで必要）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
