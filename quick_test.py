#!/usr/bin/env python3
"""
快速測試腳本
一鍵執行所有測試
"""

import os
import sys

def main():
    print("🚀 Line Bot 快速測試")
    print("=" * 30)
    
    # 設定環境變數
    os.environ["CHANNEL_ACCESS_TOKEN"] = "test_token"
    os.environ["CHANNEL_SECRET"] = "test_secret"
    os.environ["REPLICATE_API_TOKEN"] = "test_replicate_token"
    
    try:
        # 執行簡化版測試
        print("📝 執行簡化版測試...")
        from test_simple import test_function_menu, test_quick_replies, test_image_processing
        
        test_function_menu()
        test_quick_replies()
        test_image_processing()
        
        print("\n✅ 快速測試完成！")
        print("\n💡 提示：")
        print("  - 使用 'python test_simple.py' 進行詳細測試")
        print("  - 使用 'python test_local.py' 進行完整測試")
        print("  - 將測試圖片放入 'test_images/' 資料夾")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        print("請檢查是否已安裝所需套件：pip install -r requirements.txt")

if __name__ == "__main__":
    main()
