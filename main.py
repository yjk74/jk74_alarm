import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

# 1. 설정값 (본인의 정보로 유지됨)
TOKEN = "8643915197:AAHAxeM7oSIoQzxEk4KOMQ52QicRMXABE7s"
CHAT_ID = "8698887012"
FILE_PATH = "last_apartment_name.txt"

# 2. 사이트 정보 (이미지 구조 반영)
SITE_URL = "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N"
BASE_URL = "https://www.khma.org"

async def send_msg(text):
    """텔레그램 메시지 전송 함수"""
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

async def run():
    # 저장된 마지막 아파트명 불러오기
    last_apt = ""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            last_apt = f.read().strip()

    # 브라우저처럼 보이기 위한 헤더 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(SITE_URL, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 게시판 테이블의 모든 행(tr) 가져오기
        rows = soup.select("table.board_list tbody tr")
        
        target_apt = ""
        target_title = ""
        target_link = ""

        for row in rows:
            cells = row.find_all('td')
            # 최소 6개 이상의 칸(td)이 있어야 아파트명(6번째)을 찾을 수 있음
            if len(cells) < 6:
                continue
            
            # 1번째 칸(번호)에 '공지'가 있으면 실제 채용공고가 아니므로 건너뜀
            num_text = cells[0].get_text(strip=True)
            if "공지" in num_text:
                continue

            # --- 이미지 분석 결과 반영된 인덱스 ---
            # cells[2]: 채용제목 (3번째 칸)
            # cells[5]: 아파트명 (6번째 칸)
            target_apt = cells[5].get_text(strip=True)
            target_title = cells[2].get_text(strip=True)
            
            # 링크 추출 (채용제목 칸 안에 있는 a 태그)
            link_tag = cells[2].find('a')
            if link_tag:
                target_link = link_tag.get('href', '')
                if target_link.startswith('/'):
                    target_link = BASE_URL + target_link
            
            # 가장 위에 있는 '진짜 공고' 하나를 찾았으므로 루프 중단
            break

        # 추출된 아파트명이 있고, 이전과 다를 때만 알림 전송
        if target_apt:
            if last_apt != target_apt:
                msg = (
                    f"<b>🏢 [새로운 구인 공고]</b>\n\n"
                    f"<b>단지명:</b> {target_apt}\n"
                    f"<b>제목:</b> {target_title}\n\n"
                    f"<a href='{target_link}'>👉 공고 바로가기 (클릭)</a>"
                )
                
                await send_msg(msg)
                
                # 새로운 아파트명을 파일에 저장 (다음 비교용)
                with open(FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(target_apt)
                print(f"✅ 새 단지 알림 발송: {target_apt}")
            else:
                print(f"🔄 최신 공고 단지가 이전과 동일함 ({target_apt}). 알림 생략.")
        else:
            print("⚠️ 게시글 데이터를 찾을 수 없습니다.")

    except Exception as e:
        print(f"❌ 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    # 테스트 메시지는 주석 처리했습니다. 
    # 정말 작동하는지 보고 싶으시면 아래 줄의 #을 지우고 실행해 보세요.
    # asyncio.run(send_msg("🚀 봇 모니터링이 시작되었습니다!"))
    
    asyncio.run(run())
