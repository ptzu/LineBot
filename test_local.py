"""
本地端 Line Bot 測試程式
模擬收到訊息並測試處理邏輯
"""

import os
import sys
import time
import base64
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from mock_events import MockTextEvent, MockImageEvent, TEST_EVENTS

# 設定環境變數（測試用）
os.environ["CHANNEL_ACCESS_TOKEN"] = "test_token"
os.environ["CHANNEL_SECRET"] = "test_secret"
os.environ["REPLICATE_API_TOKEN"] = "test_replicate_token"

# 匯入 app.py 中的函數
from app import handle_text, handle_image, colorize_image

class MockLineBotApi:
    """模擬 Line Bot API"""
    def __init__(self):
        self.reply_messages = []
        self.push_messages = []
    
    def reply_message(self, reply_token, message):
        """模擬回覆訊息"""
        self.reply_messages.append({
            'reply_token': reply_token,
            'message': message,
            'timestamp': datetime.now()
        })
        print(f"📤 回覆訊息: {message.text if hasattr(message, 'text') else '圖片訊息'}")
    
    def push_message(self, user_id, message):
        """模擬推送訊息"""
        self.push_messages.append({
            'user_id': user_id,
            'message': message,
            'timestamp': datetime.now()
        })
        print(f"📤 推送訊息給 {user_id}: {message.text if hasattr(message, 'text') else '圖片訊息'}")
    
    def get_message_content(self, message_id):
        """模擬取得訊息內容"""
        # 這裡會回傳模擬的圖片內容
        mock_content = Mock()
        mock_content.iter_content.return_value = [b'fake_image_data']
        return mock_content

class LocalTester:
    """本地端測試器"""
    
    def __init__(self, mock_replicate=True):
        self.mock_replicate = mock_replicate
        self.mock_api = MockLineBotApi()
        self.test_results = []
    
    def test_text_message(self, event_name, event):
        """測試文字訊息處理"""
        print(f"\n🧪 測試文字訊息: {event_name}")
        print(f"📝 輸入文字: {event.message.text}")
        
        start_time = time.time()
        
        try:
            # 模擬 line_bot_api
            with patch('app.line_bot_api', self.mock_api):
                handle_text(event)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'test_type': 'text',
                'event_name': event_name,
                'input_text': event.message.text,
                'success': True,
                'processing_time': processing_time,
                'reply_count': len(self.mock_api.reply_messages),
                'push_count': len(self.mock_api.push_messages)
            }
            
            print(f"✅ 測試成功 - 處理時間: {processing_time:.2f}秒")
            print(f"📊 回覆訊息數: {result['reply_count']}, 推送訊息數: {result['push_count']}")
            
            # 特殊驗證：功能選單測試
            if event.message.text == "!功能":
                print("🔍 功能選單特殊驗證:")
                if result['reply_count'] > 0:
                    print(f"   ✅ Bot 有回覆功能選單 - 回覆數: {result['reply_count']}")
                    # 檢查回覆內容
                    for i, reply_data in enumerate(self.mock_api.reply_messages):
                        message = reply_data['message']
                        print(f"   📤 回覆 {i+1}: {type(message).__name__}")
                        if hasattr(message, 'text'):
                            print(f"      內容: {message.text[:50]}...")
                else:
                    print("   ❌ Bot 沒有回覆功能選單")
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'test_type': 'text',
                'event_name': event_name,
                'input_text': event.message.text,
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
            
            print(f"❌ 測試失敗: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_image_message(self, image_path=None):
        """測試圖片訊息處理"""
        print(f"\n🧪 測試圖片訊息處理")
        
        if not image_path or not os.path.exists(image_path):
            print("⚠️  找不到測試圖片，使用模擬圖片")
            image_path = None
        
        event = MockImageEvent(image_path)
        start_time = time.time()
        
        try:
            # 模擬 line_bot_api 和 replicate
            with patch('app.line_bot_api', self.mock_api):
                if self.mock_replicate:
                    with patch('app.replicate') as mock_replicate:
                        mock_replicate.run.return_value = "https://example.com/colorized_image.jpg"
                        handle_image(event)
                else:
                    handle_image(event)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'test_type': 'image',
                'image_path': image_path,
                'success': True,
                'processing_time': processing_time,
                'reply_count': len(self.mock_api.reply_messages),
                'push_count': len(self.mock_api.push_messages)
            }
            
            print(f"✅ 圖片處理成功 - 處理時間: {processing_time:.2f}秒")
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            result = {
                'test_type': 'image',
                'image_path': image_path,
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
            
            print(f"❌ 圖片處理失敗: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    def test_colorize_image(self, image_path):
        """測試圖片彩色化功能"""
        print(f"\n🧪 測試圖片彩色化: {image_path}")
        
        if not os.path.exists(image_path):
            print(f"❌ 找不到圖片檔案: {image_path}")
            return None
        
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            start_time = time.time()
            
            if self.mock_replicate:
                # 模擬 Replicate API 回應
                with patch('app.replicate') as mock_replicate:
                    mock_replicate.run.return_value = "https://example.com/colorized_image.jpg"
                    output_url = colorize_image(image_bytes)
            else:
                # 實際呼叫 Replicate API
                output_url = colorize_image(image_bytes)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ 彩色化成功 - 處理時間: {processing_time:.2f}秒")
            print(f"🔗 輸出URL: {output_url}")
            
            return {
                'success': True,
                'output_url': output_url,
                'processing_time': processing_time
            }
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"❌ 彩色化失敗: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def run_all_tests(self):
        """執行所有測試"""
        print("🚀 開始執行本地端 Line Bot 測試")
        print("=" * 50)
        
        # 測試所有文字訊息
        for event_name, event in TEST_EVENTS.items():
            self.test_text_message(event_name, event)
        
        # 測試圖片處理（如果有測試圖片）
        test_images = [
            "test_images/test1.jpg",
            "test_images/test2.png",
            "test_images/test3.jpeg"
        ]
        
        for image_path in test_images:
            if os.path.exists(image_path):
                self.test_image_message(image_path)
                self.test_colorize_image(image_path)
        
        # 如果沒有測試圖片，至少測試圖片處理邏輯
        if not any(os.path.exists(img) for img in test_images):
            self.test_image_message()
        
        self.print_summary()
    
    def print_summary(self):
        """印出測試摘要"""
        print("\n" + "=" * 50)
        print("📊 測試摘要")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - successful_tests
        
        print(f"總測試數: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失敗: {failed_tests}")
        print(f"成功率: {(successful_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失敗的測試:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result.get('event_name', result.get('test_type', 'Unknown'))}: {result.get('error', 'Unknown error')}")
        
        print("\n📝 詳細結果:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            test_name = result.get('event_name', result.get('test_type', 'Unknown'))
            print(f"  {status} {test_name} ({result['processing_time']:.2f}s)")

def main():
    """主程式"""
    print("🤖 Line Bot 本地端測試工具")
    print("請選擇測試模式:")
    print("1. 模擬模式 (不呼叫 Replicate API)")
    print("2. 真實模式 (會呼叫 Replicate API)")
    
    try:
        choice = input("請輸入選擇 (1/2): ").strip()
        mock_mode = choice == "1"
        
        if mock_mode:
            print("🔧 使用模擬模式")
        else:
            print("🌐 使用真實模式 (會消耗 Replicate 點數)")
        
        tester = LocalTester(mock_replicate=mock_mode)
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  測試被中斷")
    except Exception as e:
        print(f"\n❌ 執行測試時發生錯誤: {str(e)}")

if __name__ == "__main__":
    main()
