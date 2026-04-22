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

RSS_SOURCES = [
    {'name': '한국경제', 'url': 'https://feeds.hankyung.com/app/economy.xml'},
    {'name': '매일경제', 'url': 'https://www.mk.co.kr/rss/30000001/'},
    {'name': '머니투데이', 'url': 'https://news.mt.co.kr/mtview/rss.xml'},
    {'name': '조선비즈', 'url': 'https://biz.chosun.com/rss/economics.xml'},
    {'name': 'Investing.com', 'url': 'https://kr.investing.com/rss/news.rss'},
]


def get_market_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    market = {}
    try:
        symbols = {
            'kospi': '^KS11',
            'kosdaq': '^KQ11',
            'nasdaq': '^IXIC',
            'sp500': '^GSPC',
            'usdkrw': 'USDKRW=X',
            'oil': 'CL=F',
        }
        for key, symbol in symbols.items():
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            prev = data['chart']['result'][0]['meta']['chartPreviousClose']
            change = price - prev
            pct = (change / prev) * 100
            market[key] = {
                'price': price,
                'change': change,
                'pct': pct
            }
            print(key, "수집 완료:", price)
    except Exception as e:
        print("시장 데이터 오류:", e)
    return market


def format_market(market):
    def arrow(val):
        return "🔺" if val >= 0 else "🔻"

    lines = []
    if 'kospi' in market:
        m = market['kospi']
        lines.append("🇰🇷 코스피: {:,.2f} {} ({:+.2f} / {:+.2f}%)".format(
            m['price'], arrow(m['change']), m['change'], m['pct']))
    if 'kosdaq' in market:
        m = market['kosdaq']
        lines.append("🇰🇷 코스닥: {:,.2f} {} ({:+.2f} / {:+.2f}%)".format(
            m['price'], arrow(m['change']), m['change'], m['pct']))
    if 'nasdaq' in market:
        m = market['nasdaq']
        lines.append("🇺🇸 나스닥: {:,.2f} {} ({:+.2f} / {:+.2f}%)".format(
            m['price'], arrow(m['change']), m['change'], m['pct']))
    if 'sp500' in market:
        m = market['sp500']
        lines.append("🇺🇸 S&P500: {:,.2f} {} ({:+.2f} / {:+.2f}%)".format(
            m['price'], arrow(m['change']), m['change'], m['pct']))
    if 'usdkrw' in market:
        m = market['usdkrw']
        lines.append("💱 달러/원: {:,.2f}원 {} ({:+.2f} / {:+.2f}%)".format(
            m['price'], arrow(m['change']), m['change'], m['pct']))
    if 'oil' in market:
        m = market['oil']
        lines.append("🛢 WTI유가: ${:.2f} {} ({:+.2f} / {:+.2f}%)".format(
            m['price'], arrow(m['change']), m['change'], m['pct']))
    return "\n".join(lines)


def get_news():
    headers = {'User-Agent': 'Mozilla/5.0'}
    all_news = []
    for source in RSS_SOURCES:
        try:
            response = requests.get(source['url'], headers=headers, timeout=10)
            root = ET.fromstring(response.content)
            count = 0
            for item in root.findall('.//item'):
                if count >= 2:
                    break
                title_tag = item.find('title')
                link_tag = item.find('link')
                desc_tag = item.find('description')
                if title_tag is None or link_tag is None:
                    continue
                title = title_tag.text.strip()
                link = link_tag.text.strip()
                desc = desc_tag.text.strip() if desc_tag is not None and desc_tag.text else '내용을 확인하세요.'
                if len(desc) > 150:
                    desc = desc[:150] + '...'
                all_news.append({'source': source['name'], 'title': title, 'desc': desc, 'link': link})
                count += 1
            print(source['name'] + " 수집 완료:", count)
        except Exception as e:
            print(source['name'] + " 오류:", e)
    return all_news


def send_telegram(market_text, news_items):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    msg = "📈 <b>" + today + " 투자 뉴스 브리핑</b>\n\n"
    msg += "📊 <b>주요 증시 현황</b>\n"
    msg += market_text + "\n\n"
    msg += "📰 <b>오늘의 주요 뉴스</b>\n"
    current_source = ""
    for item in news_items:
        if item['source'] != current_source:
            current_source = item['source']
            msg += "\n📌 <b>[" + current_source + "]</b>\n"
        msg += "• <b>" + item['title'] + "</b>\n"
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


def send_email(market_text, news_items):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    market_html = market_text.replace("\n", "<br>")
    news_html = ""
    current_source = ""
    for item in news_items:
        if item['source'] != current_source:
            current_source = item['source']
            news_html += "<h4 style='color:#1a73e8;margin-top:20px;'>📌 " + current_source + "</h4>"
        news_html += (
            "<div style='margin-bottom:15px;padding:12px;background:#f9f9f9;border-radius:8px;'>"
            "<b>" + item['title'] + "</b><br>"
            "<p style='color:#555;margin:5px 0;'>" + item['desc'] + "</p>"
            "<a href='" + item['link'] + "' style='color:#1a73e8;'>🔗 자세히 보기</a>"
            "</div>"
        )
    html = (
        "<html><body style='font-family:Arial;max-width:600px;margin:0 auto;'>"
        "<h2>📈 " + today + " 투자 뉴스 브리핑</h2>"
        "<h3>📊 주요 증시 현황</h3>"
        "<p style='background:#f0f7ff;padding:15px;border-radius:8px;line-height:2;'>"
        + market_html +
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
    market = get_market_data()
    market_text = format_market(market)
    print("시장 데이터:\n" + market_text)
    news_items = get_news()
    print("총 뉴스 수집 완료:", len(news_items))
    send_telegram(market_text, news_items)
    print("텔레그램 전송 완료!")
    send_email(market_text, news_items)
    print("이메일 전송 완료!")


if __name__ == "__main__":
    main()