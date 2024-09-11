from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return "歡迎使用股票資料API"

@app.route('/api/stock_data/<stock_code>')
def get_stock_data(stock_code):
    url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zca/zca_{stock_code}.djhtm"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 這裡需要根據網頁結構進行具體的解析邏輯
    # 以下是示例數據,實際使用時需要替換為真實解析結果
    data = {
        '股票代號': stock_code,
        '日期': '2023-04-20',
        '開盤價': 100.5,
        '收盤價': 102.0,
        '最高價': 103.5,
        '最低價': 99.5,
        '成交量': 1000000
    }
    
    return jsonify(data)

@app.route('/api/chip_data/<stock_code>')
def get_chip_data(stock_code):
    url = f"https://fubon-ebrokerdj.fbs.com.tw/z/zc/zcl/zcl.djhtm?a={stock_code}&b=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 這裡需要根據網頁結構進行具體的解析邏輯
    # 以下是示例數據,實際使用時需要替換為真實解析結果
    data = [
        {
            '股票代號': stock_code,
            '日期': '2023-04-20',
            '券商': '富邦證券',
            '買張': 1000,
            '賣張': 800,
            '買賣超資訊': 200,
            '券商分點位置': '台北'
        }
    ]
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
