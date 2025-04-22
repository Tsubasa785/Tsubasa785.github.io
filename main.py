import os
import openai
from flask import Flask, request, abort
from langdetect import detect_langs
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からAPIキー等を取得
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text

    try:
        langs = detect_langs(text)
        lang_code = langs[0].lang
        confidence = langs[0].prob
    except Exception:
        lang_code = "unknown"
        confidence = 0

    # 翻訳の組み合わせを決定
    if lang_code == "ja":
        prompt = f"日本語を英語とスペイン語に自然な文章で翻訳してください:\n{text}"
    elif lang_code == "en":
        prompt = f"Translate the following English sentence naturally into Spanish:\n{text}"
    elif lang_code == "es":
        prompt = f"Traduce esta frase en español al inglés de forma natural:\n{text}"
    else:
        if confidence < 0.70:
            reply = "Only Japanese, English, and Spanish are supported."
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            return
        else:
            prompt = f"Translate this sentence into English and Spanish:\n{text}"

    # OpenAIへ翻訳依頼
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        reply_text = response['choices'][0]['message']['content'].strip()
    except Exception as e:
        reply_text = "[Translation error] " + str(e)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
