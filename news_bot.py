import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']

def get_news():
    url = "https://news.google.com/rss/search?q=주식+투자+증시&hl=ko&gl=KR&ceid=KR:ko"
    response = requests.get(url)
    news_items = []
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    for item in root.findall('.//item')[:10]:
        title = item.find('title').text
        link = item.find('link').text
        news_items.append({'title': title, 'link': link})
    return news_items

def get_market_data():
    return (
        "📊 주요 증시 현황\n"
        "🇰🇷 코스피: finance.naver.com 확인\n"
        "🇺🇸 나스닥: finance.yahoo.com 확인\n"
        "💱 환율: finance.naver.com/marketindex 확인\n"
    )

def send_telegram(news_items):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    msg = "📈 <b>" + today + " 투자 뉴스 브리핑</b>\n\n"
    msg += get_market_data() + "\n"
    msg += "📰 <b>오늘의 주요 뉴스</b>\n"
    for i, item in enumerate(news_items, 1):
        msg += str(i) + ". <a href='" + item['link'] + "'>" + item['title'] + "</a>\n"
    msg += "\n🔗 <b>투자 사이트</b>\n"
    msg += "• <a href='https://finance.naver.com'>네이버 금융</a>\n"
    msg += "• <a href='https://www.investing.com'>인베스팅닷컴</a>\n"
    msg += "• <a href='https://finance.yahoo.com'>야후 파이낸스</a>"
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=data)

def send_email(news_items):
