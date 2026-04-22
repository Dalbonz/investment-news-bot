import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']


def get_news():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_items = []
    for item in soup.select('ul.type2 li')[:5]:
        a_tag = item.select_one('a')
        if not a_tag:
            continue
        title = a_tag.text.strip()
        link = a_tag['href']
        desc_tag = item.select_one('.lede')
        desc = desc_tag.text.strip() if desc_tag else '본문을 확인하세요.'
        news_items.append({'title': title, 'desc': desc, 'link': link})
    return news_items


def send_telegram(news_items):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    msg = "📈 <b>" + today + " 투자 뉴스 브리핑</b>\n\n"
    msg += "📊 주요 증시 현황\n"
    msg += "🇰🇷 <a href='https://finance.naver.com/sise'>코스피/코스닥</a>\n"
    msg += "🇺🇸 <a href='https://finance.yahoo.com'>나스닥/S&P500</a>\n"
    msg += "💱 <a href='https://finance.naver.com/marketindex'>환율</a>\n"
    msg += "🛢 <a href='https://www.investing.com/commodities/crude-oil'>유가</a>\n\n"
    msg += "📰 <b>오늘의 주요 뉴스</b>\n\n"
    for i, item in enumerate(news_items, 1):
        msg += str(i) + ". <b>" + item['title'] + "</b>\n"
        msg += item['desc'] + "\n"
        msg += "<a href='" + item['link'] + "'>🔗 자세히 보기</a>\n\n"
    msg += "🔗 <b>투자 사이트</b>\n"
    msg += "• <a href='https://finance.naver.com'>네이버 금융</a>\n"
    msg += "• <a href='https://www.investing.com'>인베스팅닷컴</a>\n"
    msg += "• <a href='https://finance.yahoo.com'>야후 파이낸스</a>"
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    print("텔레그램 응답:", response.text)


def send_email(news_items):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    news_html = ""
    for i, item in enumerate(news_items, 1):
        news_html += (
            "<div style='margin-bottom:20px;padding:15px;background:#f9f9f9;border-radius:8px;'>"
            "<h4 style='margin:0 0 8px 0;'>" + str(i) + ". " + item['title'] + "</h4>"
            "<p style='margin:0 0 8px 0;color:#555;'>" + item['desc'] + "</p>"
            "<a href='" + item['link'] + "' style='color:#1a73e8;'>🔗 자세히 보기</a>"
            "</div>"
        )
    html = (
        "<html><body style='font-family:Arial;max-width:600px;margin:0 auto;'>"
        "<h2>📈 " + today + " 투자 뉴스 브리핑</h2>"
        "<h3>📊 주요 증시 현황</h3>"
        "<p>"
        "🇰🇷 <a href='https://finance.naver.com/sise'>코스피/코스닥</a><br>"
        "🇺🇸 <a href='https://finance.yahoo.com'>나스닥/S&P500</a><br>"
        "💱 <a href='https://finance.naver.com/marketindex'>환율</a><br>"
        "🛢 <a href='https://www.investing.com/commodities/crude-oil'>유가</a>"
        "</p>"
        "<h3>📰 오늘의 주요 뉴스</h3>"
        + news_html +
        "<hr>"
        "<h3>🔗 투자 사이트 바로가기</h3>"
        "<p>"
        "<a href='https://finance.naver.com'>네이버 금융</a> | "
        "<a href='https://www.investing.com'>인베스팅닷컴</a> | "
        "<a href='https://finance.yahoo.com'>야후 파이낸스</a>"
        "</p>"
        "</body></html>"
    )
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "📈 " + today + " 투자 뉴스 브리핑"
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
    print("이메일 전송 완료!")


def main():
    print("시작!")
    news_items = get_news()
    print("뉴스 수집 완료:", len(news_items))
    send_telegram(news_items)
    print("텔레그램 전송 완료!")
    send_email(news_items)
    print("이메일 전송 완료!")


if __name__ == "__main__":
    main()