from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 讀取 Excel 文件
try:
    broker_df = pd.read_excel('brokers.xlsx')
except Exception as e:
    print(f"無法讀取 Excel 文件: {e}")
    broker_df = pd.DataFrame()

@app.route('/')
def home():
    return jsonify({"message": "歡迎使用股票資料API"})

@app.route('/api/chip_data/<stock_code>')
def get_chip_data(stock_code):
    try:
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        if start_date and end_date:
            url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco.djhtm?a={stock_code}&e={start_date}&f={end_date}"
        else:
            url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco_{stock_code}.djhtm"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'class': 't01'})
        
        if not table:
            return jsonify({'error': '無法找到數據表格'}), 404
        
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
            '日期': date,
            '開始日期': start_date,
            '結束日期': end_date,
            '買超分點': buy_super,
            '賣超分點': sell_super
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_data/<stock_code>')
def get_stock_data(stock_code):
    try:
        url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zca/zca_{stock_code}.djhtm"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {
            '股票代號': stock_code,
            '日期': soup.find('span', {'id': 'ctl00_MainContent_uctlZca_LbDATETIME'}).text.strip(),
            '開盤價': soup.find('span', {'id': 'ctl00_MainContent_uctlZca_LbOPEN'}).text.strip(),
            '收盤價': soup.find('span', {'id': 'ctl00_MainContent_uctlZca_LbCLOSE'}).text.strip(),
            '最高價': soup.find('span', {'id': 'ctl00_MainContent_uctlZca_LbHIGH'}).text.strip(),
            '最低價': soup.find('span', {'id': 'ctl00_MainContent_uctlZca_LbLOW'}).text.strip(),
            '成交量': soup.find('span', {'id': 'ctl00_MainContent_uctlZca_LbVOLUME'}).text.strip()
        }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/broker_history/<stock_code>/<broker_id>')
def get_broker_history(stock_code, broker_id):
    try:
        # 從 Excel 文件中獲取券商資訊
        broker_info = broker_df[broker_df['證券商代號'] == broker_id].iloc[0]
        broker_name = broker_info['證券商名稱']
        broker_address = broker_info['地址']

        # 設置日期範圍（例如：過去一年）
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        start_date = request.args.get('start_date', (datetime.now() - pd.DateOffset(years=1)).strftime('%Y-%m-%d'))

        url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco0/zco0.djhtm?A={stock_code}&BHID={broker_id}&b={broker_id}&C=0&D={start_date}&E={end_date}&ver=V3"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.encoding = 'big5'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', {'id': 'oMainTable'})
        
        if not table:
            return jsonify({'error': '無法找到數據表格'}), 404
        
        rows = table.find_all('tr')[1:]  # 跳過表頭
        
        history_data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                data = {
                    '日期': cols[0].text.strip(),
                    '買進': cols[1].text.strip(),
                    '賣出': cols[2].text.strip(),
                    '買賣總額': cols[3].text.strip(),
                    '買賣超': cols[4].text.strip()
                }
                history_data.append(data)
        
        result = {
            '股票代號': stock_code,
            '券商代號': broker_id,
            '券商名稱': broker_name,
            '券商地址': broker_address,
            '歷史資料': history_data
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
