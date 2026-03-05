import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os
from datetime import datetime
import html

# 1. 설정값
TOKEN = "8643915197:AAHAxeM7oSIoQzxEk4KOMQ52QicRMXABE7s"
CHAT_ID = "8698887012"
FILE_PATH = os.path.join(os.getcwd(), "last_checked_apt.txt")

# 인천 전체 공고 URL
SITE_URL = "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N"

async def send_msg(text):
    """텔레그램 메시지 전송 (HTML 모드 적용)"""
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

async def check_job():
    """게시판을 확인하고 아파트명이 변경되면 알림을 보냅니다 (링크 제외 버전)."""
    last_apt = ""
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            last_apt = f.read().strip()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(SITE_URL, headers=headers, timeout=30)
        res.raise_for_status()
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        rows = soup.find_all('tr')
        target_apt = ""
        target_title = ""

        for row in rows:
            text_line = row.get_text("|", strip=True)
            columns = [c.strip() for c in text_line.split("|") if c.strip()]

            if len(columns) < 7: continue
            if not columns[0].isdigit(): continue

            # 데이터 추출
            target_apt = columns[-4]
            target_title = columns[2]
            break

        if target_apt:
            target_apt = target_apt.replace("|", "").strip()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if last_apt != target_apt:
                print(f"[{current_time}] 🆕 새 단지 발견: {target_apt}")

                # 안전한 텍스트 처리를 위해 escape 적용
                safe_apt = html.escape(target_apt)
                safe_title = html.escape(target_title)

                # 메시지 구성 (링크 제거)
                msg = (
                    f"<b>🏠 [인천 신규 공고 알림]</b>\n\n"
                    f"<b>📍 단지명:</b> {safe_apt}\n"
                    f"<b>📝 제목:</b> {safe_title}\n\n"
                    f"📢 상세 내용은 PC에서 확인해 주세요."
                )

                await send_msg(msg)

                with open(FILE_PATH, "w", encoding="utf-8") as f:
                    f.write(target_apt)
            else:
                print(f"[{current_time}] 🔄 변동 없음 (최근: {target_apt})")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ 데이터를 찾을 수 없습니다.")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")

async def main():
    interval = 1800 # 30분
    print(f"🚀 모니터링 시작 (주기: 30분)")

    while True:
        await check_job()
        await asyncio.sleep(interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
