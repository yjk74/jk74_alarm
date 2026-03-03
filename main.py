import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

TOKEN = "8643915197:AAHAxeM7oSIoQzxEk4KOMQ52QicRMXABE7s"
CHAT_ID = "8698887012"

SITES = [
    {
        "name": "연수구청 채용공고", 
        "url": "https://www.yeonsu.go.kr/main/community/notify/job.asp", 
        "base_url": "https://www.yeonsu.go.kr", 
        "selector": ".table_style_1 tbody tr",
        "check_type": "title"
    },
    {
        "name": "대한주택관리사협회 인천", 
        "url": "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N", 
        "base_url": "https://www.khma.org", 
        "selector": ".board_list tbody tr",
        "check_type": "region"
    }
]

async def send_msg(text):
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

async def run():
    # 파일 이름을 하나로 통일합니다.
    last_data = {}
    file_path = "last_check_values.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    s_name, s_val = line.strip().split(":", 1)
                    last_data[s_name] = s_val

    headers = {'User-Agent': 'Mozilla/5.0'}

    for site in SITES:
        try:
            res = requests.get(site['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select(site['selector'])
            
            target_row = None
            for row in rows:
                if "공지" in row.get_text() or "NOTICE" in row.get_text().upper(): continue
                target_row = row
                break

            if target_row:
                cells = target_row.find_all('td')
                link_tag = target_row.find('a')
                check_value = link_tag.get_text(strip=True) if site['check_type'] == "title" else cells[1].get_text(strip=True)

                if last_data.get(site['name']) != check_value:
                    link = link_tag.get('href', '')
                    if link.startswith('/'): link = site['base_url'] + link
                    msg = f"<b>[새 공고 - {site['name']}]</b>\n내용: {check_value}\n<a href='{link}'>👉 보기</a>"
                    await send_msg(msg)
                    last_data[site['name']] = check_value
        except Exception as e:
            print(f"Error {site['name']}: {e}")

    with open(file_path, "w", encoding="utf-8") as f:
        for s_name, s_val in last_data.items():
            f.write(f"{s_name}:{s_val}\n")

if __name__ == "__main__":
    # 이 줄을 추가하면 '변동 사항'과 상관없이 무조건 메시지가 옵니다.
    asyncio.run(send_msg("🚀 봇이 정상 작동 중입니다! (강제 테스트)")) 
    asyncio.run(run())
