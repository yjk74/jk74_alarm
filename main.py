import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import os

# 설정 값 (토큰과 ID는 그대로 유지)
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
    # 저장된 마지막 글 읽기
    last_titles = []
    if os.path.exists("last_titles.txt"):
        with open("last_titles.txt", "r", encoding="utf-8") as f:
            last_titles = [line.strip() for line in f.readlines()]

    new_titles = []
    # 브라우저처럼 보이기 위한 헤더 보강
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    for site in SITES:
        try:
            # verify=False를 추가해 SSL 보안 인증 에러 방지 (필요시)
            res = requests.get(site['url'], headers=headers, timeout=20)
            
            if res.status_code != 200:
                print(f"Error {site['name']}: Status Code {res.status_code}")
                continue

            soup = BeautifulSoup(res.text, 'html.parser')
            row = soup.select_one(site['selector'])
            
            if row:
                link_tag = row.find('a')
                if not link_tag: continue
                
                title = link_tag.get_text(strip=True)
                link = link_tag.get('href')
                
                if link.startswith('/'): link = site['base_url'] + link
                elif not link.startswith('http'): link = site['url'].rsplit('/', 1)[0] + '/' + link
                
                # 새로운 글 체크 로직 개선
                if title not in last_titles:
                    print(f"새 공고 발견: {title}")
                    msg = f"<b>[새 공고 - {site['name']}]</b>\n{title}\n<a href='{link}'>👉 상세보기</a>"
                    await send_msg(msg)
                
                new_titles.append(title)
            else:
                print(f"{site['name']}: 게시글을 찾을 수 없습니다 (Selector 확인 필요)")

        except Exception as e:
            print(f"Error {site['name']}: {e}")

    # 현재 확인한 글들을 저장 (성공한 것들만 업데이트 방지 위해 로직 유지)
    if new_titles:
        with open("last_titles.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(new_titles))

if __name__ == "__main__":
    asyncio.run(run())
