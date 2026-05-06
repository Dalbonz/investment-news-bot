# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the bot

```bash
pip install requests
export TELEGRAM_TOKEN=... TELEGRAM_CHAT_ID=... GMAIL_USER=... GMAIL_PASSWORD=...
python news_bot.py
```

`OPENAI_API_KEY` and `TELEGRAM_CHAT_ID_WIFE` are optional — the bot degrades gracefully if absent.

## Architecture

This is a two-part system connected by `data.json`:

1. **`news_bot.py`** — Python script that runs via GitHub Actions on a daily cron (`30 23 * * *` UTC = 08:30 KST). It:
   - Fetches 5-day OHLCV candles for ~35 symbols from the Yahoo Finance v8 API
   - Scrapes up to 3 articles per source from 5 Korean financial RSS feeds, filtered by `INVEST_KW` / `EXCLUDE_KW` keyword lists
   - Optionally generates a 3–4 sentence Korean market commentary using OpenAI `gpt-4o-mini`
   - Writes everything to `data.json` and commits it back to the repo
   - Sends an HTML Telegram message and Gmail email

2. **`index.html`** — Single-file static dashboard served on GitHub Pages (`https://dalbonz.github.io/investment-news-bot`). It fetches `data.json` at load time and renders market tables, candlestick charts (via `lightweight-charts@3.8.0`), and the news feed. No build step — all CSS and JS are inline.

`data.json` is the sole data contract between the bot and the frontend. The workflow has `contents: write` permission so it can `git push` the updated file.

## Key conventions

- All required secrets live in GitHub Actions secrets: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_PASSWORD`. `OPENAI_API_KEY` is optional.
- `SYMBOLS` dict in `news_bot.py` maps short keys (e.g. `'kospi'`) to Yahoo Finance ticker symbols. The same keys are used in `data.json` and referenced directly in `index.html`.
- News keyword filtering (`is_invest_news`) is purely title-based with no ML — add/remove strings from `INVEST_KW` / `EXCLUDE_KW` to tune.
- The frontend (`index.html`) has no dependency on `new_index_gpt.html`; the latter is an alternate/experimental layout.
npm install -g @anthropic-ai/claude-code

## 현재 심볼 현황
- 코스피: ^KS11, 코스닥: ^KQ11
- 추가 심볼: dow, vix, jpykrw, eurkrw, gbpkrw, cnykrw, brent, natgas, googl, naver

## RSS 카테고리
- 속보: Investing.com
- 분석: 매일경제, 파이낸셜뉴스
- 국내: 한국경제, 연합뉴스

## Secrets
- TELEGRAM_CHAT_ID_WIFE 추가됨

## 대시보드 구성
- 주식 카드: 한국/미국 탭
- 뉴스 탭: 전체/속보/분석/국내
- 상세 팝업: 8개 기간 + 기간별 변동 요약
