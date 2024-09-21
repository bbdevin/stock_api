from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import logging
import traceback
import yfinance as yf
import json
import os

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

# 讀取 brokers.json 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file_path = os.path.join(script_dir, 'brokers.json')

with open(json_file_path, 'r', encoding='utf-8') as file:
    brokers_data = json.load(file)

def parse_broker_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', {'class': 'hasBorder'})
    if not table:
        return []

    rows = table.find_all('tr')[1:]  # 跳過表頭
    data = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            data.append({
                '日期': cols[0].text.strip(),
                '買進股數': cols[1].text.strip(),
                '賣出股數': cols[2].text.strip(),
                '買賣超股數': cols[3].text.strip(),
                '買賣超金額(元)': cols[4].text.strip()
            })
    return data

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
        start_date = end_date - timedelta(days=365 * 10)  # 獲取10年的資料

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

@app.route('/api/broker_data', methods=['GET'])
def get_broker_data():
    stock_id = request.args.get('stock_id')
    broker_input = request.args.get('broker')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not stock_id or not broker_input:
        return jsonify({"error": "股票代碼和券商代號或名稱是必需的"}), 400

    broker = next((b for b in brokers_data if broker_input in (b['分行名稱'], b['富邦編碼'])), None)

    if not broker:
        return jsonify({"error": "找不到指定的券商"}), 404

    bhid = broker['BHID']
    fubon_code = broker['富邦編碼']
    
    # 如果沒有提供日期，默認使用最近三個月
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zco/zco0/zco0.djhtm?a={stock_id}&BHID={bhid}&b={fubon_code}&D={start_date}&E={end_date}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://fubon-ebrokerdj.fbs.com.tw/',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'big5'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 獲取券商和股票信息
        title_info = soup.find('td', class_='t10')
        title_text = title_info.text.strip() if title_info else ""
        
        # 解析標題信息
        broker_name, stock_info = title_text.split(' 對 ', 1) if ' 對 ' in title_text else (title_text, "")
        stock_name, stock_id = stock_info.split('(', 1) if '(' in stock_info else (stock_info, "")
        stock_id = stock_id.rstrip(')') if stock_id.endswith(')') else stock_id

        # 獲取日期範圍選擇器的選項
        date_range_options = [option.text for option in soup.select('select[name="D"] option')]

        # 獲取券商選擇器的選項
        broker_options = [{'value': option['value'], 'text': option.text} for option in soup.select('select[name="sel_Broker"] option')]

        # 獲取券商分支機構選擇器的選項
        branch_options = [{'value': option['value'], 'text': option.text} for option in soup.select('select[name="sel_BrokerBranch"] option')]

        # 找到包含數據的表格
        table = soup.find('table', {'id': 'oMainTable'})
        
        if not table:
            return jsonify({"error": "無法找到數據表格"}), 404
        
        # 解析表格數據
        rows = table.find_all('tr')[1:]  # 跳過表頭
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 5:
                data.append({
                    "日期": cols[0].text.strip(),
                    "買進(張)": int(cols[1].text.strip().replace(',', '')),
                    "賣出(張)": int(cols[2].text.strip().replace(',', '')),
                    "買賣總額(張)": int(cols[3].text.strip().replace(',', '')),
                    "買賣超(張)": int(cols[4].text.strip().replace(',', ''))
                })
        
        # 獲取期間累計買賣超張數
        total_net_buy = soup.find('td', class_='t3t1')
        total_net_buy_text = total_net_buy.text.strip() if total_net_buy else ""
        total_net_buy_value = total_net_buy_text.split('：')[-1] if '：' in total_net_buy_text else ""

        broker_info = {
            'broker_name': broker_name,
            'stock_name': stock_name,
            'stock_id': stock_id,
            'address': broker['地址'],
            'phone': broker['電話'],
            'date_range_options': date_range_options,
            'broker_options': broker_options,
            'branch_options': branch_options,
            'data': data,
            'total_net_buy': total_net_buy_value,
            'start_date': start_date,
            'end_date': end_date
        }
        return jsonify(broker_info)
    
    except requests.RequestException as e:
        app.logger.error(f"請求失敗: {str(e)}")
        return jsonify({"error": f"請求失敗: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# 在文件底部添加以下代碼以安裝所需的庫
# pip install yfinance
