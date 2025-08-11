import os
import base64
import tempfile
import requests
import replicate
import threading
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    TextSendMessage, ImageSendMessage
)

app = Flask(__name__)

# 驗證環境變數
if not os.getenv("CHANNEL_ACCESS_TOKEN"):
    raise ValueError("CHANNEL_ACCESS_TOKEN 環境變數未設定")
if not os.getenv("CHANNEL_SECRET"):
    raise ValueError("CHANNEL_SECRET 環境變數未設定")
if not os.getenv("REPLICATE_API_TOKEN"):
    raise ValueError("REPLICATE_API_TOKEN 環境變數未設定")

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# 設定 Replicate API token
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

REPLICATE_MODEL = "arielreplicate/deoldify_image"  # DeOldify 彩色化模型

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
    try:
        # 1. 從 LINE 下載圖片
        message_content = line_bot_api.get_message_content(event.message.id)
        image_bytes = b''.join(chunk for chunk in message_content.iter_content())

        # 2. 先回覆用戶正在處理
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="正在處理您的圖片，請稍候...")
        )

        # 3. 在背景執行彩色化處理
        def process_image_async():
            try:
                output_url = colorize_image(image_bytes)
                # 回傳彩色圖片
                line_bot_api.push_message(
                    event.source.user_id,
                    ImageSendMessage(
                        original_content_url=output_url,
                        preview_image_url=output_url
                    )
                )
            except Exception as e:
                # 回傳錯誤訊息
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text=f"處理圖片時發生錯誤: {str(e)}")
                )

        # 啟動背景執行緒
        thread = threading.Thread(target=process_image_async)
        thread.start()

    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"發生錯誤: {str(e)}")
        )

def colorize_image(image_bytes):
    """呼叫 Replicate 彩色化 API"""
    try:
        # 使用 Replicate Python SDK
        output = replicate.run(
            REPLICATE_MODEL,
            input={"image": image_bytes}
        )
        
        if output and len(output) > 0:
            return output[0]  # 回傳第一個結果
        else:
            raise Exception("API 沒有回傳結果")
            
    except Exception as e:
        print(f"Replicate API 錯誤: {str(e)}")
        raise Exception(f"彩色化處理失敗: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
