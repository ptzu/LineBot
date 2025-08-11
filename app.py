import os
import base64
import tempfile
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    TextSendMessage, ImageSendMessage
)

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

REPLICATE_MODEL_VERSION = "fb15d64e807e38c0603d9bb95d65a48d33cb8393cd5e356045b63c6f23649e0c"  # DeOldify v2

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    # 簡單 Echo
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # 1. 從 LINE 下載圖片
    message_content = line_bot_api.get_message_content(event.message.id)
    image_bytes = b''.join(chunk for chunk in message_content.iter_content())

    # 2. 轉成 Base64（Replicate 可直接吃）
    image_b64 = "data:image/jpeg;base64," + base64.b64encode(image_bytes).decode()

    # 3. 呼叫 Replicate API
    output_url = colorize_image(image_b64)

    # 4. 回傳彩色圖片
    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
            original_content_url=output_url,
            preview_image_url=output_url
        )
    )

def colorize_image(image_b64):
    """呼叫 Replicate 彩色化 API"""
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "version": REPLICATE_MODEL_VERSION,
        "input": {"image": image_b64}
    }
    res = requests.post(url, json=payload, headers=headers).json()
    prediction_id = res["id"]

    # 等待結果
    while True:
        res = requests.get(f"{url}/{prediction_id}", headers=headers).json()
        if res["status"] in ["succeeded", "failed"]:
            break

    if res["status"] == "succeeded":
        # DeOldify 回傳的是單一 URL
        return res["output"]
    else:
        raise Exception("彩色化失敗")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
