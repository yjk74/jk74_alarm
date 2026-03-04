import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

# 1. 설정값
TOKEN = "8643915197:AAHAxeM7oSIoQzxEk4KOMQ52QicRMXABE7s"
CHAT_ID = "8698887012"
# 파일 경로를 현재 작업 디렉토리 기준으로 설정
FILE_PATH = os.path.join(os.getcwd(), "last_apartment_name.txt")

SITE_URL = "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N"
BASE_URL = "https://www.khma.org"

async def send_msg(text):
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

async def run():
    # 저장된 데이터 로드 (파일이 없으면 빈 문자열)
    last_apt = ""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            last_apt = f.read().strip()
            print(f"기록된 마지막 아파트: {last_apt}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(SITE_URL, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 게시판 행 추출
        rows = soup.select("table.board_list tbody tr")
        
        target_apt = ""
        target_title = ""
        target_link = ""

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 6: continue
            
            # 번호가 '공지'이면 건너뜀
            if "공지" in cells[0].get_text(): continue

            # 이미지 기준 6번째(index 5)가 아파트명
            target_apt = cells[5].get_text(strip=True)
            target_title = cells[2].get_text(strip=True)
            
            link_tag = cells[2].find('a')
            if link_tag:
                target_link = link_tag.get('href', '')
                if target_link.startswith('/'):
                    target_link = BASE_URL + target_link
            break

        if target_apt:
            print(f"현재 최상단 아파트: {target_apt}")
            
            # 이전과 다르거나, 기록이 없을 때 알림
            if last_apt != target_apt:
                msg = (
                    f"<b>🏢 [신규 채용 공고]</b>\n\n"
                    f"<b>단지명:</b> {target_apt}\n"
                    f"<b>제목:</b> {target_title}\n\n"
                    f"<a href='{target_link}'>👉 자세히 보기</a>"
                )
                await send_msg(msg)
                
                # 파일에 새로운 아파트명 저장
                with open(FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(target_apt)
                print(f"✅ 새 단지 저장 완료: {target_apt}")
            else:
                print("🔄 변동 사항 없음 (이전과 동일한 단지).")
        else:
            print("⚠️ 게시글을 찾을 수 없습니다.")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    # 실행 시 무조건 돌아가도록 run()만 호출
    asyncio.run(run())
