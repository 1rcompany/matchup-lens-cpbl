"""Build the static, independently addressable website pages (stdlib only)."""
from pathlib import Path
import html, json

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'site'
DIST=ROOT/'dist'
ORIGIN='https://matchup-lens-cpbl-anson.rosycoin67.chatgpt.site'
PAGES=[
 ('home','/','首頁','Matchup Lens｜CPBL Scouting','查詢中華職棒歷史投打對戰、樣本數、三振比例與估計區間，並閱讀Out-of-Time Validation與資料方法。'),
 ('matchup','/query/','Matchup','Matchup｜Matchup Lens','查詢 2024 中職投打對戰，並列三振次數、歷史比例、Wilson 區間與收縮估計。'),
 ('pitch','/pitch/','Pitch Scout','Pitch Scout｜Matchup Lens','以真實逐球資料比較配球傾向、打者球種揮空與時間外驗證。'),
 ('compare','/compare/','Compare','多人對戰比較｜Matchup Lens','固定投手，比較最多九名打者的歷史三振、Player Baseline與對戰權重。'),
 ('validation','/results/','Validation','模型回測結果｜Matchup Lens','以 2025 中職獨立賽季比較三振機率模型、基準誤差與信賴區間。'),
 ('about','/data/','資料與方法','資料與計算方法｜Matchup Lens','Rebas 開放資料來源、分析母體、資料清理、收縮估計與研究限制。'),
 ('guide','/guide/','使用說明','使用說明與常見問題｜Matchup Lens','了解Matchup、比例區間、情蒐摘要下載與分享連結的使用方式。'),
]

def layout(page,path,label,title,description,content,script=True):
 nav=''.join(f'<a class="nav-item{" active" if k==page else ""}" href="{url}"'+(' aria-current="page"' if k==page else '')+f'>{html.escape(name)}</a>' for k,url,name,*_ in PAGES)
 crumb='' if page=='home' else f'<div class="breadcrumb"><a href="/">首頁</a><span class="breadcrumb-divider">/</span><span>{html.escape(label)}</span></div>'
 loading='<div id="loading" role="status">正在載入資料。</div>' if script else ''
 return f'''<!doctype html>
<html lang="zh-Hant"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{html.escape(description,quote=True)}">
<meta name="theme-color" content="#07151a">
<meta property="og:type" content="website"><meta property="og:title" content="{html.escape(title,quote=True)}"><meta property="og:description" content="{html.escape(description,quote=True)}"><meta property="og:url" content="{ORIGIN+path}">
<link rel="canonical" href="{ORIGIN+path}"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="/style.css"><link rel="stylesheet" href="/scout.css"><link rel="icon" href="/favicon.svg" type="image/svg+xml">
</head><body data-page="{page}">
<a class="skip-link" href="#main-content">跳至主要內容</a>
<header class="site-header"><div class="header-inner">
<a class="site-name" href="/" aria-label="Matchup Lens 首頁"><b class="brand-mark" aria-hidden="true">ML</b><span class="brand-name">Matchup<br>Lens<span>CPBL Scouting</span></span></a>
<div class="site-context">CPBL Scouting Desk<span>2024 / 2025</span></div></div>
<nav class="main-nav" aria-label="主選單"><div class="nav-inner">{nav}<span class="nav-note">資料年度 2024–2025</span></div></nav></header>
<main id="main-content" class="container">{crumb}{loading}{content}</main>
<footer class="site-footer"><div class="footer-inner"><div><a class="footer-brand" href="/">Matchup Lens</a><span>中職投打對戰資料研究</span><div class="footer-links"><a href="/guide/">使用說明</a><a href="/data/">資料來源與授權</a><a href="/results/">Validation</a></div></div><p>資料來源：Rebas 野球革命 Open Data（ODC-By 1.0）<br>歷史資料研究工具・介面更新 2026/11/10；資料年度 2024–2025<br>獨立研究作品，非中華職棒或資料提供者的官方網站。</p></div></footer>
{('<script type="module" src="/app.js"></script>' if script else '')}
</body></html>'''

for page,path,label,title,description in PAGES:
 content=(SITE/'pages'/f'{page}.html').read_text(encoding='utf-8')
 target=DIST/path.strip('/')/'index.html'
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_text(layout(page,path,label,title,description,content,script=page!='guide'),encoding='utf-8')

notfound='<section class="plain-page"><p class="page-kicker">404</p><h1>找不到這個頁面</h1><p>網址可能已變更。請回到首頁，或重新進入Matchup。</p><div class="page-actions"><a class="button primary" href="/">回到首頁</a><a class="button" href="/query/">Matchup</a></div></section>'
(DIST/'404.html').write_text(layout('notfound','/404.html','找不到頁面','找不到頁面｜Matchup Lens','找不到指定頁面。',notfound,False),encoding='utf-8')
(DIST/'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="6" fill="#007f9c"/><path d="M14 46V18h7l11 17 11-17h7v28h-8V31L32 46 22 31v15z" fill="white"/></svg>',encoding='utf-8')
print(json.dumps({'pages':[x[1] for x in PAGES],'output':str(DIST)},ensure_ascii=False))
