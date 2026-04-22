import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from openai import OpenAI

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER = os.environ['GMAIL_USER']
GMAIL_PASSWORD = os.environ['GMAIL_PASSWORD']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

client = OpenAI(api_key=OPENAI_API_KEY)

def get_news():
    news_text = (
        "[오늘의 주요 투자 뉴스]\n"
        "1. 미 연준 금리 동결 결정, 시장 안도\n"
        "2. 코스피 2,600선 회복 시도\n"
        "3. 원달러 환율 1,340원대 안정\n"
        "4. 삼성전자 반도체 수출 호조\n"
        "5. 국제 유가 WTI 80달러선 유지\n"
    )
    return news_text

def analyze_with_ai(news_text):
    system_msg = (
        "당신은 전문 투자 애널리스트입니다. "
        "뉴스를 분석하여 다음 형식으로 정리해주세요:\n"
        "📊 거시경제 동향\n"
        "📈 주목 섹터/종목\n"
        "🌏 해외 시장 동향\n"
        "💡 오늘의 투자 인사이트\n"
        "⚠️ 리스크 요인"
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "다음 뉴스를 분석해주세요:\n" + news_text}
        ]
    )
    return response.choices[0].message.content

def send_telegram(message):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def send_email(subject, body):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    html = (
        "<html><body style='font-family:Arial;max-width:600px;margin:0 auto;'>"
        "<h2>📈 오늘의 투자 뉴스 브리핑</h2>"
        "<p>" + body.replace("\n", "<br>") + "</p>"
        "<hr>"
        "<h3>🔗 투자 사이트 바로가기</h3>"
        "<p>"
        "<a href='https://finance.naver.com'>네이버 금융</a> | "
        "<a href='https://www.investing.com'>인베스팅닷컴</a> | "
        "<a href='https://finance.yahoo.com'>야후 파이낸스</a>"
        "</p>"
        "</body></html>"
    )
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

def main():
    today = datetime.now().strftime("%Y년 %m월 %d일")
    news = get_news()
    insight = analyze_with_ai(news)
    telegram_msg = (
        "📈 <b>" + today + " 투자 뉴스 브리핑</b>\n\n"
        + insight +
        "\n\n🔗 <a href='https://finance.naver.com'>네이버 금융</a>\n"
        "🔗 <a href='https://www.investing.com'>인베스팅닷컴</a>\n"
        "🔗 <a href='https://finance.yahoo.com'>야후 파이낸스</a>"
    )
    send_telegram(telegram_msg)
    send_email("📈 " + today + " 투자 뉴스 브리핑", insight)
    print("완료!")

if __name__ == "__main__":
    main()
