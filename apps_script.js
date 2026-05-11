/**
 * Investment Dashboard — Google Apps Script Web App
 *
 * 배포 방법:
 *  1. Google Sheets 열기 → 확장 프로그램 → Apps Script
 *  2. 이 파일의 내용 전체를 붙여넣기
 *  3. SHEET_ID 를 본인 스프레드시트 ID로 교체
 *  4. 배포 → 새 배포 → 유형: 웹 앱
 *     - 다음 사용자로 실행: 나(Me)
 *     - 액세스 권한: 누구나(Anyone)
 *  5. 배포 후 URL을 대시보드 ⚙️ 설정에 붙여넣기
 *
 * 시트 구조 (자동 생성됨):
 *  Bong_Stocks   | Bong_Cash   | Bong_Savings
 *  Kyoung_Stocks | Kyoung_Cash | Kyoung_Savings
 *  Meta          (realized_pnl 등 메타 값)
 */

// ← 여기를 본인 Google 스프레드시트 ID로 교체하세요
// URL의 /d/ 뒤 ~ /edit 사이의 긴 문자열입니다
const SHEET_ID = 'YOUR_SPREADSHEET_ID_HERE';

// ────────────────────────────────────────────────────────────
// GET: 전체 포트폴리오 데이터 반환
// ────────────────────────────────────────────────────────────
function doGet(e) {
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    const result = {
      bong:   readOwner(ss, 'Bong'),
      kyoung: readOwner(ss, 'Kyoung'),
    };
    return jsonResponse(result);
  } catch (err) {
    return jsonResponse({ error: err.toString() });
  }
}

// ────────────────────────────────────────────────────────────
// POST: 오너의 포트폴리오 저장 (owner, stocks, cash, savings)
// ────────────────────────────────────────────────────────────
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const owner = data.owner; // 'bong' | 'kyoung'
    if (!owner || owner === 'total') throw new Error('Invalid owner');

    const prefix = owner.charAt(0).toUpperCase() + owner.slice(1); // 'Bong' | 'Kyoung'
    const ss = SpreadsheetApp.openById(SHEET_ID);

    if (data.stocks !== undefined)
      writeSheet(ss, prefix + '_Stocks', HEADERS.stocks, data.stocks);
    if (data.cash !== undefined)
      writeSheet(ss, prefix + '_Cash', HEADERS.cash, data.cash);
    if (data.savings !== undefined)
      writeSheet(ss, prefix + '_Savings', HEADERS.savings, data.savings);

    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ error: err.toString() });
  }
}

// ────────────────────────────────────────────────────────────
// 헤더 정의
// ────────────────────────────────────────────────────────────
const HEADERS = {
  stocks:  ['name', 'symbol', 'market', 'qty', 'avg_price', 'currency', 'locked'],
  cash:    ['bank', 'currency', 'amount'],
  savings: ['type', 'bank', 'maturity', 'rate_pct', 'maturity_amount', 'currency'],
};

// ────────────────────────────────────────────────────────────
// 헬퍼: 오너 데이터 읽기
// ────────────────────────────────────────────────────────────
function readOwner(ss, prefix) {
  const stocks  = readSheet(ss, prefix + '_Stocks',  HEADERS.stocks);
  const cash    = readSheet(ss, prefix + '_Cash',    HEADERS.cash);
  const savings = readSheet(ss, prefix + '_Savings', HEADERS.savings);
  const meta    = readSheet(ss, 'Meta', ['key', 'value']);
  const realized = Number(
    (meta.find(r => r.key === prefix.toLowerCase() + '_realized_pnl_2025') || {}).value || 0
  );
  return { stocks, cash, savings, realized_pnl_2025_krw: realized };
}

// ────────────────────────────────────────────────────────────
// 헬퍼: 시트 읽기 → 오브젝트 배열
// ────────────────────────────────────────────────────────────
function readSheet(ss, sheetName, headers) {
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) return [];
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return [];
  return data.slice(1)
    .filter(row => row[0] !== '' && row[0] !== null)
    .map(row => {
      const obj = {};
      headers.forEach((h, i) => { obj[h] = row[i] !== undefined ? row[i] : ''; });
      // 숫자 필드 변환
      ['qty', 'avg_price', 'amount', 'rate_pct', 'maturity_amount'].forEach(f => {
        if (obj[f] !== undefined && obj[f] !== '') obj[f] = Number(obj[f]);
      });
      // boolean 변환
      if (obj.locked !== undefined)
        obj.locked = obj.locked === true || obj.locked === 'TRUE' || obj.locked === 1;
      return obj;
    });
}

// ────────────────────────────────────────────────────────────
// 헬퍼: 시트 쓰기 (전체 덮어쓰기)
// ────────────────────────────────────────────────────────────
function writeSheet(ss, sheetName, headers, rows) {
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) sheet = ss.insertSheet(sheetName);
  sheet.clearContents();
  sheet.appendRow(headers);
  rows.forEach(row => {
    sheet.appendRow(headers.map(h => row[h] !== undefined ? row[h] : ''));
  });
}

// ────────────────────────────────────────────────────────────
// 헬퍼: JSON 응답 생성
// ────────────────────────────────────────────────────────────
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
