<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tablet Compare Pro</title>

<style>
body { font-family:-apple-system; background:#f5f5f7; text-align:center; }

h1 { margin:30px 0; }

.container {
    display:flex;
    gap:20px;
    justify-content:center;
}

.card {
    background:white;
    border-radius:20px;
    padding:15px;
    width:180px;
    box-shadow:0 10px 25px rgba(0,0,0,0.08);
}

select,input { width:100%; margin-bottom:8px; padding:6px; }

.add-btn {
    width:45px; height:45px; border-radius:50%;
    background:#0071e3; color:white; font-size:22px;
    border:none; cursor:pointer;
    align-self:center;
}

/* GO 버튼 */
.go-btn {
    margin-top:20px;
    padding:10px 30px;
    border:none;
    background:black;
    color:white;
    border-radius:10px;
    cursor:pointer;
}

/* TABLE */
.table-box {
    margin-top:40px;
    background:white;
    border-radius:20px;
    padding:20px;
}

table { width:100%; border-collapse:collapse; }

td,th { padding:10px; border-bottom:1px solid #eee; }

.category {
    background:#f0f0f0;
    font-weight:bold;
    text-align:left;
}

.good { color:#1a7f37; font-weight:bold; }
.bad { color:#d93025; font-weight:bold; }
.base { font-weight:bold; }
</style>
</head>

<body>

<h1>Tablet Compare Pro</h1>

<div class="container" id="cards"></div>

<button class="go-btn" onclick="generateTable()">GO</button>

<div class="table-box">
<table id="table"></table>
</div>

<script>
const brands = {
    Apple:["iPad Pro M4","iPad Air M2"],
    Samsung:["Galaxy Tab S10","Galaxy Tab S9"],
    Xiaomi:["Pad 7","Pad 6"]
};

let devices=[{},{},];

function renderCards(){
    const c=document.getElementById("cards");
    c.innerHTML="";

    devices.forEach((d,i)=>{
        c.innerHTML+=`
        <div class="card">
            <select onchange="setBrand(${i},this.value)">
                <option>제조사</option>
                ${Object.keys(brands).map(b=>`<option ${d.brand===b?'selected':''}>${b}</option>`).join("")}
            </select>

            <select onchange="setModel(${i},this.value)">
                <option>모델</option>
                ${(brands[d.brand]||[]).map(m=>`<option ${d.model===m?'selected':''}>${m}</option>`).join("")}
            </select>

            <input placeholder="모델 직접 입력 (검색 실패 시)" onblur="manual(${i},this.value)">
            <div>${d.model||"미선택"}</div>
        </div>`;
    });

    if(devices.length<5){
        c.innerHTML+=`<button class="add-btn" onclick="add()">+</button>`;
    }
}

function add(){ devices.push({}); renderCards(); }
function setBrand(i,v){ devices[i].brand=v; devices[i].model=""; renderCards(); }
function setModel(i,v){ devices[i].model=v; renderCards(); }
function manual(i,v){ if(v) devices[i].model=v; renderCards(); }

/* ====== 핵심: GO 버튼 ====== */
function generateTable(){

const table=document.getElementById("table");

/* 헤더 */
let html="<tr><th>항목</th>";
devices.forEach((d,i)=> html+=`<th>${d.model||"제품"+(i+1)}</th>`);
html+="</tr>";

/* 더미 데이터 (구조용) */
const data = [
["■ 기본정보"],
["출시일","2024","2023","2022"],
["가격","150","130","90"],

["■ 디스플레이"],
["크기","11","11","12"],
["주사율","120","120","144"],

["■ AP"],
["칩셋","M4","Snapdragon","Dimensity"],
["성능",100,85,70],

["■ 메모리"],
["RAM","16","12","8"]
];

data.forEach(row=>{
    if(row.length===1){
        html+=`<tr><td class="category" colspan="${devices.length+1}">${row[0]}</td></tr>`;
    }else{
        html+="<tr>";
        html+=`<td>${row[0]}</td>`;

        row.slice(1).forEach((v,i)=>{
            let cls="";
            if(row[0]==="성능"){
                if(i===0) cls="base";
                else if(v>100) cls="good";
                else if(v<100) cls="bad";
            }
            html+=`<td class="${cls}">${v}${row[0]==="성능"?"%":""}</td>`;
        });

        html+="</tr>";
    }
});

table.innerHTML=html;
}

renderCards();
</script>

</body>
</html>
