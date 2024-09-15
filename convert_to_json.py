import json
from bs4 import BeautifulSoup

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
                    "富邦編碼": value
                })
    
    return broker_data

def main():
    # 讀取 file.txt
    with open('file.txt', 'r', encoding='utf-8') as file:
        content = file.read()

    # 解析數據
    broker_data = parse_broker_data(content)

    # 將數據寫入 JSON 文件
    with open('brokers.json', 'w', encoding='utf-8') as json_file:
        json.dump(broker_data, json_file, ensure_ascii=False, indent=2)

    print("轉換完成，數據已保存到 brokers.json")

if __name__ == "__main__":
    main()