# Web Assistant Frontend (Streamlit Test UI)

這是 Web Assistant API 的簡單測試前端，使用 Streamlit 構建。

## 功能特性

- 🔐 **用戶認證**：註冊和登入功能
- 💬 **會話管理**：創建、選擇和管理聊天會話
- 🤖 **AI 對話**：與 GPT-4o-mini 進行對話
- 📝 **消息歷史**：查看和管理聊天記錄
- 🎨 **直觀界面**：簡潔易用的 Web 界面

## 安裝和運行

### 1. 安裝依賴

```bash
# 在 frontend 目錄下
pip install -r requirements.txt
```

### 2. 確保後端運行

確保您的 FastAPI 後端正在運行：

```bash
# 在 backend 目錄下
make dev
```

後端應該在 `http://127.0.0.1:8000` 運行。

### 3. 啟動 Streamlit 前端

```bash
# 在 frontend 目錄下
streamlit run app.py
```

前端將在 `http://localhost:8501` 啟動。

## 使用說明

### 首次使用

1. **註冊帳號**：
   - 點擊 "Register" 標籤
   - 輸入郵箱和密碼
   - 點擊 "Register" 按鈕

2. **登入**：
   - 如果已有帳號，使用 "Login" 標籤
   - 輸入郵箱和密碼
   - 點擊 "Login" 按鈕

### 開始聊天

1. **創建會話**：
   - 登入後，前往 "Sessions" 標籤
   - 點擊 "Create New Session" 創建新對話

2. **選擇會話**：
   - 在會話列表中點擊任意會話
   - 切換到 "Chat" 標籤開始對話

3. **發送消息**：
   - 在文本框中輸入您的消息
   - 點擊 "Send" 按鈕
   - AI 會自動回覆

### 會話管理

- **刷新會話列表**：點擊 "Refresh Sessions"
- **載入聊天記錄**：選擇會話時自動載入
- **清除聊天記錄**：點擊 "Clear Chat" 按鈕
- **查看會話信息**：在側邊欄查看當前會話詳情

## 界面說明

### 側邊欄
- 顯示登入狀態
- 當前會話信息
- 消息統計
- API 文檔連結

### 主要區域
- **認證頁面**：註冊和登入表單
- **聊天界面**：消息顯示和輸入區域
- **會話管理**：會話列表和控制按鈕

## API 端點

此前端使用以下 API 端點：

- `POST /api/v1/auth/register` - 用戶註冊
- `POST /api/v1/auth/login` - 用戶登入
- `POST /api/v1/auth/session` - 創建會話
- `GET /api/v1/auth/sessions` - 獲取用戶會話
- `POST /api/v1/chatbot/chat` - 發送聊天消息
- `GET /api/v1/chatbot/messages` - 獲取會話消息
- `DELETE /api/v1/chatbot/messages` - 清除會話消息

## 注意事項

1. **後端依賴**：此前端完全依賴後端 API，請確保後端正常運行
2. **本地測試**：此界面僅用於測試，生產環境請使用正式前端
3. **API 文檔**：詳細 API 說明請查看 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 故障排除

### 連接問題
- 確認後端在 `http://127.0.0.1:8000` 運行
- 檢查防火牆設置
- 查看後端日誌

### 認證問題
- 檢查郵箱和密碼格式
- 確認用戶是否已註冊
- 查看瀏覽器控制台錯誤

### 聊天問題
- 確認已選擇會話
- 檢查 OpenAI API 密鑰配置
- 查看後端錯誤日誌 