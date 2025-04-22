from flask import Flask, request
import openai
import os
import requests

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.json
    for event in body["events"]:
        if event["type"] == "message":
            msg = event["message"]["text"]
            lang = "es" if any(ord(c) < 128 for c in msg) else "ja"
            prompt = f"Translate this to {'Spanish' if lang == 'es' else 'Japanese'}:\n{msg}"
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            translated = res.choices[0].message["content"]

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
