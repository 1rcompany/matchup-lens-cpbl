# Matchup Lens｜中職對戰情報可信度

中職歷史投打對戰分析網站，以 Rebas 2024–2025 例行賽開放資料製作。包含三振對戰分析、多人比較、逐球情蒐、揮空率模型及球種位置分布。

網站：https://matchup-lens-cpbl-anson.rosycoin67.chatgpt.site

## 在自己的電腦開啟

儲存庫已包含網站所需的彙整資料與模型權重。下載後，在專案根目錄執行：

```bash
python3 -m http.server 8000 --directory dist
```

用瀏覽器開啟 http://localhost:8000 。一般瀏覽不需要訓練模型、安裝 Python 套件或設定 API key。請透過 HTTP 開啟，瀏覽器直接開啟 HTML 檔會限制資料載入。

## 修改網站

頁面內容位於 `site/pages/`，共用版型位於 `site/build.py`。修改後執行：

```bash
python3 site/build.py
```

樣式與前端程式直接維護於 `dist/`。`dist/` 可部署到支援根路徑路由的靜態網站服務。

## 功能

- 以球員 ID 選擇投手、打者；查看歷史對戰三振數與打席數。
- 比較原始三振比例、Wilson 90% 區間、球員組合基準及收縮估計。
- 顯示對戰資料直接權重；可下載中文文字情蒐卡。
- 顯示時間外驗證、按樣本數分組的結果與資料排除規則。
- 無 API key、無登入、無後端、無外部字型或追蹤服務。原型不是即時賽事系統。

## 重建資料

Python 3，套件僅需 numpy。執行 `python analysis/build_data.py` 會從官方 Rebas GitHub Releases 下載兩季 ZIP，檢查固定 SHA-256，重建 `dist/data.json`、`analysis/results.json`、`analysis/eligible_pa.csv`。也可用 `--raw-dir /path/to/existing/zips` 重用既有下載。

`dist/` 可由任何靜態 HTTP 伺服器提供；請勿直接以 file:// 開啟，以免瀏覽器限制 fetch。Sites 部署目錄為 dist。

## 驗證與結果

2024 年 8 月前訓練，8 月起選參數；重估 2024 全季後固定模型，測試 2025。2024 有 27,365 有效打席、2025 有 27,033 有效打席，各 360 場。模型 Brier 0.137574，聯盟平均 0.139517；球員組合基準 0.137571。相較球員基準的差異區間包含零，不能宣稱加入對戰資料帶來額外提升。

球員基準：排除此組對戰後，以聯盟率平滑兩名球員的比例；合併兩者 log-odds 並扣除聯盟 log-odds。最終預測 `(k + m * p0) / (n + m)`。球員平滑強度及 m 只依 2024 後段 Log loss 選定，均為 100。Wilson 區間只描述歷史二項比例，不是此預測的後驗區間。

完成打席結果使用實際 JSON 的 `result` 欄位（schema 文件寫作 results，程式兼容兩者）。排除空字串、IBB、妨礙事件及不明結果 H。犧牲觸擊與犧牲飛球列入分母。這是本作品自訂的三振分析母體，不應直接當成官方所有打席口徑。以單場名單 playerId 合併跨年資料；球隊為資料最後觀察記錄。

## 資料與授權

資料來源：Rebas 野球革命 Open Data，https://github.com/rebas-tw/rebas.tw-open-data ，ODC-By 1.0，全文見 `dist/DATA_LICENSE.txt`。保留來源署名與來源 SHA-256；原始 ZIP 不納入 Git。部分資料為人工記錄。下載連結、版本及 SHA-256 固定於重建程式。

`analysis/eligible_pa.csv` 是清理後衍生資料，b / p 欄位為來源球員 ID。衍生彙整資料 `dist/data.json` 使用相同來源署名，並非主辦單位官方模型。未使用球隊商標、球員照片或私人報名資料。

## 已知限制

對戰模型預測三振；逐球模型預測揮棒後的揮空機率。兩者都不代表打擊整體價值，也不作因果推論、最適打線或換投建議。逐球模型使用球種、投球前球數、左右手及球員 ID，位置圖另作描述性彙整；未納入疲勞、球場或傷勢。區間採獨立二項近似。95% Brier 差異區間以 2025 比賽作 2,000 次 block bootstrap，未包含重新訓練的不確定性。MLP 為探索性結果：開發前已看過 2025 的既有模型表現，仍需新賽季獨立驗證。

## 網站頁面與重建

`python site/build.py` 產生首頁 `/`、對戰查詢 `/query/`、研究結果 `/results/`、資料與方法 `/data/` 及使用說明 `/guide/`。頁面內容在 `site/pages/`，共用版型在 `site/build.py`；CSS 與瀏覽器邏輯直接編輯 `dist/style.css` 與 `dist/app.js`。

查詢網址以 pitcher / batter 球員 ID 儲存選擇，重載後還原；可複製連結或下載帶來源的文字情蒐摘要。舊版首頁 #matchup / #validation / #about 書籤會導至對應獨立頁面。現有示範網站可公開瀏覽。

## 2026-11-07 更新
新增 `/compare/` 多人比較（固定投手、最多九名打者、CSV 匯出），以及 `/results/` 的固定 5pp 校準表。`python analysis/calibration.py` 從清理打席重建凍結模型校準，並驗證 Brier 與既有獨立測試相符。網站 `/research-notes.md` 保存選題、來源、研究結論與後續驗證決策。

## 球數情境情蒐（2026-11-07）
主產品入口 `/pitch/`。來源固定為 Rebas 2024–2025 例行賽 ZIP；執行 `python analysis/pitch/build.py` 建立 `dist/pitch-data.json` 與結果。來源 ZIP 統一放在專案的 `data/raw/`。`python analysis/pitch/test_parity.py` 驗證彙總與凍結年度並產生跨語言測試資料；前端公式在 `dist/pitch-model.mjs`。模型及資料口徑詳見 `dist/pitch-research.md`，網站亦提供下載。

### MLP and spatial lab (v7)
`python analysis/pitch/deep.py` trains temporal one-hot MLP (scikit-learn 1.8.0, numpy, threadpoolctl), writes benchmark/zone aggregates and weights. `python analysis/pitch/export_mlp.py` exports browser weights and parity fixtures. `node analysis/pitch/test_mlp.mjs` checks cross-language inference and zone denominators. Then `python site/build.py`. Sources need the same SHA-verified Rebas zip files as the pitch pipeline. Test results are exploratory because 2025 was inspected in the previous version. Browser inference uses frozen 2024 weights, never trains on user input. See `/pitch-research.md` for limitations.

## 從原始資料重建全部分析

需要 Python 3.11 以上；最後一項前端一致性檢查需要 Node.js。原始 ZIP 不納入儲存庫，第一個分析程式會從官方 Releases 下載至 `data/raw/` 並驗證 SHA-256。

```bash
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python analysis/build_data.py
python analysis/calibration.py
python analysis/pitch/build.py
python analysis/pitch/test_parity.py
python analysis/pitch/deep.py
python analysis/pitch/export_mlp.py
node analysis/pitch/test_mlp.mjs
python site/build.py
```

網站已附有以上程式產生的結果，僅修改頁面或瀏覽示範時不需要重跑分析。訓練耗時與浮點結果可能因執行環境而略有差異。
