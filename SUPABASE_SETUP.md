# Supabase 資料庫設定指南

本指南將引導您如何申請 Supabase 並取得資料庫連線資訊。

## 為什麼選擇 Supabase？

- ✅ 免費額度：500MB 儲存、無限 API 請求
- ✅ 基於 PostgreSQL：穩定可靠
- ✅ 管理介面：直接在網頁上查看/編輯資料
- ✅ 免維護：不用自己管理資料庫伺服器

## 申請步驟（約 5-10 分鐘）

### 1. 註冊帳號

前往 [Supabase 官網](https://supabase.com/)

點擊 **"Start your project"** 或 **"Sign Up"**

可以使用以下方式註冊：
- GitHub 帳號（推薦，最快）
- Google 帳號
- Email + 密碼

### 2. 建立新專案

登入後，點擊 **"New Project"**

填寫以下資訊：
- **Name**：專案名稱（例如：`linebot-member-system`）
- **Database Password**：資料庫密碼（請妥善保管，之後需要用到）
  - 建議使用自動產生的強密碼
  - 📝 **重要：請複製並保存此密碼**
- **Region**：選擇最近的區域
  - 推薦選擇：`Northeast Asia (Tokyo)` 或 `Southeast Asia (Singapore)`
- **Pricing Plan**：選擇 **Free**（免費方案）

點擊 **"Create new project"**

⏳ 等待 2-3 分鐘，資料庫啟動中...

### 3. 取得 DATABASE_URL

專案建立完成後，進入以下步驟：

1. 點擊左側選單的 **"Settings"**（齒輪圖示）
2. 點擊 **"Database"**
3. 找到 **"Connection string"** 區塊
4. 選擇 **"URI"** 分頁
5. 複製 Connection string，格式如下：

```
postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
```

6. 將 `[YOUR-PASSWORD]` 替換為您在步驟 2 設定的密碼

**完整範例：**
```
postgresql://postgres:MySecurePassword123@db.abcdefghijk.supabase.co:5432/postgres
```

### 4. 設定環境變數

在專案根目錄建立 `.env` 檔案（如果還沒有的話）：

```bash
cp env_example.txt .env
```

編輯 `.env` 檔案，加入 `DATABASE_URL`：

```env
# LINE Bot 設定
CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
CHANNEL_SECRET=your_line_channel_secret_here

# Replicate API 設定
REPLICATE_API_TOKEN=your_replicate_api_token_here

# Database 資料庫設定
DATABASE_URL=postgresql://postgres:MySecurePassword123@db.abcdefghijk.supabase.co:5432/postgres

# Feature Point Costs
COLORIZE_COST=10
EDIT_COST=5
```

### 5. 初始化資料庫

執行以下指令建立資料表：

```bash
python scripts/init_db.py
```

如果看到以下訊息，代表成功：

```
🎉 資料庫初始化完成！
```

## 測試資料庫連線

啟動 LINE Bot：

```bash
python app.py
```

如果看到以下訊息，代表資料庫連線成功：

```
✅ 資料庫連線初始化完成
✅ 會員服務初始化完成
✅ 會員功能已啟用
```

## 使用 Supabase 管理介面

### 查看資料

1. 進入 Supabase 專案
2. 點擊左側選單的 **"Table Editor"**
3. 可以看到 `members` 和 `point_transactions` 兩個表
4. 點擊表格名稱即可查看資料

### 手動新增測試資料

在 **Table Editor** 中：

1. 選擇 `members` 表
2. 點擊 **"Insert row"**
3. 填寫資料：
   - `user_id`: U1234567890abcdef
   - `display_name`: 測試用戶
   - `points`: 100
   - `status`: normal
4. 點擊 **"Save"**

### SQL 編輯器

點擊左側選單的 **"SQL Editor"** 可以執行 SQL 查詢：

```sql
-- 查詢所有會員
SELECT * FROM members;

-- 查詢交易記錄
SELECT * FROM point_transactions ORDER BY created_at DESC LIMIT 10;

-- 查詢特定用戶的點數
SELECT user_id, display_name, points FROM members WHERE user_id = 'U1234567890abcdef';
```

## 常見問題

### Q1: 忘記資料庫密碼怎麼辦？

A: 需要重設密碼
1. 進入專案設定 → Database
2. 找到 **"Database password"** 區塊
3. 點擊 **"Reset database password"**
4. 複製新密碼並更新 `.env` 檔案中的 `DATABASE_URL`

### Q2: 連線失敗怎麼辦？

A: 檢查以下項目：
- ✅ DATABASE_URL 格式是否正確
- ✅ 密碼是否有特殊字元需要 URL 編碼
- ✅ 網路連線是否正常
- ✅ Supabase 專案是否處於暫停狀態（免費版 7 天不使用會暫停）

### Q3: 如何查看資料庫用量？

A: 
1. 進入專案設定 → Usage
2. 可以看到：
   - Database size（資料庫大小）
   - API requests（API 請求次數）
   - Bandwidth（流量使用）

### Q4: 免費額度夠用嗎？

A: 免費方案包含：
- 500MB 資料庫空間
- 無限 API 請求
- 1GB 檔案儲存
- 2GB 流量/月

對於小型 LINE Bot（< 1000 使用者）完全足夠。

## 備份建議

雖然 Supabase 會自動備份，但建議定期匯出重要資料：

1. 進入 **SQL Editor**
2. 執行匯出查詢：

```sql
-- 匯出所有會員資料
SELECT * FROM members;

-- 匯出所有交易記錄
SELECT * FROM point_transactions;
```

3. 點擊 **"Download CSV"** 下載備份

## 其他資料庫選項

如果不想用 Supabase，也可以選擇：
- **Railway**：類似 Heroku，免費額度
- **Heroku Postgres**：需要 Heroku 帳號
- **ElephantSQL**：專門的 PostgreSQL 服務
- **AWS RDS**：需付費，適合大型專案

所有選項只需要修改 `DATABASE_URL` 環境變數即可，程式碼不需要改動。

## 需要幫助？

如果遇到問題，可以：
1. 查看 Supabase 官方文檔：https://supabase.com/docs
2. 檢查專案的 logs（Settings → Logs）
3. 查看 Python 程式的錯誤訊息

---

設定完成後，您的 LINE Bot 會員系統就可以正常運作了！🎉

