import os
import smtplib
import requests
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']

        
def get_news():
    news_items = [
        {'title': '코스피 오늘 시장 동향 확인', 'link': 'https://finance.naver.com/sise'},
        {'title': '오늘의 환율 정보', 'link': 'https://finance.naver.com/marketindex'},
        {'title': '미국 증시 현황', 'link': 'https://finance.yahoo.com'},
        {'title': '국제 유가 동향', 'link': 'https://www.investing.com/commodities/crude-oil'},
        {'title': '오늘의 투자 뉴스', 'link': 'https://finance.naver.com/news'},
    ]
    return news_items

def send_telegram(news_items):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    msg = "📈 <b>" + today + " 투자 뉴스 브리핑</b>\n\n"
    msg += "📊 주요 증시 현황\n"
    msg += "🇰🇷 <a href='https://finance.naver.com/sise'>코스피/코스닥</a>\n"
    msg += "🇺🇸 <a href='https://finance.yahoo.com'>나스닥/S&P500</a>\n"
    msg += "💱 <a href='https://finance.naver.com/marketindex'>환율</a>\n"
    msg += "🛢 <a href='https://www.investing.com/commodities/crude-oil'>유가</a>\n\n"
    msg += "📰 <b>오늘의 주요 뉴스</b>\n"
    for i, item in enumerate(news_items, 1):
        msg += str(i) + ". <a href='" + item['link'] + "'>" + item['title'] + "</a>\n"
    msg += "\n🔗 <b>투자 사이트</b>\n"
    msg += "• <a href='https://finance.naver.com'>네이버 금융</a>\n"
    msg += "• <a href='https://www.investing.com'>인베스팅닷컴</a>\n"
    msg += "• <a href='https://finance.yahoo.com'>야후 파이낸스</a>"
    url = "https://api.telegram.org/bot" + TELEGRAM