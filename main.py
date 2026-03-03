import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

TOKEN = "8643915197:AAHAxeM7oSiOqzEk4KOMQ52qicRMXABE7S"
CHAT_ID = "8698887012"

SITES = [
    {"name": "인천인재평생교육진흥원", "url": "https://itle.or.kr/user/board/list.do?bbs_id=bbs_136", "base_url": "https://itle.or.kr", "selector": "tbody tr"},
    {"name": "연수구청 채용공고", "url": "https://www.yeonsu.go.kr/main/community/notify/job.asp", "base_url": "https://www.yeonsu.go.kr", "selector": ".table_style_1 tbody tr"},
    {"name": "대한주택관리협회 인천", "url": "https://www.khma.org/portal/00011/00109/00114.web?sido=incheon&isEnd=N", "base_url": "https://www.khma.org", "selector": ".board_list tbody tr"}
]

async def send_msg(text):
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

async def run():
    # 저장된 데이터 읽기 (딕셔너리 형태로 관리하여 사이트별 매칭 정확도 향상)
    last_titles_dict = {}
    if os.path.exists("last_titles.txt"):
        with open("last_titles.txt", "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    s_name, s_title = line.strip().split(":", 1)
                    last_titles_dict[s_name] = s_title

    current_titles = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    for site in SITES:
        try:
            # SSL 인증 에러 방지를 위해 verify=False 추가 검토
            res = requests.get(site['url'], headers=headers, timeout=20, verify=True)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select(site['selector']) # select_one 대신 전체 행을 가져옴
            
            target_row = None
            for row in rows:
                # '공지', 'Notice' 텍스트가 포함된 행은 건너뜀 (사이트마다 다를 수 있음)
                if "공지" in row.get_text() or "NOTICE" in row.get_text().upper():
                    continue
                target_row = row
                break # 공지가 아닌 첫 번째 행을 찾으면 중단

            if target_row:
                link_tag = target_row.find('a')
                if not link_tag: continue
                
                title = link_tag.get_text(strip=True)
                # 제목이 너무 짧거나 공백인 경우 방지
                if not title:
                    title = link_tag.get('title', '제목 없음').strip()

                link = link_tag.get('href')
                if link.startswith('/'): link = site['base_url'] + link
                elif not link.startswith('http'): link = site['url'].rsplit('/', 1)[0] + '/' + link
                
                # 이전 저장된 제목과 비교
                if site['name'] not in last_titles_dict or last_titles_dict[site['name']] != title:
                    print(f"[{site['name']}] 새 공고 발견: {title}")
                    msg = f"<b>[새 공고 - {site['name']}]</b>\n{title}\n<a href='{link}'>👉 상세보기</a>"
                    await send_msg(msg)
                    last_titles_dict[site['name']] = title
                else:
                    print(f"[{site['name']}] 새로운 글 없음")
            
        except Exception as e:
            print(f"Error {site['name']}: {e}")

    # 최종 상태 저장
    with open("last_titles.txt", "w", encoding="utf-8") as f:
        for s_name, s_title in last_titles_dict.items():
            f.write(f"{s_name}:{s_title}\n")

if __name__ == "__main__":
    asyncio.run(run())
