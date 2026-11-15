import {inspect} from './model.mjs';
const $=id=>document.getElementById(id);
const fmt=(x,d=1)=>(100*x).toFixed(d)+'%';
const num=x=>x.toLocaleString('en-US');
const page=document.body.dataset.page;
const metricNames={league:'聯盟平均',raw_jeffreys:'歷史對戰比例（0.5 平滑）',league_shrink:'對戰向聯盟平均收縮',player_context:'投打者組合基準',matchup_shrink:'投打者基準 + 對戰收縮'};
const legacyRoutes={matchup:'/query/',validation:'/results/',about:'/data/'};
if(page==='home' && legacyRoutes[location.hash.slice(1)]){
 location.replace(legacyRoutes[location.hash.slice(1)]+location.search);
}
let data,current,revealed=false;
function setText(id,value){const el=$(id);if(el)el.textContent=value;}
function setHTML(id,value){const el=$(id);if(el)el.innerHTML=value;}
function announce(message){const el=$('query-status');if(el){el.textContent=message;el.hidden=!message;}}
function updateShareUrl(){
 const url=new URL('/query/',location.origin);
 url.searchParams.set('pitcher',$('pitcher').value);
 url.searchParams.set('batter',$('batter').value);
 history.replaceState(null,'',url);
 if($('share-link'))$('share-link').value=url.href;
}
async function shareQuery(){
 try{
  await navigator.clipboard.writeText(location.href);
  $('share-link').hidden=true;
  announce('查詢連結已複製，可分享目前的投打組合。');
 }catch{
  const field=$('share-link');field.hidden=false;field.value=location.href;field.focus();field.select();
  announce('請複製下方查詢網址。');
 }
}
function fillSummary(){
 const s=data.summary;
 setText('train-count',num(s.train_pa)+' 打席');
 setText('validation-count',num(s.validation_pa)+' 打席');
 setText('test-count',num(s.test_pa)+' 打席');
 setText('unseen-percent',fmt(s.sparse_test.unseen.pa/s.test_pa));
 setText('home-games',num(Object.values(s.audit).reduce((n,a)=>n+a.games,0)));
 setText('home-pa',num(Object.values(s.audit).reduce((n,a)=>n+a.eligible_pa,0)));
 setHTML('metrics-table',Object.entries(s.metrics).map(([k,v])=>'<tr class="'+(k==='matchup_shrink'?'highlight':'')+'"><td>'+metricNames[k]+'</td><td>'+v.brier.toFixed(6)+'</td><td>'+v.log_loss.toFixed(6)+'</td></tr>').join(''));
 const d=s.delta_brier.player_context,dl=s.delta_brier.league;
 setHTML('main-finding','<strong>結果判讀</strong>相較聯盟平均，收縮模型的 Brier 差為 '+dl.delta_brier.toFixed(6)+'，95% 區間 ['+dl.ci95.map(x=>x.toFixed(6)).join(', ')+']。相較投打者組合基準，差為 '+d.delta_brier.toFixed(6)+'，95% 區間 ['+d.ci95.map(x=>x.toFixed(6)).join(', ')+']，包含零；目前未觀察到加入對戰資料後的穩定額外改善。');
 const labels={unseen:'0 打席（未見對戰）','1_5':'1–5 打席','6_15':'6–15 打席','16_plus':'16 打席以上'};
 setHTML('sparse-table',Object.entries(s.sparse_test).map(([k,v])=>'<tr><td>'+labels[k]+'</td><td>'+num(v.pa)+'</td><td>'+v.brier.raw_jeffreys.toFixed(6)+'</td><td>'+v.brier.matchup_shrink.toFixed(6)+'</td></tr>').join(''));
 setHTML('audit-table',Object.entries(s.audit).map(([k,v])=>'<tr><td>'+k+'</td><td>'+v.games+'</td><td>'+num(v.eligible_pa)+'</td><td>'+num(v.strikeouts)+'</td><td>'+num(v.all_records-v.eligible_pa)+'</td></tr>').join(''));
 setText('parameter-description','2024 後段選定：球員整體比例的基準相當打席數 '+s.parameters.strength+'；對戰模型的基準相當打席數 '+s.parameters.m+'。對戰直接權重 = 對戰樣本數 /（對戰樣本數 + '+s.parameters.m+'）。超參數只用 2024 年選定，2025 僅評估。');
}
function rateHTML(x){return x===null?'—':(100*x).toFixed(1)+'<small>%</small>';}
function render(){
 current=inspect(data,$('batter').value,$('pitcher').value);const r=current;
 $('pitcher-name').textContent=r.p.name;$('batter-name').textContent=r.b.name;
 $('evidence-badge').textContent=r.n===0?'2024 無同組對戰':r.n<20?'歷史樣本較少':'2024 歷史紀錄';
 $('sample-pa').textContent=num(r.n);$('strikeouts').textContent=num(r.k);$('raw-rate').innerHTML=rateHTML(r.raw);
 $('estimate').innerHTML=rateHTML(r.estimate);$('estimate-detail').textContent=`投打者組合基準：${fmt(r.p0)}`;
 $('weight').innerHTML=rateHTML(r.weight);$('weight-detail').textContent=`基準資料權重：${fmt(1-r.weight)}`;
 const iv=r.interval;$('interval-description').innerHTML=iv?`只有 <strong>${r.n} 個打席</strong>，歷史三振比例的 90% 區間為 <strong>${fmt(iv[0])} – ${fmt(iv[1])}</strong>。`:'沒有同組對戰樣本，無法估計其歷史比例區間；目前顯示Player Baseline。';
 $('raw-dot').hidden=!iv;$('interval-segment').hidden=!iv;
 if(iv){$('interval-segment').style.left=fmt(iv[0],4);$('interval-segment').style.width=fmt(iv[1]-iv[0],4);$('raw-dot').style.left=fmt(r.raw,4);}
 $('estimate-dot').style.left=fmt(r.estimate,4);
 $('pitcher-rate').textContent=r.p.n?`${fmt(r.p.k/r.p.n)} / ${num(r.p.n)} 打席`:'2024 無資料';
 $('batter-rate').textContent=r.b.n?`${fmt(r.b.k/r.b.n)} / ${num(r.b.n)} 打席`:'2024 無資料';
 $('context-rate').textContent=fmt(r.p0);
 $('scouting-note').textContent=!r.n?'2024 無同組對戰紀錄，估計值取自投打者整體資料。歷史三振率以「—」表示，不計為 0%。':`這組對戰共 ${r.n} 個有效打席、${r.k} 次三振。對戰資料占估計值 ${fmt(r.weight)}，其餘參考Player Baseline；樣本量與計算方式應一併考量。`;
 revealed=false;setHoldout();updateShareUrl();
}
function setHoldout(){const r=current;$('holdout-result').hidden=!revealed;$('reveal').setAttribute('aria-expanded',String(revealed));$('reveal').textContent=revealed?'收起 2025 結果':'顯示 2025 對戰結果';$('holdout-result').innerHTML=r.tn?`<strong>${fmt(r.tk/r.tn)}</strong>${r.tk} 次三振 / ${r.tn} 打席`:'2025 無同組有效對戰';}
function exportCard(){const r=current,s=data.summary;let text=`Matchup Lens｜歷史情蒐卡\n投手：${r.p.name}\n打者：${r.b.name}\n快照：2025-01-01；僅使用 2024 例行賽資料\n\n對戰樣本：${r.n} 打席，${r.k} 三振\n歷史三振比例：${r.raw===null?'無樣本':fmt(r.raw)}\nWilson 90% 歷史比例區間：${r.interval?r.interval.map(x=>fmt(x)).join('–'):'無法估計'}\n投打者組合基準：${fmt(r.p0)}\n收縮後三振估計：${fmt(r.estimate)}\n對戰資料直接權重：${fmt(r.weight)}\n\n判讀：${$('scouting-note').textContent}\n`;
 if(revealed)text+=`\n2025 獨立結果：${r.tn} 打席，${r.tk} 三振${r.tn?'，'+fmt(r.tk/r.tn):''}\n`;
 text+=`\n方法：Player Baseline排除此組對戰，m=${s.parameters.m}；參數由 2024 時間切分選定。\n本卡僅分析三振，非最佳代打或換投建議。區間不包含跨年能力漂移。\n來源：Rebas Open Data，ODC-By 1.0\nhttps://github.com/rebas-tw/rebas.tw-open-data\n`;
 const a=document.createElement('a'),url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/plain;charset=utf-8'}));a.href=url;a.download=`Matchup_Lens_${r.p.name}_${r.b.name}.txt`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function initialize(){
 try{
  const response=await fetch(new URL('./data.json',import.meta.url));
  if(!response.ok)throw new Error('Data could not be loaded');
  data=await response.json();fillSummary();
  if($('pitcher') && $('batter')){
   for(const [id,key] of [['pitcher','pitchers'],['batter','batters']]){
    const select=$(id);select.replaceChildren();
    for(const player of Object.values(data[key]).sort((a,b)=>a.name.localeCompare(b.name,'zh-Hant'))){
     const option=document.createElement('option');option.value=player.id;option.textContent=player.name+' · '+player.team;select.append(option);
    }
   }
   const defaults=data.summary.examples[0].split('|');
   const params=new URLSearchParams(location.search);
   const requestedPitcher=params.get('pitcher'),requestedBatter=params.get('batter');
   $('pitcher').value=Object.hasOwn(data.pitchers,requestedPitcher)?requestedPitcher:defaults[1];
   $('batter').value=Object.hasOwn(data.batters,requestedBatter)?requestedBatter:defaults[0];
   if(page==='matchup'){
    for(const id of ['pitcher','batter'])$(id).addEventListener('change',()=>{announce('');if($('share-link'))$('share-link').hidden=true;render();});
    for(const key of data.summary.examples){
     const [b,p]=key.split('|');const button=document.createElement('button');
     button.type='button';button.textContent=data.pitchers[p].name+'／'+data.batters[b].name;
     button.addEventListener('click',()=>{$('batter').value=b;$('pitcher').value=p;announce('');render();});
     $('examples').append(button);
    }
    $('reveal').addEventListener('click',()=>{revealed=!revealed;setHoldout();});
    $('export').addEventListener('click',exportCard);
    $('share').addEventListener('click',shareQuery);
    render();
    if((requestedPitcher&&!Object.hasOwn(data.pitchers,requestedPitcher))||(requestedBatter&&!Object.hasOwn(data.batters,requestedBatter))){
     announce('查詢連結中的球員未在資料名單內，已顯示預設範例。');
    }
   }else if($('quick-submit')){
    $('quick-submit').disabled=false;
   }
  }
  if($('loading'))$('loading').hidden=true;
  const section=$(page);if(section)section.hidden=false;
 }catch(error){
  const notice=$('loading');if(notice){notice.hidden=false;notice.textContent='目前無法讀取資料，請重新整理頁面。資料來源與操作方式可由「使用說明」查閱。';notice.classList.add('load-error');}
  console.error(error);
 }
}
initialize();

// Comparison board and frozen out-of-time calibration diagnostics.
async function extendedPages(){
 if(page!=='compare'&&page!=='validation')return;
 try{
  if(page==='validation'){
   const response=await fetch('/calibration.json');if(!response.ok)throw Error('Calibration unavailable');const cal=await response.json();
   const renderCal=()=>{const m=cal.models[$('cal-model').value];$('cal-summary').textContent=`2025 測試 ${num(cal.test_pa)} 打席；分組平均絕對差 ECE：${(m.ece*100).toFixed(2)} 個百分點。`;$('cal-rows').replaceChildren();for(const b of m.bins){let tr=document.createElement('tr');for(const v of [`${fmt(b.lo,0)}–${fmt(b.hi,0)}`,num(b.n),fmt(b.predicted),fmt(b.observed),((b.observed-b.predicted)*100).toFixed(2)+' pp']){let td=document.createElement('td');td.textContent=v;tr.append(td)}$('cal-rows').append(tr)}};$('cal-model').addEventListener('change',renderCal);renderCal();return;
  }
  const response=await fetch('/data.json');if(!response.ok)throw Error('Data unavailable');const d=await response.json();let chosen=[];
  const fill=(el,items)=>{el.replaceChildren();for(const [id,name]of items)el.add(new Option(name,id))};
  fill($('board-pitcher'),Object.values(d.pitchers).sort((a,b)=>b.n-a.n).map(p=>[p.id,p.name+' · '+p.team]));
  const teams=[...new Set(Object.values(d.batters).map(p=>p.team))].sort();fill($('board-team'),teams.map(t=>[t,t]));
  function options(){fill($('board-player'),Object.values(d.batters).filter(b=>b.team===$('board-team').value).sort((a,b)=>b.n-a.n).map(b=>[b.id,b.name+' · 2024 '+b.n+' PA']))}
  function renderBoard(){let rows=$('board-rows');rows.replaceChildren();for(const bid of chosen){const r=inspect(d,bid,$('board-pitcher').value);let tr=document.createElement('tr');for(const v of [r.b.name,`${r.k} / ${r.n}`,r.raw===null?'—':fmt(r.raw),fmt(r.p0),fmt(r.estimate),fmt(r.weight),!r.b.n||!r.p.n?'球員資料不足':r.n?'歷史樣本 '+r.n+' PA':'無同組對戰']){let td=document.createElement('td');td.textContent=v;tr.append(td)}let td=document.createElement('td'),a=document.createElement('a');a.href='/query/?pitcher='+encodeURIComponent($('board-pitcher').value)+'&batter='+encodeURIComponent(bid);a.textContent='詳情';let btn=document.createElement('button');btn.className='button';btn.textContent='移除';btn.onclick=()=>{chosen=chosen.filter(x=>x!==bid);renderBoard()};td.append(a,document.createTextNode(' '),btn);tr.append(td);rows.append(tr)}$('board-status').textContent=`已選 ${chosen.length} / 9 名打者。`;$('download-board').disabled=!chosen.length;}
  $('board-team').onchange=options;$('board-pitcher').onchange=renderBoard;$('add-board').onclick=()=>{const bid=$('board-player').value;if(chosen.includes(bid)){$('board-status').textContent='這位打者已在比較表內。';return}if(chosen.length>=9){$('board-status').textContent='最多比較九名打者，請先移除一位。';return}chosen.push(bid);renderBoard()};$('clear-board').onclick=()=>{chosen=[];renderBoard()};
  $('download-board').onclick=()=>{const quote=v=>'"'+String(v).replaceAll('"','""')+'"',lines=[['pitcher','batter','reference_year','PA','K','raw_K_rate','player_baseline','estimate','matchup_weight','source']];for(const bid of chosen){const r=inspect(d,bid,$('board-pitcher').value);lines.push([r.p.name,r.b.name,2024,r.n,r.k,r.raw??'',r.p0,r.estimate,r.weight,'Rebas Open Data / ODC-By 1.0 / https://github.com/rebas-tw/rebas.tw-open-data'])}const u=URL.createObjectURL(new Blob(['\ufeff'+lines.map(l=>l.map(quote).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=u;a.download='Matchup_Lens_comparison.csv';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};
  options();chosen=Object.values(d.batters).filter(b=>b.team===$('board-team').value).sort((a,b)=>b.n-a.n).slice(0,3).map(b=>b.id);renderBoard();
 }catch(e){const el=$('board-status')||$('cal-summary');if(el)el.textContent='比較資料載入失敗，請重新整理。';console.error(e)}
}
extendedPages();
