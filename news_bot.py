import os, json, smtplib, requests, xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

TELEGRAM_TOKEN   = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER       = os.environ['GMAIL_USER']
GMAIL_PASSWORD   = os.environ['GMAIL_PASSWORD']
OPENAI_API_KEY   = os.environ.get('OPENAI_API_KEY', '')

HEADERS = {'User-Agent': 'Mozilla/5.0'}

SYMBOLS = {
    'kospi':   '^KS11',  'kosdaq':  '^KQ11',
    'nasdaq':  '^IXIC',  'sp500':   '^GSPC',
    'ndx':     '^NDX',   'nikkei':  '^N225',
    'usdkrw':  'USDKRW=X', 'usdjpy': 'USDJPY=X',
    'eurusd':  'EURUSD=X', 'dxy':   'DX-Y.NYB',
    'oil':     'CL=F',   'gold':    'GC=F',
    'silver':  'SI=F',   'copper':  'HG=F',
    'aapl':    'AAPL',   'nvda':    'NVDA',
    'tsla':    'TSLA',   'msft':    'MSFT',
    'spy':     'SPY',    'qqq':     'QQQ',
    'samsung': '005930.KS', 'hynix': '000660.KS',
    'hanwha':  '012450.KS', 'hyundai':'005380.KS',
}

RSS_SOURCES = [
    {'name': '한국경제', 'url': 'https://feeds.hankyung.com/app/stock.xml'},
    {'name': '매일경제', 'url': 'https://www.mk.co.kr/rss/30100041/'},
    {'name': '머니투데이', 'url': 'https://news.mt.co.kr/mtview/rss/stock.xml'},
    {'name': '조선비즈', 'url': 'https://biz.chosun.com/rss/economics.xml'},
    {'name': 'Investing.com', 'url': 'https://kr.investing.com/rss/news.rss'},
]

INVEST_KW  = ['주식','증시','코스피','코스닥','나스닥','S&P','금리','환율','달러','유가','원자재','채권','ETF','펀드','투자','매수','매도','실적','수출','무역','경제','GDP','인플레','연준','Fed','반도체','배당','IPO','공모','상장']
EXCLUDE_KW = ['연예','드라마','영화','아이돌','가수','배우','스포츠','축구','야구','골프','패션','뷰티','다이어트','맛집','여행','결혼','이혼','열애']

def is_invest_news(title):
    if any(k in title for k in EXCLUDE_KW): return False
    return any(k in title for k in INVEST_KW)

# ── 시장 데이터 ──
def get_market_data():
    market = {}
    for key, symbol in SYMBOLS.items():
        try:
            url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol
            res = requests.get(url, headers=HEADERS, timeout=10)
            d   = res.json()['chart']['result'][0]
            meta = d['meta']
            price = meta['regularMarketPrice']
            prev  = meta['chartPreviousClose']
            chg   = price - prev
            pct   = chg / prev * 100
            market[key] = {
                'price': round(price, 4),
                'change': round(chg, 4),
                'pct': round(pct, 2),
                'high': meta.get('regularMarketDayHigh', 0),
                'low':  meta.get('regularMarketDayLow',  0),
                'vol':  meta.get('regularMarketVolume',  0),
            }
        except Exception as e:
            print(f'{key} 오류: {e}')
    return market

# ── 뉴스 ──
def get_news():
    all_news = []
    for source in RSS_SOURCES:
        try:
            res  = requests.get(source['url'], headers=HEADERS, timeout=10)
            root = ET.fromstring(res.content)
            cnt  = 0
            for item in root.findall('.//item'):
                if cnt >= 3: break
                t = item.find('title')
                l = item.find('link')
                if t is None or l is None: continue
                title = t.text.strip()
                link  = l.text.strip()
                if not is_invest_news(title): continue
                all_news.append({'source': source['name'], 'title': title, 'link': link})
                cnt += 1
        except Exception as e:
            print(source['name'], '오류:', e)
    return all_news

# ── OpenAI 분석 코멘트 ──
def get_ai_comment(market):
    if not OPENAI_API_KEY:
        return '오늘의 시장 분석을 불러오지 못했어요.'
    try:
        summary = []
        name_map = {
            'kospi':'코스피','kosdaq':'코스닥','nasdaq':'나스닥','sp500':'S&P500',
            'usdkrw':'달러/원','oil':'WTI유가','gold':'금','nvda':'엔비디아','tsla':'테슬라'
        }
        for k, label in name_map.items():
            if k in market:
                m = market[k]
                summary.append(f"{label}: {m['price']} ({m['pct']:+.2f}%)")
        prompt = (
            "당신은 전문 증권 애널리스트입니다. 아래 오늘의 시장 데이터를 보고 "
            "투자자를 위한 간결한 시황 분석 코멘트를 한국어로 3~4문장으로 작성해주세요.\n\n"
            "시장 데이터:\n" + "\n".join(summary)
        )
        res = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 300},
            timeout=15
        )
        return res.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print('AI 코멘트 오류:', e)
        return '오늘의 시장 분석을 불러오지 못했어요.'

# ── data.json 저장 ──
def save_data_json(market, news, ai_comment):
    data = {
        'updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'market':  market,
        'news':    news,
        'ai_comment': ai_comment,
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('data.json 저장 완료!')

# ── 텔레그램 ──
def send_telegram(market, news, ai_comment):
    def arrow(v): return '🔺' if v >= 0 else '🔻'
    today = datetime.now().strftime('%Y년 %m월 %d일')
    msg = f'📈 <b>{today} 투자 브리핑</b>\n\n'

    msg += '🤖 <b>AI 시황 코멘트</b>\n' + ai_comment + '\n\n'

    msg += '📊 <b>주요 증시</b>\n'
    for k, label in [('kospi','코스피'),('kosdaq','코스닥'),('nasdaq','나스닥'),('sp500','S&P500')]:
        if k in market:
            m = market[k]
            msg += f"{label}: {m['price']:,.2f} {arrow(m['change'])} ({m['pct']:+.2f}%)\n"

    msg += '\n💱 <b>환율/원자재</b>\n'
    for k, label in [('usdkrw','달러/원'),('oil','WTI'),('gold','금')]:
        if k in market:
            m = market[k]
            msg += f"{label}: {m['price']:,.2f} {arrow(m['change'])} ({m['pct']:+.2f}%)\n"

    msg += '\n📰 <b>주요 뉴스</b>\n'
    cur = ''
    for item in news:
        if item['source'] != cur:
            cur = item['source']
            msg += f"\n📌 <b>[{cur}]</b>\n"
        msg += f"• {item['title']}\n<a href=\"{item['link']}\">🔗 자세히 보기</a>\n\n"

    msg += '🌐 <a href="https://dalbonz.github.io/investment-news-bot">📊 대시보드 바로가기</a>'

    requests.post(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
        data={'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'}
    )
    print('텔레그램 전송 완료!')

# ── 이메일 ──
def send_email(market, news, ai_comment):
    def arrow(v): return '🔺' if v >= 0 else '🔻'
    today = datetime.now().strftime('%Y년 %m월 %d일')

    rows = ''
    for k, label in [('kospi','코스피'),('kosdaq','코스닥'),('nasdaq','나스닥'),('sp500','S&P500'),
                     ('usdkrw','달러/원'),('oil','WTI유가'),('gold','금')]:
        if k in market:
            m = market[k]
            color = '#16a34a' if m['change'] >= 0 else '#dc2626'
            rows += f"<tr><td>{label}</td><td>{m['price']:,.2f}</td><td style='color:{color}'>{m['pct']:+.2f}%</td></tr>"

    news_html = ''
    cur = ''
    for item in news:
        if item['source'] != cur:
            cur = item['source']
            news_html += f"<h4 style='color:#1a73e8'>📌 {cur}</h4>"
        news_html += f"<div style='margin-bottom:10px;padding:10px;background:#f9f9f9;border-radius:8px'><b>{item['title']}</b><br><a href='{item['link']}' style='color:#1a73e8'>🔗 자세히 보기</a></div>"

    html = f"""
    <html><body style='font-family:Arial;max-width:640px;margin:0 auto;padding:20px'>
    <h2>📈 {today} 투자 브리핑</h2>
    <div style='background:#f0f7ff;padding:15px;border-radius:10px;margin-bottom:20px'>
      <b>🤖 AI 시황 코멘트</b><br><br>{ai_comment}
    </div>
    <h3>📊 주요 증시</h3>
    <table style='width:100%;border-collapse:collapse;font-size:14px'>
      <tr style='background:#f8fafc'><th style='text-align:left;padding:8px'>지수</th><th>현재가</th><th>등락률</th></tr>
      {rows}
    </table>
    <br>
    <a href='https://dalbonz.github.io/investment-news-bot' style='background:#1a73e8;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block;margin-bottom:20px'>📊 대시보드 바로가기</a>
    <h3>📰 주요 뉴스</h3>{news_html}
    </body></html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'📈 {today} 투자 브리핑'
    msg['From']    = GMAIL_USER
    msg['To']      = GMAIL_USER
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASSWORD)
        s.send_message(msg)
    print('이메일 전송 완료!')

# ── 메인 ──
def main():
    print('시작!')
    market     = get_market_data()
    news       = get_news()
    ai_comment = get_ai_comment(market)
    save_data_json(market, news, ai_comment)
    send_telegram(market, news, ai_comment)
    send_email(market, news, ai_comment)
    print('완료!')

if __name__ == '__main__':
    main()
