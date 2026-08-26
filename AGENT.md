# AGENT.md — Agent 指引文件

本文件為 AI Agent（含 Claude Code 等自動化工具）提供操作本專案的背景知識、慣例與行為準則。

---

## 專案定位

本 repo 目前的主線是**冷啟動 PHM 畢業專題**：只用健康資料（8screws）建立基準，
即時偵測未知故障、以 HDBSCAN 發現新故障類型、經操作員確認後擴張「健康量尺」
（開放集 + 持續學習），並以變化點分析判別故障是漸進磨損還是突發事件。
完整說明、實驗結果與引用文獻見 [README.md](README.md)。

原論文版程式碼（Step 1–6 管線、128 個 notebook、docs 與論文全文）已整批移回
[Ancestor](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor) repo
（本機路徑 `~/Ancestor`）保存；本 repo 的 git 歷史仍保留搬移前的所有版本。

---

## 目錄結構

```
core/            共用零件：data / mahalanobis / monitor / trend / logger / runner
experiments/     三個實驗模組（exp1_cold_start、exp2_scale_growth、exp3_trend）
web/             即時展示（live.py 編排、server.py Tornado+WS、static/index.html）
data/            特徵資料（git 忽略；由論文版管線產出，本專案唯讀）
logs/ output/    每次執行的日誌與結果（納入版控）
run_web.sh       啟動展示伺服器
build_uv.sh      建 venv；--legacy 加裝論文版管線依賴（TF/CUDA、Jupyter）
```

---

## 鐵則（違反會破壞專案架構）

1. **不依賴論文版程式碼。** 需要其零件時，以「複製 + 檔頭註記來源」帶入
   （範例：`core/mahalanobis.py`）。論文版程式碼在 Ancestor repo，視為唯讀封存。
2. **實驗邏輯只住在 `experiments/` 與 `core/`。** `web/` 只做編排與視覺化——
   任何判定、分群、統計邏輯若出現在 web 層就是放錯位置。這是為了讓論文批次執行
   與即時展示共用同一份邏輯、數字一致。
3. **每個實驗模組維持雙介面**：`run(pools, ...) -> dict`（程式化 API，web 與論文都呼叫）
   ＋ `main()`（CLI，`python -m experiments.expN_*`）。新增實驗照此模式。
4. **logs/output 慣例**：所有可執行程式經 `core.logger.setup_run(program)` 初始化，
   產生 `logs/{program}/{ts}.log` 與 `output/{program}/{ts}/`；圖表用 `save_plot()`。
   不要自創輸出位置。
5. **資料唯讀**：本專案只讀 `data/Step-*/myfeature/**/*_Group_feature_data_clean.csv`
   （105 維，最後過濾版）。不重新產生、不修改 data/ 內容；缺資料時提示以論文版管線
   （Ancestor）產出。
6. **未知資料絕不參與擬合**：訓練／校準／閾值只用已知類別；ground-truth 標籤只在
   「操作員確認」步驟揭示（`ScaleGrowthSession.confirm()`）。動到這條就毀了實驗效度。
7. **決定論**：所有隨機性走 `numpy.random.default_rng(seed)`，seed 從 CLI/建構子傳入，
   預設 42。修改後同 seed 應重現同數字。

---

## 關鍵參數（預設值）

| 參數 | 值 | 所在 |
|---|---|---|
| 已知類別切分 | train/cal/holdout = 60/20/20 | `core.data.make_split` |
| 共變異數估計 | Ledoit–Wolf（逐類）| `core.monitor.OpenSetMonitor` |
| 校準信心水準 | 0.95（校準距離分位數）| `--confidence` |
| 開集判定 | 正規化分數 > 1 = 未知 | `core.mahalanobis` |
| HDBSCAN | min_cluster_size=25, min_samples=3 | `experiments.exp2_scale_growth` |
| 重分群節流 | 每 10 筆新未知樣本試一次 | 同上 `recluster_every` |
| 隔離線 | 分數 > 2.0 才進隔離區（偵測線仍為 1.0）| 同上 `quarantine_margin` |
| 趨勢 EWMA | alpha=0.08 | `core.trend.TrendMonitor` |
| 中間帶 / 警報線 | [0.2, 0.5) / 0.5 | 同上 |
| 突發判定 | 中間帶停留 ≤ 12 筆 | 同上 `sudden_max` |
| 特徵維度 | 105（固定，不可增減）| 資料層 |

---

## 常用指令

```bash
# 三個實驗（在專案根目錄執行；輸出到 logs/ 與 output/）
venv/bin/python -m experiments.exp1_cold_start --motor T1 --rpm 8000rpm
venv/bin/python -m experiments.exp2_scale_growth --sequence 5screws 3_14screws
venv/bin/python -m experiments.exp3_trend --trials 40

# 即時展示（http://localhost:8600）
./run_web.sh
./run_web.sh --port 8600 --motor T1 --rpm 8000rpm --rate 4

# 環境
./build_uv.sh              # 新專案依賴（無 TF、不需 GPU）
./build_uv.sh --legacy     # 另需重跑 legacy 管線時
```

---

## 已知行為與陷阱

1. **健康誤報率 ≈ 10.9%**（名目 5%）：校準集只有 ~62 筆的有限樣本效應，是已知結果
   不是 bug；EWMA 警報線與中間帶下緣（0.5 / 0.2）就是據此拉開的，調整前先看
   `experiments/exp3_trend.py` 的分布數據。**衍生設計**：誤報分數僅些微超線
   （實測 1.01–1.08），而真實故障最低分 ≥ 10——因此隔離區設「隔離線」
   `quarantine_margin=2.0`，邊界誤報只警報、不參與新類發現；若仍有已知類別
   邊界樣本聚成叢，`confirm()` 回傳 `action="rejected_known"`（操作員退回、
   清叢、量尺不變）作為第二道保險。web 偵測統計拆「學會前偵測率／學會後
   認出率」兩組，認出率天生 ≈ 90–95%。
2. **3_14screws 特徵發散**：在 HDBSCAN 下需要遠超 25 筆才成叢；exp2 全序列重播中
   它在自身階段（600 筆）未被發現，其樣本累積到下一階段才成叢。
3. **exp2 的 stage 列「learned」欄可能不等於注入配置**：候選叢集取自整個隔離區，
   多數決可能是前一階段的殘餘（CSV 中有 `learned` 欄，判讀時以它為準）。
4. **量尺擴張後 PCA 投影會變**：web 前端在已知類別數改變時清空散佈圖，這是刻意行為。
5. **目錄名陷阱**：螺絲配置目錄可能是 `1screw` 或 `1screws`（既有資料兩種都出現過），
   `core.data` 以掃描目錄迴避硬編碼——不要寫死配置清單去讀資料。
6. **T2（Step-2）資料不全**：備份僅含部分特徵檔；`discover_datasets` 只列出實際
   存在 clean CSV 的 (motor, rpm) 組合，以掃描結果為準。
7. **venv 相容性**：現有 venv 是舊依賴集（含 TF）建的超集，可直接跑新專案；
   重建才會套用新 `pyproject.toml`。伺服器用的 Tornado 由 Jupyter 附帶或新依賴提供。

---

## Web 協定摘要（改前端前先讀）

WebSocket `/ws`，JSON 訊息：

- server → client：`state`（完整狀態）、`state_patch`、`sample`（逐筆分數/判定/PCA/EWMA）、
  `event`（info/warn/success/error）、`metrics`
- client → server：`{cmd: start|pause|reset|rate|set_source|scenario|confirm|dataset, ...}`
- 重任務（confirm/reset/dataset）在執行緒池執行，期間 `busy=true`、串流暫停。

---

## GitHub

1. 允許在完成改動後 commit and push，但應建立 PR 或 issues。
2. `logs/` 與 `output/` 納入版控，不需要加入 .gitignore；`data/` 維持忽略。
3. Agent 進行 GitHub 相關操作時，將自己加入 Co-Authors。
4. legacy 的 issue 討論串在 [Ancestor](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor)，查缺陷成因時到該處。
