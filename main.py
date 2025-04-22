from flask import Flask, request
import os
import requests
import openai
from langdetect import detect

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
LINE_TOKEN = os.getenv("LINE_TOKEN")

# 言語を自動判定（ja / en / es）
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

            prompts = []

            if lang == "en":
                prompts.append(("Spanish", f"Translate the following English sentence into Spanish:\n{msg}"))
            elif lang == "es":
                prompts.append(("English", f"Translate the following Spanish sentence into English:\n{msg}"))
            elif lang == "ja":
                prompts.append(("English", f"Translate the following Japanese sentence into English:\n{msg}"))
                prompts.append(("Spanish", f"Translate the following Japanese sentence into Spanish:\n{msg}"))
            else:
                prompts.append(("Info", "Sorry, only English, Spanish, and Japanese are supported."))

            replies = []
            for target, prompt in prompts:
                try:
                    res = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    translated = res.choices[0].message["content"].strip()
                except Exception as e:
                    translated = f"[{target} translation error]\n{str(e)}"

                replies.append({"type": "text", "text": translated})

            reply_data = {
                "replyToken": event["replyToken"],
                "messages": replies
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
