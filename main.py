import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

# 설정 값
TOKEN = "8643915197:AAHAxeM7oSiOqzEk4KOMQ52qicRMXABE7S"
CHAT_ID = "8698887012"

# 인천인재평생교육원 제외, 사이트별 체크 기준 설정
SITES = [
    {
        "name": "연수구청 채용공고", 
        "url": "https://www.yeonsu.go.kr/main/community/notify/job.asp", 
        "base_url": "https://www.yeonsu.go.kr", 
        "selector": ".table_style_1 tbody tr",
        "check_type": "title"  # 제목 기준
    },
    {
        "name": "대한주택관리사협회 인천", 
        "url": "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N", 
        "base_url": "https://www.khma.org", 
        "selector": ".board_list tbody tr",
        "check_type": "region" # 근무지역 기준
    }
]

async def send_msg(text):
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

async def run():
    # 저장된 마지막 데이터 읽기
    last_data = {}
    if os.path.exists("last_check_values.txt"):
        with open("last_check_values.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    s_name, s_val = line.strip().split(":", 1)
                    last_data[s_name] = s_val

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    for site in SITES:
        try:
            print(f"🔍 {site['name']} 확인 중 (기준: {site['check_type']})...")
            res = requests.get(site['url'], headers=headers, timeout=20)
            if res.status_code != 200:
                print(f"⚠️ {site['name']} 접속 실패")
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select(site['selector'])
            
            target_row = None
            for row in rows:
                if "공지" in row.get_text() or "NOTICE" in row.get_text().upper():
                    continue
                target_row = row
                break

            if target_row:
                cells = target_row.find_all('td')
                link_tag = target_row.find('a')
                
                # 체크할 값 결정
                check_value = ""
                if site['check_type'] == "title":
                    check_value = link_tag.get_text(strip=True) if link_tag else "제목없음"
                elif site['check_type'] == "region":
                    # 대한주택관리사협회 기준: 보통 2번째 td가 지역(인천 중구 등)임
                    check_value = cells[1].get_text(strip=True) if len(cells) > 1 else "지역없음"

                # 상세 링크 처리
                link = link_tag.get('href', '') if link_tag else ""
                if link.startswith('/'): link = site['base_url'] + link
                elif link and not link.startswith('http'): link = site['url'].rsplit('/', 1)[0] + '/' + link
                
                # 업데이트 확인
                if last_data.get(site['name']) != check_value:
                    print(f"✅ {site['name']} 업데이트 발견: {check_value}")
                    display_title = link_tag.get_text(strip=True) if link_tag else check_value
                    msg = f"<b>[새 공고 - {site['name']}]</b>\n기준값: {check_value}\n제목: {display_title}\n<a href='{link}'>👉 상세보기</a>"
                    await send_msg(msg)
                    last_data[site['name']] = check_value
                else:
                    print(f"😴 {site['name']}: 변동 사항 없음")

        except Exception as e:
            print(f"🔥 Error {site['name']}: {e}")

    # 최종 상태 저장
    with open("last_check_values.txt", "w", encoding="utf-8") as f:
        for s_name, s_val in last_data.items():
            f.write(f"{s_name}:{s_val}\n")

if __name__ == "__main__":
    # 실행 시 무조건 테스트 메시지 발송 (정상 작동 확인용)
    asyncio.run(send_msg("🤖 봇이 체크를 시작합니다!"))
    asyncio.run(run())
