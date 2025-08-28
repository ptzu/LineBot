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
    TextSendMessage, ImageSendMessage, QuickReply, QuickReplyButton
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

REPLICATE_MODEL = "flux-kontext-apps/restore-image"  # flux-kontext-apps/restore-image

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
    user_message = event.message.text
    
    # 處理功能選單命令
    if user_message == "!功能":
        quick_reply_buttons = [
            QuickReplyButton(action=TextSendMessage(text="📸 圖片彩色化")),
            QuickReplyButton(action=TextSendMessage(text="💬 文字回覆")),
            QuickReplyButton(action=TextSendMessage(text="❓ 使用說明")),
            QuickReplyButton(action=TextSendMessage(text="🔧 其他功能"))
        ]
        
        quick_reply = QuickReply(items=quick_reply_buttons)
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="🤖 請選擇您想要的功能：",
                quick_reply=quick_reply
            )
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
        # 將 bytes 轉換為 base64 格式
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{image_b64}"
        
        # 使用 Replicate Python SDK
        output = replicate.run(
            REPLICATE_MODEL,
            input={
                "input_image": image_data_url,
            }
        )
        
        if output:
            # 如果 output 是字串（URL），直接回傳
            if isinstance(output, str):
                return output
            # 如果 output 是列表，回傳第一個元素
            elif isinstance(output, list) and len(output) > 0:
                return output[0]
            # 如果 output 是 FileOutput 物件，轉換為字串
            else:
                return str(output)
        else:
            raise Exception("API 沒有回傳結果")
            
    except Exception as e:
        print(f"Replicate API 錯誤: {str(e)}")
        if "Insufficient credit" in str(e):
            raise Exception("Replicate 點數不足，請前往 https://replicate.com/account/billing#billing 購買點數")
        else:
            raise Exception(f"彩色化處理失敗: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
