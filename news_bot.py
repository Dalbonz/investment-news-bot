import os, json, smtplib, requests, xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

TELEGRAM_TOKEN   = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
GMAIL_USER       = os.environ['GMAIL_USER']
GMAIL_PASSWORD   = os.environ['GMAIL_PASSWORD']
OPENAI_API_KEY   = os.environ.get('OPENAI_API_KEY', '')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

SYMBOLS = {
    'kospi':   '000001.KS',  'kosdaq':  'KOSDAQ.KQ',
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
    {'name': '매일경제',     'url': 'https://www.mk.co.kr/rss/30100041/'},
    {'name': '머니투데이',   'url': 'https://news.mt.co.kr/mtview/rss/stock.xml'},
    {'name': 'Investing.com','url': 'https://kr.investing.com/rss/news.rss'},
    {'name': '연합뉴스',     'url': 'https://www.yonhapnewstv.co.kr/feed/'},
]

INVEST_KW  = ['주식','증시','코스피','코스닥','나스닥','S&P','금리','환율','달러','유가','원자재','채권','ETF','펀드','투자','매수','매도','실적','수출','무역','경제','GDP','인플레','연준','Fed','반도체','배당','IPO','공모','상장']
EXCLUDE_KW = ['연예','드라마','영화','아이돌','가수','배우','스포츠','축구','야구','골프','패션','뷰티','다이어트','맛집','여행','결혼','이혼','열애']

def is_invest_news(title):
    if any(k in title for k in EXCLUDE_KW): return False
    return any(k in title for k in INVEST_KW)

def get_market_data():
    market = {}
    for key, symbol in SYMBOLS.items():
        try:
            url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?interval=1d&range=5d'
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()
            d    = res.json()['chart']['result'][0]
            meta = d['meta']
            q    = d['indicators']['quote'][0]
            ts   = d.get('timestamp', [])

            price = meta['regularMarketPrice']
            prev  = meta.get('chartPreviousClose', price)
            chg   = price - prev
            pct   = round(chg / prev * 100, 2) if prev else 0

            candles = []
            opens  = q.get('open',  [])
            highs  = q.get('high',  [])
            lows   = q.get('low',   [])
            closes = q.get('close', [])
            vols   = q.get('volume',[])
            for i, t in enumerate(ts):
                try:
                    c = closes[i]
                    if c is None: continue
                    candles.append({
                        'time':  int(t),
                        'open':  round(opens[i]  or c, 4),
                        'high':  round(highs[i]  or c, 4),
                        'low':   round(lows[i]   or c, 4),
                        'close': round(c, 4),
                        'vol':   int(vols[i] or 0) if i < len(vols) else 0,
                    })
                except:
                    pass

            market[key] = {
                'price':   round(price, 4),
                'change':  round(chg, 4),
                'pct':     pct,
                'high':    round(meta.get('regularMarketDayHigh', 0), 4),
                'low':     round(meta.get('regularMarketDayLow',  0), 4),
                'vol':     meta.get('regularMarketVolume', 0),
                'candles': candles,
            }
            print(key + ': ' + str(price))
        except Exception as e:
            print(key + ' 오류: ' + str(e))
    return market

def get_news():
    all_news = []
    for source in RSS_SOURCES:
        try:
            res = requests.get(source['url'], headers=HEADERS, timeout=10)
            res.raise_for_status()
            content = res.content
            for b in [b'\x00',b'\x08',b'\x0b',b'\x0c',b'\x0e',b'\x1f']:
                content = content.replace(b, b'')
            root = ET.fromstring(content)
            cnt  = 0
            for item in root.findall('.//item'):
                if cnt >= 3: break
                t = item.find('title')
                l = item.find('link')
                if t is None or l is None: continue
                title = (t.text or '').strip()
                link  = (l.text or '').strip()
                if not title or not is_invest_news(title): continue
                all_news.append({'source': source['name'], 'title': title, 'link': link})
                cnt += 1
            print(source['name'] + ': ' + str(cnt) + '개')
        except Exception as e:
            print(source['name'] + ' 오류: ' + str(e))
    return all_news

def get_ai_comment(market):
    if not OPENAI_API_KEY:
        return '오늘의 시장 분석을 불러오지 못했어요.'
    try:
        name_map = {
            'kospi':'코스피','kosdaq':'코스닥','nasdaq':'나스닥','sp500':'S&P500',
            'usdkrw':'달러/원','oil':'WTI유가','gold':'금','nvda':'엔비디아','tsla':'테슬라'
        }
        summary = []
        for k, label in name_map.items():
            if k in market:
                m = market[k]
                summary.append(label + ': ' + str(m['price']) + ' (' + ('+' if m['pct']>=0 else '') + str(m['pct']) + '%)')

        prompt = (
            '당신은 전문 증권 애널리스트입니다. '
            '아래 오늘의 시장 데이터를 보고 투자자를 위한 간결한 시황 분석 코멘트를 '
            '한국어로 3~4문장으로 작성해주세요.\n\n'
            '시장 데이터:\n' + '\n'.join(summary)
        )
        res = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={'Authorization': 'Bearer ' + OPENAI_API_KEY, 'Content-Type': 'application/json'},
            json={'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 300},
            timeout=20
        )
        result = res.json()
        print('OpenAI 응답: ' + str(result))
        if 'choices' in result:
            return result['choices'][0]['message']['content'].strip()
        elif 'error' in result:
            print('OpenAI 에러: ' + str(result['error']))
            return '시장 분석 생성 중 오류가 발생했어요.'
        return '시장 분석을 불러오지 못했어요.'
    except Exception as e:
        print('AI 코멘트 오류: ' + str(e))
        return '시장 분석을 불러오지 못했어요.'

def save_data_json(market, news, ai_comment):
    data = {
        'updated':    datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'market':     market,
        'news':       news,
        'ai_comment': ai_comment,
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('data.json 저장 완료!')

def send_telegram(market, news, ai_comment):
    today = datetime.now().strftime('%Y년 %m월 %d일')
    msg = '📈 <b>' + today + ' 투자 브리핑</b>\n\n'
    msg += '🤖 <b>AI 시황 코멘트</b>\n' + ai_comment + '\n\n'
    msg += '📊 <b>주요 증시</b>\n'
    for k, label in [('kospi','코스피'),('kosdaq','코스닥'),('nasdaq','나스닥'),('sp500','S&P500')]:
        if k in market:
            m = market[k]
            arrow = '🔺' if m['change'] >= 0 else '🔻'
            msg += label + ': ' + '{:,.2f}'.format(m['price']) + ' ' + arrow + ' (' + ('+' if m['pct']>=0 else '') + '{:.2f}'.format(m['pct']) + '%)\n'
    msg += '\n💱 <b>환율</b>\n'
    for k, label in [('usdkrw','달러/원'),('usdjpy','엔/달러'),('eurusd','유로/달러')]:
        if k in market:
            m = market[k]
            arrow = '🔺' if m['change'] >= 0 else '🔻'
            msg += label + ': ' + '{:,.2f}'.format(m['price']) + ' ' + arrow + ' (' + ('+' if m['pct']>=0 else '') + '{:.2f}'.format(m['pct']) + '%)\n'
    msg += '\n🛢 <b>원자재</b>\n'
    for k, label in [('oil','WTI'),('gold','금'),('silver','은')]:
        if k in market:
            m = market[k]
            arrow = '🔺' if m['change'] >= 0 else '🔻'
            msg += label + ': ' + '{:,.2f}'.format(m['price']) + ' ' + arrow + ' (' + ('+' if m['pct']>=0 else '') + '{:.2f}'.format(m['pct']) + '%)\n'
    msg += '\n📰 <b>주요 뉴스</b>\n'
    cur = ''
    for item in news:
        if item['source'] != cur:
            cur = item['source']
            msg += '\n📌 <b>[' + cur + ']</b>\n'
        msg += '• ' + item['title'] + '\n<a href="' + item['link'] + '">🔗 자세히 보기</a>\n\n'
    msg += '🌐 <a href="https://dalbonz.github.io/investment-news-bot">📊 대시보드 바로가기</a>'
    res = requests.post(
        'https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage',
        data={'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'},
        timeout=15
    )
    print('텔레그램 응답: ' + str(res.status_code))

def send_email(market, news, ai_comment):
    today = datetime.now().strftime('%Y년 %m월 %d일')
    rows = ''
    for k, label in [('kospi','코스피'),('kosdaq','코스닥'),('nasdaq','나스닥'),('sp500','S&P500'),('usdkrw','달러/원'),('oil','WTI유가'),('gold','금')]:
        if k in market:
            m = market[k]
            chg_color = '#16a34a' if m['change'] >= 0 else '#dc2626'
            rows += '<tr>'
            rows += '<td style="padding:6px">' + label + '</td>'
            rows += '<td style="padding:6px;text-align:right">' + '{:,.2f}'.format(m['price']) + '</td>'
            rows += '<td style="padding:6px;text-align:right;color:' + chg_color + '">' + ('+' if m['pct']>=0 else '') + '{:.2f}'.format(m['pct']) + '%</td>'
            rows += '</tr>'
    news_html = ''
    cur = ''
    for item in news:
        if item['source'] != cur:
            cur = item['source']
            news_html += '<h4 style="color:#1a73e8;margin-top:16px">📌 ' + cur + '</h4>'
        news_html += '<div style="margin-bottom:10px;padding:10px;background:#f9f9f9;border-radius:8px">'
        news_html += '<b>' + item['title'] + '</b><br>'
        news_html += '<a href="' + item['link'] + '" style="color:#1a73e8;font-size:0.9em">🔗 자세히 보기</a>'
        news_html += '</div>'
    html = (
        '<html><body style="font-family:Arial;max-width:640px;margin:0 auto;padding:20px;color:#222">'
        '<h2 style="border-bottom:2px solid #1a73e8;padding-bottom:8px">📈 ' + today + ' 투자 브리핑</h2>'
        '<div style="background:#f0f7ff;padding:15px;border-radius:10px;margin:16px 0;line-height:1.7">'
        '<b>🤖 AI 시황 코멘트</b><br><br>' + ai_comment +
        '</div>'
        '<h3>📊 주요 시장</h3>'
        '<table style="width:100%;border-collapse:collapse;font-size:14px;border:1px solid #eee">'
        '<tr style="background:#f8fafc">'
        '<th style="padding:6px;text-align:left">지수</th>'
        '<th style="padding:6px;text-align:right">현재가</th>'
        '<th style="padding:6px;text-align:right">등락률</th>'
        '</tr>' + rows +
        '</table><br>'
        '<a href="https://dalbonz.github.io/investment-news-bot" style="background:#1a73e8;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;display:inline-block">📊 대시보드 바로가기</a>'
        '<h3 style="margin-top:24px">📰 주요 뉴스</h3>' + news_html +
        '</body></html>'
    )
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '📈 ' + today + ' 투자 브리핑'
    msg['From']    = GMAIL_USER
    msg['To']      = GMAIL_USER
    msg.attach(MIMEText(html, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASSWORD)
        s.send_message(msg)
    print('이메일 전송 완료!')

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
