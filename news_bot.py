import os, json, smtplib, requests, xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

TELEGRAM_TOKEN      = os.environ['TELEGRAM_TOKEN']
TELEGRAM_CHAT_ID    = os.environ['TELEGRAM_CHAT_ID']
TELEGRAM_CHAT_ID_WIFE = os.environ.get('TELEGRAM_CHAT_ID_WIFE', '')
GMAIL_USER          = os.environ['GMAIL_USER']
GMAIL_PASSWORD      = os.environ['GMAIL_PASSWORD']
ANTHROPIC_API_KEY   = os.environ.get('ANTHROPIC_API_KEY', '')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

SYMBOLS = {
    'kospi':   '^KS11',      'kosdaq':  '^KQ11',
    'nasdaq':  '^IXIC',      'sp500':   '^GSPC',
    'dow':     '^DJI',       'ndx':     '^NDX',
    'vix':     '^VIX',       'nikkei':  '^N225',
    'usdkrw':  'USDKRW=X',  'jpykrw':  'JPYKRW=X',
    'eurkrw':  'EURKRW=X',  'gbpkrw':  'GBPKRW=X',
    'cnykrw':  'CNYKRW=X',  'usdjpy':  'USDJPY=X',
    'eurusd':  'EURUSD=X',  'dxy':     'DX-Y.NYB',
    'oil':     'CL=F',       'brent':   'BZ=F',
    'natgas':  'NG=F',       'gold':    'GC=F',
    'silver':  'SI=F',       'copper':  'HG=F',
    'aapl':    'AAPL',       'nvda':    'NVDA',
    'tsla':    'TSLA',       'msft':    'MSFT',
    'googl':   'GOOGL',
    'spy':     'SPY',        'qqq':     'QQQ',
    'eem':     'EEM',        'efa':     'EFA',
    'gdx':     'GDX',        'uso':     'USO',
    'samsung': '005930.KS',  'hynix':   '000660.KS',
    'hanwha':  '012450.KS',  'hyundai': '005380.KS',
    'naver':   '035420.KS',
}

RSS_SOURCES = [
    {'name': '매일경제',     'url': 'https://www.mk.co.kr/rss/30100041/',           'category': '분석'},
    {'name': '파이낸셜뉴스', 'url': 'https://www.fnnews.com/rss/fn_stock_news.xml', 'category': '분석'},
    {'name': 'Investing.com','url': 'https://kr.investing.com/rss/news.rss',         'category': '속보'},
    {'name': '한국경제',     'url': 'https://www.hankyung.com/feed/all-news',        'category': '국내'},
    {'name': '연합뉴스',     'url': 'https://www.yna.co.kr/rss/economy.xml',         'category': '국내'},
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
            if key in ('kospi', 'kosdaq'):
                print('>>> ' + key + ' 실제값: ' + str(price))
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
                all_news.append({
                    'source':   source['name'],
                    'category': source['category'],
                    'title':    title,
                    'link':     link,
                })
                cnt += 1
            print(source['name'] + ': ' + str(cnt) + '개')
        except Exception as e:
            print(source['name'] + ' 오류: ' + str(e))
    return all_news

_FALLBACK_COMMENT = {
    'kr':   '한국 시황 분석을 불러오지 못했어요.',
    'us':   '미국 시황 분석을 불러오지 못했어요.',
    'tips': '투자 포인트를 불러오지 못했어요.',
}

def get_ai_comment(market):
    if not ANTHROPIC_API_KEY:
        return dict(_FALLBACK_COMMENT)

    kr_rows, us_rows, other_rows = [], [], []
    for k, label in [('kospi','코스피'),('kosdaq','코스닥'),('usdkrw','달러/원'),('jpykrw','엔/원'),('eurkrw','유로/원')]:
        if k in market:
            m = market[k]
            kr_rows.append(label + ': ' + str(m['price']) + ' (' + ('+' if m['pct']>=0 else '') + str(m['pct']) + '%)')
    for k, label in [('nasdaq','나스닥'),('sp500','S&P500'),('dow','다우'),('nvda','엔비디아'),('aapl','애플'),('msft','마이크로소프트'),('tsla','테슬라'),('googl','구글')]:
        if k in market:
            m = market[k]
            us_rows.append(label + ': ' + str(m['price']) + ' (' + ('+' if m['pct']>=0 else '') + str(m['pct']) + '%)')
    for k, label in [('oil','WTI유가'),('gold','금'),('vix','VIX'),('silver','은')]:
        if k in market:
            m = market[k]
            other_rows.append(label + ': ' + str(m['price']) + ' (' + ('+' if m['pct']>=0 else '') + str(m['pct']) + '%)')

    prompt = (
        '당신은 전문 증권 애널리스트입니다. 아래 시장 데이터를 바탕으로 투자자를 위한 시황 분석을 한국어로 작성하세요.\n\n'
        '한국 시장:\n' + '\n'.join(kr_rows) + '\n\n'
        '미국 시장:\n' + '\n'.join(us_rows) + '\n\n'
        '기타(원자재/변동성):\n' + '\n'.join(other_rows) + '\n\n'
        '아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):\n'
        '{\n'
        '  "kr": "🇰🇷 한국 시황: [코스피/코스닥/환율 중심 2~3문장]",\n'
        '  "us": "🇺🇸 미국 시황: [나스닥/S&P500/빅테크 중심 2~3문장]",\n'
        '  "tips": "💡 오늘의 투자 포인트: [주목 섹터/종목 2~3문장]"\n'
        '}'
    )

    key_hint = ANTHROPIC_API_KEY[:8] + '...' + ANTHROPIC_API_KEY[-4:] if len(ANTHROPIC_API_KEY) > 12 else '(short key?)'
    print('ANTHROPIC_API_KEY hint: ' + key_hint + ' (len=' + str(len(ANTHROPIC_API_KEY)) + ')')

    raw = ''
    try:
        res = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key':          ANTHROPIC_API_KEY,
                'anthropic-version':   '2023-06-01',
                'content-type':        'application/json',
            },
            json={
                'model':      'claude-haiku-4-5',
                'max_tokens': 800,
                'messages':   [{'role': 'user', 'content': prompt}],
            },
            timeout=30,
        )
        print('Claude 응답 status: ' + str(res.status_code))
        print('Claude 응답 헤더: ' + str(dict(res.headers)))
        result = res.json()
        print('Claude 응답 body: ' + str(result)[:500])

        if res.status_code != 200:
            err      = result.get('error', {})
            err_type = err.get('type', '').lower()
            err_msg  = err.get('message', '').lower()
            if any(w in err_type + err_msg for w in ('credit', 'billing', 'quota', 'balance')):
                return {
                    'kr':   '⚠️ API 크레딧 부족으로 한국 시황 분석을 생성하지 못했습니다.',
                    'us':   '⚠️ API 크레딧 부족으로 미국 시황 분석을 생성하지 못했습니다.',
                    'tips': '💳 Anthropic Console(console.anthropic.com)에서 크레딧을 충전하면 AI 시황 분석이 재개됩니다.',
                }
            return dict(_FALLBACK_COMMENT)

        raw = result['content'][0]['text'].strip()
        # strip markdown code fence if present
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        parsed = json.loads(raw)
        return {
            'kr':   parsed.get('kr',   ''),
            'us':   parsed.get('us',   ''),
            'tips': parsed.get('tips', ''),
        }

    except json.JSONDecodeError as e:
        print('JSON 파싱 오류: ' + str(e) + ' / raw: ' + raw[:300])
        return dict(_FALLBACK_COMMENT)
    except Exception as e:
        print('AI 코멘트 오류: ' + str(e))
        return dict(_FALLBACK_COMMENT)

def get_portfolio_data(market):
    try:
        with open('portfolio.json', 'r', encoding='utf-8') as f:
            pf = json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print('portfolio.json 오류: ' + str(e))
        return None

    usdkrw = market.get('usdkrw', {}).get('price', 1300.0)
    sym_to_key = {v: k for k, v in SYMBOLS.items()}

    holdings_out = []
    total_cost_krw = 0.0
    total_value_krw = 0.0

    for h in pf.get('holdings', []):
        symbol     = h['symbol']
        qty        = h['qty']
        avg_price  = h['avg_price']
        currency   = h.get('currency', 'KRW')
        name       = h['name']

        # 이미 fetch된 시장 데이터에서 현재가 조회
        current_price = None
        mkey = sym_to_key.get(symbol)
        if mkey and mkey in market:
            current_price = market[mkey]['price']

        # 없으면 직접 fetch
        if current_price is None:
            try:
                url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + symbol + '?interval=1d&range=1d'
                res = requests.get(url, headers=HEADERS, timeout=10)
                res.raise_for_status()
                current_price = res.json()['chart']['result'][0]['meta']['regularMarketPrice']
                print(name + ' 포트폴리오 가격: ' + str(current_price))
            except Exception as e:
                print(name + ' 가격 오류: ' + str(e))
                current_price = avg_price

        rate           = usdkrw if currency == 'USD' else 1.0
        avg_price_krw  = avg_price * rate
        curr_price_krw = current_price * rate
        cost_krw       = avg_price_krw * qty
        value_krw      = curr_price_krw * qty
        pnl_krw        = value_krw - cost_krw
        pnl_pct        = pnl_krw / cost_krw * 100 if cost_krw else 0

        total_cost_krw  += cost_krw
        total_value_krw += value_krw

        holdings_out.append({
            'name':              name,
            'symbol':            symbol,
            'qty':               qty,
            'avg_price':         round(avg_price, 4),
            'currency':          currency,
            'current_price':     round(current_price, 4),
            'current_price_krw': round(curr_price_krw, 2),
            'value_krw':         round(value_krw, 2),
            'cost_krw':          round(cost_krw, 2),
            'pnl_krw':           round(pnl_krw, 2),
            'pnl_pct':           round(pnl_pct, 2),
        })

    total_pnl_krw = total_value_krw - total_cost_krw
    total_pnl_pct = total_pnl_krw / total_cost_krw * 100 if total_cost_krw else 0

    print('포트폴리오 완료: 평가 ' + str(round(total_value_krw)) + 'KRW')
    return {
        'holdings':        holdings_out,
        'total_cost_krw':  round(total_cost_krw, 2),
        'total_value_krw': round(total_value_krw, 2),
        'total_pnl_krw':   round(total_pnl_krw, 2),
        'total_pnl_pct':   round(total_pnl_pct, 2),
        'usdkrw':          round(usdkrw, 2),
    }

def save_data_json(market, news, ai_comment, portfolio=None):
    data = {
        'updated':    datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'market':     market,
        'news':       news,
        'ai_comment': ai_comment,
    }
    if portfolio:
        data['portfolio'] = portfolio
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('data.json 저장 완료!')

def build_telegram_msg(market, news, ai_comment):
    today = datetime.now().strftime('%Y년 %m월 %d일')
    msg = '📈 <b>' + today + ' 투자 브리핑</b>\n\n'
    msg += '🤖 <b>AI 시황 분석</b>\n'
    if isinstance(ai_comment, dict):
        msg += ai_comment.get('kr',   '') + '\n\n'
        msg += ai_comment.get('us',   '') + '\n\n'
        msg += ai_comment.get('tips', '') + '\n\n'
    else:
        msg += str(ai_comment) + '\n\n'
    msg += '📊 <b>주요 증시</b>\n'
    for k, label in [('kospi','코스피'),('kosdaq','코스닥'),('nasdaq','나스닥'),('sp500','S&P500')]:
        if k in market:
            m = market[k]
            arrow = '🔺' if m['change'] >= 0 else '🔻'
            msg += label + ': ' + '{:,.2f}'.format(m['price']) + ' ' + arrow + ' (' + ('+' if m['pct']>=0 else '') + '{:.2f}'.format(m['pct']) + '%)\n'
    msg += '\n💱 <b>환율</b>\n'
    for k, label in [('usdkrw','달러/원'),('jpykrw','엔/원'),('eurkrw','유로/원')]:
        if k in market:
            m = market[k]
            arrow = '🔺' if m['change'] >= 0 else '🔻'
            msg += label + ': ' + '{:,.2f}'.format(m['price']) + ' ' + arrow + ' (' + ('+' if m['pct']>=0 else '') + '{:.2f}'.format(m['pct']) + '%)\n'
    msg += '\n🛢 <b>원자재</b>\n'
    for k, label in [('oil','WTI'),('brent','브렌트유'),('gold','금'),('silver','은')]:
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
    return msg

def send_telegram(market, news, ai_comment):
    msg = build_telegram_msg(market, news, ai_comment)
    # 본인 발송
    res = requests.post(
        'https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage',
        data={'chat_id': TELEGRAM_CHAT_ID, 'text': msg, 'parse_mode': 'HTML'},
        timeout=15
    )
    print('텔레그램(본인) 응답: ' + str(res.status_code))
    # 와이프 발송
    if TELEGRAM_CHAT_ID_WIFE:
        res2 = requests.post(
            'https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/sendMessage',
            data={'chat_id': TELEGRAM_CHAT_ID_WIFE, 'text': msg, 'parse_mode': 'HTML'},
            timeout=15
        )
        print('텔레그램(와이프) 응답: ' + str(res2.status_code))

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
    if isinstance(ai_comment, dict):
        ai_html = (
            '<div style="margin-bottom:10px">' + ai_comment.get('kr',   '') + '</div>'
            '<div style="margin-bottom:10px">' + ai_comment.get('us',   '') + '</div>'
            '<div>'                             + ai_comment.get('tips', '') + '</div>'
        )
    else:
        ai_html = str(ai_comment)
    html = (
        '<html><body style="font-family:Arial;max-width:640px;margin:0 auto;padding:20px;color:#222">'
        '<h2 style="border-bottom:2px solid #1a73e8;padding-bottom:8px">📈 ' + today + ' 투자 브리핑</h2>'
        '<div style="background:#f0f7ff;padding:15px;border-radius:10px;margin:16px 0;line-height:1.8">'
        '<b>🤖 AI 시황 분석</b><br><br>' + ai_html +
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
    portfolio  = get_portfolio_data(market)
    save_data_json(market, news, ai_comment, portfolio)
    send_telegram(market, news, ai_comment)
    send_email(market, news, ai_comment)
    print('완료!')

if __name__ == '__main__':
    main()
