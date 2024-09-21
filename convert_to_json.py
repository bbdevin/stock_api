import json
from bs4 import BeautifulSoup
import pandas as pd
import os

def parse_broker_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    select_elements = soup.find_all('select', {'name': 'sel_BrokerBranch'})
    
    broker_data = []
    for select in select_elements:
        options = select.find_all('option')
        if options:
            bhid = options[0]['value']  # 使用第一個選項的值作為 BHID
            broker_name = options[0].text.split('-')[0]  # 獲取券商名稱
            
            for option in options:
                value = option['value']
                name = option.text
                broker_data.append({
                    "BHID": bhid,
                    "券商名稱": broker_name,
                    "分行名稱": name,
                    "富邦編碼": value,
                    "地址": None,
                    "電話": None
                })
    
    return broker_data

def read_excel_file(file_path):
    return pd.read_excel(file_path)

def add_address_and_phone(broker_data, excel_data):
    for broker in broker_data:
        # 從分行名稱中提取券商名稱
        broker_name = broker['分行名稱']
        
        # 在 Excel 數據中查找匹配的證券商
        match = excel_data[excel_data['證券商名稱'] == broker_name]
        
        if not match.empty:
            broker['地址'] = match['地址'].values[0] if '地址' in match.columns and pd.notna(match['地址'].values[0]) else None
            broker['電話'] = match['電話'].values[0] if '電話' in match.columns and pd.notna(match['電話'].values[0]) else None
        else:
            print(f"未找到證券商名稱為 '{broker_name}' 的資料")
    
    return broker_data

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    txt_file_path = os.path.join(script_dir, 'file.txt')
    excel_file_path = os.path.join(script_dir, 'brokers.xlsx')
    json_file_path = os.path.join(script_dir, 'brokers.json')

    # 讀取 file.txt
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 解析數據
    broker_data = parse_broker_data(content)

    # 讀取 Excel 文件
    excel_data = read_excel_file(excel_file_path)

    # 添加地址和電話信息
    broker_data = add_address_and_phone(broker_data, excel_data)

    # 將數據寫入 JSON 文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(broker_data, json_file, ensure_ascii=False, indent=2)

    print("轉換完成，數據已保存到 brokers.json")

if __name__ == "__main__":
    main()