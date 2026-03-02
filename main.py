import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

# 설정 값
TOKEN = "8643915197:AAHAxeM7oSiOqzEk4KOMQ52qicRMXABE7S"
CHAT_ID = "8698887012"

SITES = [
    {"name": "인천인재평생교육진흥원", "url": "https://itle.or.kr/user/board/list.do?bbs_id=bbs_136", "base_url": "https://itle.or.kr", "selector": "tbody tr"},
    {"name": "연수구청 채용공고", "url": "https://www.yeonsu.go.kr/main/community/notify/job.asp", "base_url": "https://www.yeonsu.go.kr", "selector": ".table_style_1 tbody tr"},
    {"name": "대한주택관리협회 인천", "url": "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N", "base_url": "https://www.khma.org", "selector": ".board_list tbody tr"}
]

async def send_msg(text):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

async def run():
    # 저장된 마지막 글 읽기 (중복 방지용)
    last_titles = ""
    if os.path.exists("last_titles.txt"):
        with open("last_titles.txt", "r", encoding="utf-8") as f:
            last_titles = f.read()

    new_titles = []
    for site in SITES:
        try:
            res = requests.get(site['url'], headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            row = soup.select_one(site['selector']) # 최상단 글 하나만 확인
            
            if row:
                link_tag = row.find('a')
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href')
                if link.startswith('/'): link = site['base_url'] + link
                
                # 새로운 글이라면 알림 전송
                if title not in last_titles:
                    msg = f"<b>[새 공고 - {site['name']}]</b>\n{title}\n<a href='{link}'>👉 상세보기</a>"
                    await send_msg(msg)
                
                new_titles.append(title)
        except Exception as e:
            print(f"Error {site['name']}: {e}")

    # 현재 확인한 글들을 저장
    with open("last_titles.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(new_titles))

if __name__ == "__main__":
    asyncio.run(run())
