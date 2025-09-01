# Line Bot 本地端測試指南

這個專案提供了完整的本地端測試工具，讓您可以在不部署到伺服器的情況下測試 Line Bot 的功能。

## 📁 檔案結構

```
LineBot/
├── app.py              # 主要的 Line Bot 應用程式
├── test_local.py       # 完整版測試工具
├── test_simple.py      # 簡化版測試工具
├── mock_events.py      # 模擬事件資料結構
├── test_images/        # 測試圖片資料夾
└── README_TEST.md      # 本說明文件
```

## 🚀 快速開始

### 1. 安裝依賴

確保您已經安裝了所需的套件：

```bash
pip install -r requirements.txt
```

### 2. 執行簡化版測試

```bash
python test_simple.py
```

這個測試會：
- 測試功能選單 (`!功能`)
- 測試所有快速回覆選項
- 測試圖片處理邏輯

### 3. 執行完整版測試

```bash
python test_local.py
```

這個測試會：
- 提供互動式選單選擇測試模式
- 執行所有文字訊息測試
- 測試圖片處理（如果有測試圖片）
- 提供詳細的測試報告

## 🧪 測試模式

### 模擬模式 (推薦)
- 不呼叫 Replicate API
- 不會消耗 API 點數
- 適合測試程式邏輯

### 真實模式
- 會實際呼叫 Replicate API
- 會消耗 API 點數
- 適合測試完整的圖片彩色化功能

## 📝 測試內容

### 文字訊息測試
- `!功能` - 測試功能選單
- `你好` - 測試一般文字處理
- `📸 圖片彩色化` - 測試快速回覆
- `💬 文字回覆` - 測試快速回覆
- `❓ 使用說明` - 測試快速回覆
- `🔧 其他功能` - 測試快速回覆

### 圖片訊息測試
- 模擬圖片上傳事件
- 測試圖片處理流程
- 測試彩色化功能（真實模式）

## 🔧 自訂測試

### 新增測試圖片
1. 將圖片檔案放入 `test_images/` 資料夾
2. 支援格式：`.jpg`, `.png`, `.jpeg`
3. 建議檔名：`test1.jpg`, `test2.png`, `test3.jpeg`

### 修改測試事件
編輯 `mock_events.py` 中的 `TEST_EVENTS` 字典來新增或修改測試事件：

```python
TEST_EVENTS = {
    "自訂測試": MockTextEvent("您的測試文字"),
    # ... 其他測試
}
```

### 自訂測試函數
在 `test_local.py` 中新增自訂測試方法：

```python
def test_custom_function(self):
    """自訂測試函數"""
    event = MockTextEvent("自訂文字")
    # 您的測試邏輯
```

## 📊 測試結果解讀

### 成功指標
- ✅ 測試成功
- 📤 訊息回覆正常
- ⏱️ 處理時間合理

### 常見問題
- ❌ 測試失敗：檢查錯誤訊息
- ⚠️ 找不到圖片：確認圖片路徑
- 🔧 模擬模式：API 呼叫被模擬

## 🛠️ 除錯技巧

### 1. 檢查環境變數
確保測試檔案中有設定必要的環境變數：
```python
os.environ["CHANNEL_ACCESS_TOKEN"] = "test_token"
os.environ["CHANNEL_SECRET"] = "test_secret"
os.environ["REPLICATE_API_TOKEN"] = "test_replicate_token"
```

### 2. 檢查匯入
確保能正確匯入 `app.py` 中的函數：
```python
from app import handle_text, handle_image, colorize_image
```

### 3. 檢查模擬物件
確認模擬物件正確替換了真實的 Line Bot API：
```python
with patch('app.line_bot_api', mock_api):
    # 測試程式碼
```

## 📈 效能測試

測試工具會記錄每個測試的處理時間，幫助您：
- 識別效能瓶頸
- 優化程式碼
- 監控 API 回應時間

## 🔄 持續測試

建議在開發過程中：
1. 每次修改程式碼後執行簡化版測試
2. 完成功能開發後執行完整版測試
3. 部署前進行真實模式測試

## 📞 支援

如果遇到問題：
1. 檢查錯誤訊息
2. 確認檔案路徑正確
3. 驗證環境變數設定
4. 檢查 Python 套件版本

---

**注意**：測試工具僅供開發和除錯使用，請勿在生產環境中使用。
