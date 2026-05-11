/**
 * Investment Dashboard — Google Apps Script Web App (1인용)
 *
 * 배포 방법:
 *  1. Google Sheets 열기 → 확장 프로그램 → Apps Script
 *  2. 이 파일의 내용 전체를 붙여넣기
 *  3. OWNER 와 SHEET_ID 를 수정
 *     - Bong 시트: OWNER = 'bong', SHEET_ID = 'Bong 시트 ID'
 *     - Kyoung 시트: OWNER = 'kyoung', SHEET_ID = 'Kyoung 시트 ID'
 *  4. 배포 → 새 배포 → 유형: 웹 앱
 *     - 다음 사용자로 실행: 나(Me)
 *     - 액세스 권한: 누구나(Anyone)
 *  5. 배포 후 URL을 대시보드 ⚙️ 설정에 붙여넣기
 *
 * 시트 탭 구조 (자동 생성됨):
 *  Stocks | Cash | Savings | Meta
 */

// ← 'bong' 또는 'kyoung' 으로 변경하세요
const OWNER = 'bong';

// ← 본인 Google 스프레드시트 ID로 교체하세요
// URL의 /d/ 뒤 ~ /edit 사이의 긴 문자열입니다
//   Bong   시트: 1jYVXz_rJ5CiVOWl3Rts5EPXBSgib3BCvf-TDXFegC6E
//   Kyoung 시트: 1656KHRiBCbdvvksAuuppmTy9IfyhOrblZAMMcsiVu1w
const SHEET_ID = '1jYVXz_rJ5CiVOWl3Rts5EPXBSgib3BCvf-TDXFegC6E';

// ────────────────────────────────────────────────────────────
// GET: 포트폴리오 데이터 반환
// ────────────────────────────────────────────────────────────
function doGet(_e) {
  try {
    const ss = SpreadsheetApp.openById(SHEET_ID);
    return jsonResponse(readOwner(ss));
  } catch (err) {
    return jsonResponse({ error: err.toString() });
  }
}

// ────────────────────────────────────────────────────────────
// POST: 포트폴리오 저장 (stocks, cash, savings)
// ────────────────────────────────────────────────────────────
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.openById(SHEET_ID);

    if (data.stocks !== undefined)
      writeSheet(ss, 'Stocks',  HEADERS.stocks,  data.stocks);
    if (data.cash !== undefined)
      writeSheet(ss, 'Cash',    HEADERS.cash,    data.cash);
    if (data.savings !== undefined)
      writeSheet(ss, 'Savings', HEADERS.savings, data.savings);

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
// 헬퍼: 데이터 읽기
// ────────────────────────────────────────────────────────────
function readOwner(ss) {
  const stocks  = readSheet(ss, 'Stocks',  HEADERS.stocks);
  const cash    = readSheet(ss, 'Cash',    HEADERS.cash);
  const savings = readSheet(ss, 'Savings', HEADERS.savings);
  const meta    = readSheet(ss, 'Meta', ['key', 'value']);
  const realized = Number(
    (meta.find(r => r.key === OWNER + '_realized_pnl_2025') || {}).value || 0
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
      ['qty', 'avg_price', 'amount', 'rate_pct', 'maturity_amount'].forEach(f => {
        if (obj[f] !== undefined && obj[f] !== '') obj[f] = Number(obj[f]);
      });
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
