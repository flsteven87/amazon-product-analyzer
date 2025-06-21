# 🚀 Zeabur 分離部署指南

本指南將幫你將Amazon Product Analyzer部署到Zeabur，採用前後端分離的最佳實踐架構。

## 📋 部署架構概覽

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   PostgreSQL    │
│   (Next.js)     │───▶│   (FastAPI)     │───▶│   (Supabase)    │
│   Zeabur App 1  │    │   Zeabur App 2  │    │   External      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 準備工作

### 1. Supabase 數據庫設置

1. 前往 [Supabase](https://supabase.com) 註冊帳號
2. 創建新專案
3. 獲取PostgreSQL連接字串：
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

### 2. OpenAI API Key

1. 前往 [OpenAI Platform](https://platform.openai.com)
2. 創建 API Key
3. 確保帳號有足夠額度

## 🚀 後端部署 (Backend)

### Step 1: 準備後端Repository

1. **推送程式碼到GitHub**
   ```bash
   # 確保你在專案根目錄
   cd /path/to/amazon-product-analyzer
   git add .
   git commit -m "feat: ready for Zeabur deployment"
   git push origin main
   ```

### Step 2: Zeabur Backend部署

1. **登入 [Zeabur](https://zeabur.com)**

2. **創建新專案**
   - 點擊 "Create Project"
   - 選擇 "Deploy from GitHub"
   - 選擇你的 repository

3. **配置Backend服務**
   - 服務名稱: `amazon-analyzer-backend`
   - Root Directory: `backend`
   - Build Command: 自動檢測 (Dockerfile)
   - Port: `8000`

4. **設置環境變數**
   ```env
   APP_ENV=production
   PROJECT_NAME=Amazon Product Analyzer
   LLM_API_KEY=your_openai_api_key_here
   POSTGRES_URL=your_supabase_postgresql_url_here
   ALLOWED_ORIGINS=https://your-frontend-domain.zeabur.app
   JWT_SECRET_KEY=your_random_secret_key_here
   LOG_LEVEL=INFO
   ```

5. **點擊Deploy**

### Step 3: 獲取Backend URL

部署成功後，獲取你的backend URL：
```
https://your-backend-domain.zeabur.app
```

## 🌐 前端部署 (Frontend)

### Step 1: 配置Frontend環境

1. **在你的repository中創建 `.env.production`**
   ```bash
   # 複製範例檔案
   cp frontend/.env.production.example frontend/.env.production
   ```

2. **編輯環境變數**
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-domain.zeabur.app
   ```

### Step 2: Zeabur Frontend部署

1. **在同一個Zeabur專案中添加新服務**
   - 點擊 "Add Service"
   - 選擇 "GitHub"
   - 選擇同一個 repository

2. **配置Frontend服務**
   - 服務名稱: `amazon-analyzer-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Start Command: `npm start`
   - Port: `3000`

3. **設置環境變數**
   ```env
   NEXT_PUBLIC_API_URL=https://your-backend-domain.zeabur.app
   ```

4. **點擊Deploy**

## 🔗 配置服務間通信

### Step 1: 更新Backend CORS

1. **登入Backend服務的環境變數配置**
2. **更新 ALLOWED_ORIGINS**
   ```env
   ALLOWED_ORIGINS=https://your-frontend-domain.zeabur.app,https://*.zeabur.app
   ```
3. **重新部署Backend服務**

### Step 2: 測試連接

1. **訪問前端URL**
   ```
   https://your-frontend-domain.zeabur.app
   ```

2. **測試API連接**
   - 打開瀏覽器開發者工具
   - 查看Network tab
   - 確認API請求成功

## 🧪 部署驗證

### 功能測試清單

- [ ] ✅ Frontend訪問正常
- [ ] ✅ Backend API健康檢查：`/health`
- [ ] ✅ WebSocket連接成功
- [ ] ✅ 完整分析流程測試
- [ ] ✅ 數據庫連接正常

### 測試步驟

1. **基礎連接測試**
   ```bash
   # 測試Backend健康狀況
   curl https://your-backend-domain.zeabur.app/health
   
   # 預期返回
   {"status":"healthy","environment":"production",...}
   ```

2. **完整流程測試**
   - 在Frontend輸入Amazon產品URL
   - 觀察實時進度更新
   - 確認分析報告生成

## 🔍 故障排除

### 常見問題

1. **CORS Error**
   ```
   解決方案：確認Backend的ALLOWED_ORIGINS包含Frontend域名
   ```

2. **WebSocket連接失敗**
   ```
   解決方案：WebSocket會自動使用相同的NEXT_PUBLIC_API_URL
   - HTTP環境：自動使用 ws://
   - HTTPS環境：自動使用 wss://
   - 確保Frontend的NEXT_PUBLIC_API_URL正確配置
   ```

3. **數據庫連接錯誤**
   ```
   解決方案：檢查Supabase連接字串格式
   - 確保使用 postgresql:// 而非 postgresql+psycopg://
   ```

4. **OpenAI API錯誤**
   ```
   解決方案：確認API Key正確且有足夠額度
   ```

### Debug Commands

```bash
# 查看Backend logs
# 在Zeabur控制台的服務頁面查看 "Runtime Logs"

# 查看Frontend logs  
# 在Zeabur控制台的服務頁面查看 "Build Logs" 和 "Runtime Logs"
```

## 📊 監控和維護

### 設置監控

1. **Zeabur內建監控**
   - CPU使用率
   - 記憶體使用率
   - 請求數量

2. **應用層監控**
   - 健康檢查端點：`/health`
   - 分析統計：`/api/v1/stats`

### 成本優化

1. **Resource Scaling**
   - 根據實際使用量調整實例大小
   - 設置合理的auto-scaling政策

2. **Database優化**
   - 定期清理舊的分析數據
   - 使用數據庫連接池

## 🎯 生產環境最佳實踐

### 安全性

1. **API Key保護**
   - 使用環境變數，避免硬編碼
   - 定期輪換API Keys

2. **HTTPS強制**
   - Zeabur自動提供SSL證書
   - 確保所有通信都使用HTTPS

### 效能優化

1. **Frontend優化**
   - 啟用Next.js的靜態優化
   - 使用CDN加速(Zeabur內建)

2. **Backend優化**
   - 設置合理的資料庫連接池
   - 實施API速率限制

## 🎉 部署完成

恭喜！你的Amazon Product Analyzer現在已經成功部署在Zeabur上。

**下一步建議：**
1. 設置自定義域名
2. 配置CI/CD自動部署
3. 實施監控和告警
4. 根據用戶回饋持續優化

## 📞 技術支援

如果遇到問題，可以參考：
- [Zeabur文檔](https://zeabur.com/docs)
- [專案GitHub Issues](your-repo-url/issues)
- [API文檔](./API_DOCUMENTATION.md)