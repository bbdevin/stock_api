# 股票資料 API

這是一個提供股票相關資訊的 Flask API 服務。

## 功能

1. 獲取股票籌碼資料
2. 獲取股票歷史資料
3. 獲取券商交易資料

## 資料來源

- 股票籌碼資料：富邦證券 (https://fubon-ebrokerdj.fbs.com.tw/)
- 股票歷史資料：Yahoo Finance API
- 券商交易資料：富邦證券 (https://fubon-ebrokerdj.fbs.com.tw/)

注意：由於資料來源限制，部分資料可能不完整或有延遲。本 API 僅提供單一來源的資料，可能無法涵蓋所有股票或完整的歷史資料。

## API 端點

### 1. 獲取股票籌碼資料

- 端點：`/chip_data/<stock_input>`
- 方法：GET
- 參數：
  - `stock_input`：股票代碼或名稱（路徑參數）
  - `start_date`：開始日期（可選，查詢參數）
  - `end_date`：結束日期（可選，查詢參數）
- 返回：JSON 格式的股票籌碼資料

### 2. 獲取股票歷史資料

- 端點：`/stock_history/<stock_code>`
- 方法：GET
- 參數：
  - `stock_code`：股票代碼（路徑參數）
- 返回：JSON 格式的股票歷史價格和成交量資料

### 3. 獲取券商交易資料

- 端點：`/broker_data`
- 方法：GET
- 參數：
  - `stock_id`：股票代碼（查詢參數）
  - `broker`：券商代號或名稱（查詢參數）
  - `start_date`：開始日期（可選，查詢參數）
  - `end_date`：結束日期（可選，查詢參數）
- 返回：JSON 格式的券商交易資料

## 使用的套件

- Flask: Web 應用框架
- Flask-CORS: 處理跨域請求
- requests: 發送 HTTP 請求
- BeautifulSoup4: 解析 HTML
- pandas: 資料處理和分析
- yfinance: 獲取 Yahoo Finance 資料
- waitress: 生產環境 WSGI 服務器

完整的依賴列表請參考 `requirements.txt` 文件。

## 安裝和運行

1. 安裝依賴：
   `pip install -r requirements.txt`

2. 運行應用：
   `python app.py`

## Docker 部署

1. 構建 Docker 映像：
   `docker build -t stock-api .`

2. 運行 Docker 容器：
   `docker run -p 5000:5000 -v /path/to/上市公司.csv:/app/上市公司.csv -v /path/to/上櫃公司.csv:/app/上櫃公司.csv -v /path/to/brokers.json:/app/brokers.json stock-api`

## 注意事項

- 確保 `上市公司.csv`、`上櫃公司.csv` 和 `brokers.json` 文件存在於正確的路徑。
- API 使用 CORS，允許來自 `http://localhost:3000` 和 `https://stock.techtrever.site` 的跨域請求。
- 在生產環境中，建議使用 Waitress 作為 WSGI 服務器。
- 本 API 僅供教育和研究目的使用，不應用於實際投資決策。
- 請遵守資料來源的使用條款和版權規定。

## 錯誤處理

API 會返回適當的 HTTP 狀態碼和錯誤訊息。常見的錯誤包括：

- 404：找不到請求的資源
- 400：請求參數錯誤
- 500：服務器內部錯誤

請查看具體的錯誤訊息以獲取更多資訊。

## 貢獻

如果您發現任何問題或有改進建議，請提交 issue 或 pull request。

## 許可證

[MIT License](LICENSE)
