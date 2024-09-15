from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import logging
import traceback
import yfinance as yf

app = Flask(__name__)
CORS(app)

# 設置日誌
logging.basicConfig(level=logging.DEBUG)

# 讀取上市和上櫃公司資料
try:
    listed_companies = pd.read_csv('上市公司.csv', encoding='utf-8')
    otc_companies = pd.read_csv('上櫃公司.csv', encoding='utf-8')
    
    # 添加一個新列來標識公司類型
    listed_companies['上市櫃'] = '上市'
    otc_companies['上市櫃'] = '上櫃'
    
    all_companies = pd.concat([listed_companies, otc_companies])
    all_companies['公司代號'] = all_companies['公司代號'].astype(str).str.zfill(4)
    logging.info(f"成功讀取公司資料，共 {len(all_companies)} 筆")
    logging.info(f"列名: {all_companies.columns.tolist()}")
except Exception as e:
    logging.error(f"讀取公司資料時發生錯誤: {str(e)}")
    logging.error(traceback.format_exc())
    all_companies = pd.DataFrame()

@app.route('/')
def home():
    return jsonify({"message": "歡迎使用股票資料API"})

@app.route('/api/chip_data/<stock_input>')
def get_chip_data(stock_input):
    try:
        logging.info(f"接收到查詢請求：{stock_input}")
        
        # 查找股票代碼和名稱
        if stock_input.isdigit():
            stock_info = all_companies[all_companies['公司代號'] == stock_input.zfill(4)]
        else:
            stock_info = all_companies[all_companies['公司名稱'].str.contains(stock_input)]
        
        if stock_info.empty:
            logging.warning(f"找不到匹配的股票: {stock_input}")
            return jsonify({'error': f'找不到匹配的股票: {stock_input}'}), 404
        
        stock_code = stock_info['公司代號'].iloc[0]
        stock_name = stock_info['公司名稱'].iloc[0]
        stock_short_name = stock_info['公司簡稱'].iloc[0]
        industry = stock_info['產業類別'].iloc[0] if '產業類別' in stock_info.columns else '未知'
        address = stock_info['住址'].iloc[0]
        listing_type = stock_info['上市櫃'].iloc[0]
        stock_agent = stock_info['股票過戶機構'].iloc[0]
        
        logging.info(f"找到匹配的股票: {stock_name} ({stock_code}) - {listing_type}")
        
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        if start_date and end_date:
            url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco.djhtm?a={stock_code}&e={start_date}&f={end_date}"
        else:
            url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco_{stock_code}.djhtm"
        
        logging.info(f"請求 URL：{url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'class': 't01'})
        
        if not table:
            logging.warning("無法找到資料表格")
            return jsonify({'error': '無法找到資料表格'}), 404
        
        rows = table.find_all('tr')[5:-3]
        
        buy_super = []
        sell_super = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 10:
                buy_data = {
                    '券商': cols[0].text.strip(),
                    '買張': cols[1].text.strip(),
                    '賣張': cols[2].text.strip(),
                    '買賣超股數': cols[3].text.strip(),
                    '佔成交量%': cols[4].text.strip().replace('%', '')
                }
                sell_data = {
                    '券商': cols[5].text.strip(),
                    '買張': cols[6].text.strip(),
                    '賣張': cols[7].text.strip(),
                    '買賣超股數': cols[8].text.strip(),
                    '佔成交量%': cols[9].text.strip().replace('%', '')
                }
                buy_super.append(buy_data)
                sell_super.append(sell_data)
        
        date_element = soup.find('div', {'class': 't11'})
        date = date_element.text.split('：')[-1] if date_element else None
        
        result = {
            '股票代號': stock_code,
            '股票名稱': stock_name,
            '股票簡稱': stock_short_name,
            '產業別': industry,
            '公司地址': address,
            '上市櫃': listing_type,
            '股票過戶機構': stock_agent,
            '日期': date,
            '開始日期': start_date,
            '結束日期': end_date,
            '買超分點': buy_super,
            '賣超分點': sell_super
        }
        
        logging.info("成功獲取並解析資料")
        return jsonify(result)
    except Exception as e:
        logging.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_history/<stock_code>')
def get_stock_history(stock_code):
    try:
        logging.info(f"開始獲取股票 {stock_code} 的歷史資料")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 獲取一年的資料

        # 為台灣股票添加 .TW 後綴
        ticker = yf.Ticker(f"{stock_code}.TW")
        history = ticker.history(start=start_date, end=end_date)

        if history.empty:
            logging.warning(f"股票 {stock_code} 沒有返回任何歷史資料")
            return jsonify({'error': '沒有找到該股票的歷史資料'}), 404

        data = []
        for date, row in history.iterrows():
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })

        logging.info(f"成功獲取並處理 {stock_code} 的歷史資料，共 {len(data)} 條記錄")
        return jsonify(data)
    except Exception as e:
        logging.error(f"獲取股票 {stock_code} 歷史資料時發生錯誤: {str(e)}", exc_info=True)
        return jsonify({'error': f"獲取股票歷史資料時發生錯誤: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# 在文件底部添加以下代碼以安裝所需的庫
# pip install yfinance
