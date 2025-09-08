# Line Bot 群組支援功能

## 修改概述

本次修改讓 Line Bot 能夠在群組中正常回應，同時保持個人聊天的現有功能。

## 主要修改

### 1. MessagePublisher 類別增強

- 新增 `_get_source_type()` 方法：檢測訊息來源類型（user/group/room）
- 新增 `_is_group_chat()` 方法：判斷是否為群組聊天
- 修改 `process_reply_message()` 方法：支援群組聊天檢測
- 修改 `process_push_message()` 方法：支援群組聊天檢測

### 2. 群組聊天處理邏輯

- **群組聊天**：跳過用戶驗證，直接回應到群組
- **個人聊天**：維持現有的用戶驗證機制

### 3. 測試功能增強

- 更新 `test_local.py` 測試腳本
- 新增群組功能測試
- 支援模擬群組和房間訊息

## 使用方式

### 在群組中使用

1. 將 Bot 加入群組
2. 在群組中輸入指令（如 `!功能`、`圖片彩色化` 等）
3. Bot 會直接在群組中回應，無需加好友

### 測試群組功能

```bash
cd test
python test_local.py
# 選擇選項 3: 執行群組功能測試
```

## 技術細節

### 群組檢測邏輯

```python
def _is_group_chat(self, event):
    source_type = self._get_source_type(event)
    return source_type in ['group', 'room']
```

### 回應策略

- 群組聊天：`self.line_bot_api.reply_message(reply_token, messages)`
- 個人聊天：先驗證用戶，再回應

## 圖片處理行為

### 群組中的圖片處理

**群組聊天**：
1. 收到圖片 → **不立即回覆**任何訊息
2. 背景處理圖片
3. 處理完成 → 使用 `reply_message` 回覆結果到群組

**個人聊天**：
1. 收到圖片 → **不立即回覆**任何訊息
2. 背景處理圖片  
3. 處理完成 → 使用 `push_message` 發送結果到個人

### 技術實現

- 群組聊天：使用 `reply_message(reply_token)` 回覆到群組
- 個人聊天：使用 `push_message(user_id)` 發送到個人
- **重要**：`reply_token` 只能使用一次，所以不先回覆「正在處理...」

### Reply Token 限制

- **只能使用一次**：每個 `reply_token` 只能呼叫一次 `reply_message()`
- **有時效性**：通常幾分鐘內有效
- **一次性使用後失效**：即使處理失敗，該 token 也不能重複使用

## 注意事項

1. 群組中的用戶不需要加 Bot 為好友
2. 群組功能會跳過用戶驗證，直接回應
3. 個人聊天功能保持不變
4. 所有現有功能都支援群組使用
5. **群組中的圖片處理結果會回覆到群組**

## 測試結果

- ✅ 群組中的功能選單正常顯示
- ✅ 群組中的圖片彩色化功能正常運作
- ✅ 房間中的使用說明正常顯示
- ✅ 個人聊天功能不受影響
- ✅ 群組中的圖片處理結果會回覆到群組
