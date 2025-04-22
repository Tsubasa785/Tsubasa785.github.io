import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
from langdetect import detect

app = Flask(__name__)

# 環境変数からLINEとOpenAIのキーを取得
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    try:
        lang = detect(user_message)
    except:
        lang = "unknown"

    prompt = ""
    if lang == "ja":
        prompt = f"Translate the following Japanese text into both English and Spanish:\n\n{user_message}"
    elif lang == "en":
        prompt = f"Translate the following English text into Spanish:\n\n{user_message}"
    elif lang == "es":
        prompt = f"Translate the following Spanish text into English:\n\n{user_message}"
    else:
        return  # 未対応の言語は無視

    # OpenAI APIで翻訳
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )

    translated_text = response.choices[0].message.content.strip()

    # 翻訳を返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
