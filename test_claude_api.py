#!/usr/bin/env python3
"""
Claude API 연결 테스트 스크립트
로컬에서 실행: ANTHROPIC_API_KEY=sk-ant-... python test_claude_api.py
"""
import os
import requests

API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY 환경변수가 없습니다.")
    print("  export ANTHROPIC_API_KEY=sk-ant-...")
    exit(1)

key_hint = API_KEY[:8] + '...' + API_KEY[-4:] + f' (len={len(API_KEY)})'
print(f"[1] API 키 확인: {key_hint}")

res = requests.post(
    'https://api.anthropic.com/v1/messages',
    headers={
        'x-api-key':        API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type':     'application/json',
    },
    json={
        'model':    'claude-haiku-4-5',
        'max_tokens': 50,
        'messages': [{'role': 'user', 'content': '안녕하세요. 한 문장으로 답하세요.'}],
    },
    timeout=30,
)

org_id = res.headers.get('anthropic-organization-id', 'N/A')
print(f"[2] HTTP 상태: {res.status_code}")
print(f"[3] Org ID: {org_id}")

body = res.json()
if res.status_code == 200:
    text = body['content'][0]['text']
    print(f"[4] 성공! 응답: {text}")
else:
    err = body.get('error', {})
    print(f"[4] 오류 타입: {err.get('type')}")
    print(f"[5] 오류 메시지: {err.get('message')}")
    print()
    print("==== 진단 ====")
    print(f"위 Org ID({org_id})가 console.anthropic.com의 조직 ID와 일치하는지 확인하세요.")
    print("console.anthropic.com → Settings → Organization → Organization ID")
