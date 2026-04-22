import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from openai import OpenAI

# 환경변수
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

client = OpenAI(api_key=OPENAI_API_KEY)

def get_news():
    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": "pub_test",
        "q": "주식 투자 금리 환율 증시",
        "language": "ko",
        "category": "business"
    }
    # 네이버 금융 뉴스 RSS 사용
    rss_urls = [
        "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258",
    ]
    
    news_text = """
    [오늘의 주요 투자 뉴스 - 실제 API 연동 전 테스트]
    1. 미 연준 금리 동결 결정, 시장 안도
    2. 코스피 2,600선 회복 시도
    3. 원달러 환율 1,340원대 안정
    4. 삼성전자 반도체 수출 호조
    5. 국제 유가 WTI 80달러선 유지
    """
    return news_text

def analyze_with_ai(news_text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """당신은 전문 투자 애널리스트입니다. 
                뉴스를 분석하여 다음 형식으로 정리해주세요:
                
                📊 거시경제 동향
                📈 주목 섹터/종목
                🌏 해외 시장 동향
