import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

# 설정 값
TOKEN = "8643915197:AAHAxeM7oSIoQzxEk4KOMQ52QicRMXABE7s"
CHAT_ID = "8698887012"
FILE_PATH = "last_apartment_name.txt"

SITE_URL = "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N"
BASE_URL = "https://www.khma.org"

async def send_msg(text):
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

async def run():
    # 1. 이전 저장 데이터 로드
    last_apt = ""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            last_apt = f.read().strip()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(SITE_URL, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 게시판 행(tr) 추출
        rows = soup.select("table.board_list tbody tr")
        
        target_apt = ""
        target_title = ""
        target_link = ""

        for row in rows:
            cells = row.find_all('td')
            # 최소 6개 이상의 칸이 있어야 아파트명을 찾을 수 있음
            if len(cells) < 6:
                continue
            
            # 번호 칸에 '공지'가 있으면 패스
            if "공지" in cells[0].get_text():
                continue

            # 이미지 기준 열 순서:
            # 0:번호, 1:등록시도회, 2:채용제목, 3:근무지역, 4:모집부분, 5:아파트명
            target_apt = cells[5].get_text(strip=True)  # 6번째 칸 (index 5)
            target_title = cells[2].get_text(strip=True) # 3번째 칸 (index 2)
            
            # 링크는 보통 제목(cells[2]) 안에 있는 a 태그에 있습니다.
            link_tag = cells[2].find('a')
            if link_tag:
                target_link = link_tag.get('href', '')
                if target_link.startswith('/'):
                    target_link = BASE_URL + target_link
            
            break # 최상단 글 하나만 확인

        if target_apt:
            # 2. 아파트명이 이전과 다르면 알림 전송
            if last_apt != target_apt:
                msg = (
                    f"<b>🏢 [새 공고 알림]</b>\n\n"
                    f"<b>단지명:</b> {target_apt}\n"
                    f"<b>제목:</b> {target_title}\n\n"
                    f"<a href='{target_link}'>👉 자세히 보기</a>"
                )
                
                await send_msg(msg)
                
                # 3. 새로운 아파트명 저장
                with open(FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(target_apt)
                print(f"✅ 새 단지 발견: {target_apt}")
            else:
                print(f"🔄 최신 단지가 동일함: {target_apt}")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    asyncio.run(run())
