# 改善 Roadmap（可直接交給 Codex）

本輪只完成稽核報告；以下任務是下一輪的 PR-sized 工作單位，不代表本輪已修改程式。每一項都明確保留目前的 feature、split、threshold 與正式結果。

## 優先排序方法

依提示詞使用 `Priority Score = (Impact × Confidence Weight) / (Effort + Risk)`；Impact／Effort／Risk 為 1–5，High／Medium／Low confidence weight 分別為 1.0／0.7／0.4。P0 即使分數低也優先。本次沒有新發現的 P0；以下 P1 先處理會影響證據可信度、資料安全或正式使用的項目。

| 順序 | Task | Findings | Impact | Effort | Risk | 信心 | Score 參考 | 分類 |
|---:|---|---|---:|---:|---:|---|---:|---|
| 1 | R1 Matrix evidence integrity | EXP-002, AGG-001 | 5 | 2 | 2 | High | 1.25 | A 立即 |
| 2 | R2 Formal dataset contract | DATA-001 | 5 | 3 | 3 | High | 0.83 | A 立即 |
| 3 | R3 Archive safety + channel policy | SEC-003, DATA-002 | 5 | 2 | 3 | Medium | 0.70 | A 立即 |
| 4 | R4 Reproducible run metadata | ENV-001, REPRO-001, REPRO-002, DATA-003/004 | 4 | 3 | 2 | High/Medium | 0.80/0.47 | B 下一輪 |
| 5 | R5 CI and high-risk tests | TEST-001, TEST-002 | 4 | 3 | 2 | High | 0.80 | B 下一輪 |
| 6 | R6 Web security boundary | SEC-001, SEC-002 | 5 | 3 | 3 | High/Medium | 1.00/0.58 | A 立即 |
| 7 | R7 Config/API contracts | ARCH-001, ARCH-003 | 3 | 3 | 2 | High | 0.60 | B 下一輪 |
| 8 | R8 Profiling before cache/vectorization | PERF-001/002 | 3 | 3 | 2 | Medium | 0.42 | C 中期 |
| 9 | R9 Current docs and Windows onboarding | DOC-001, DX-001 | 3 | 2 | 1 | High | 1.00 | C 中期 |
| 10 | R10 Orchestration refactor after contracts | ARCH-002 | 3 | 4 | 2 | High | 0.50 | C 中期 |

## A. 立即處理

### R1 — Matrix resume 與 aggregate evidence integrity

- **目標**：只有 `summary.json`、`results.csv`、`run.log`、manifest identity 與結果 schema 全部一致時，才可 resume／aggregate。
- **修改範圍**：`experiments/exp6_matrix.py` 的 `_is_complete()` 與完成寫入；`experiments/aggregate_exp6.py` 的共用 artifact validator；新增 `tests/test_exp6_matrix.py`／`tests/test_aggregate_exp6.py` fixture cases。
- **不修改**：detector、feature、60/20/20 split、threshold、既有 54-run metrics、正式 data。
- **步驟**：
  1. 定義預期 `results.csv` 欄位與一列 condition contract。
  2. 檢查 summary／CSV／log 存在、可解析、run_id／method／seed／motor／rpm／fingerprint 一致。
  3. 將 stale run 標成待重跑，不刪除既有檔案。
  4. aggregate 重用同一 validator，provenance 取自驗證後的 summaries。
- **測試**：valid resume；缺 summary、缺 CSV、缺 log、CSV schema 錯、fingerprint 錯、condition mismatch、tampered aggregate manifest；確認 invalid evidence 非 0 退出。
- **驗收**：刪除任一 artifact 後 matrix 不會誤判 completed；合法 54-run aggregate 結果逐欄與目前 artifact 相同；`git diff --check` 與全測試通過。
- **依賴**：目前 exp6 schema、DATA-003 fingerprint policy；先不需要新套件。
- **Rollback**：revert validator commit；不重寫或刪除舊 output。
- **建議 commit**：`test(exp6): cover missing matrix artifacts` → `fix(exp6): validate resume evidence` → `fix(aggregate): reuse matrix artifact contract`。
- **Effort/Risk**：M／中；風險是舊 output schema 被正確拒絕，應回報而非放寬 assertion。

### R2 — Formal dataset schema validator

- **目標**：把目前「9 工況、10 config、105 維」從默認假設提升為可驗證 contract，缺檔或欄位漂移立即失敗。
- **修改範圍**：新增 `core/formal_contract.py` 或擴充 `core.data`；在 `experiments/exp6_osr_benchmark.py` 與 materialization smoke 入口呼叫；新增小型 fixture tests。
- **不修改**：正式 raw archive、既有清洗規則、特徵名稱定義、已產生 54-run 結果。
- **步驟**：
  1. 由 `core.formal_data` 的 `MOTORS`、`RPMS`、`CONFIGS`、`FEATURE_NAMES` 建立單一 contract。
  2. 驗證 exact condition set、每個 class 一個 clean CSV、欄名與順序、105 維、dtype、finite、非空與 duplicate。
  3. `strict=True` 僅供 formal exp6；明確保留 legacy compatibility mode 並發 warning。
  4. 在 error 中列出缺少／多出的具體項目與資料根目錄。
- **測試**：合法 9×10 fixture；缺 class、duplicate condition、reordered/renamed column、extra numeric column、empty/nonfinite rows、中文 Windows path。
- **驗收**：合法 formal_local 通過；任一契約違反在 model fit 前以明確錯誤結束；不再由 `select_dtypes` 靜默改變欄位意義。
- **依賴**：先閱讀 DATA-002 的 channel policy；與 R1 的 fixture 可共用。
- **Rollback**：revert validator wiring，保留 validator module，不碰資料。
- **建議 commit**：`test(data): add formal contract fixtures` → `feat(data): validate formal dataset schema` → `feat(exp6): enable strict formal validation`。
- **Effort/Risk**：L／中高；若來源資料存在未文件化例外，先列 evidence，不直接修改資料。

### R3 — Archive containment 與 channel window policy

- **目標**：拒絕不安全 Stage-2 archive member，並將 channel 寬度不一致從隱式截斷變成可追溯政策。
- **修改範圍**：`core/formal_data.py` 的 `_convert_condition()`、materialization manifest 欄位；`tests/test_formal_data.py` archive fixtures。
- **不修改**：可信正式 archive 的 bytes、IQR 清洗公式、既有 feature vector 順序。
- **步驟**：
  1. 以 `CONFIGS`／允許 path component 驗證 motor、rpm、config。
  2. 寫入前檢查 resolved output 在 output_root 下。
  3. 與資料擁有者確認 mismatch policy：fail-fast 或保留 min-width 但記錄每通道原始寬度／截斷數。
  4. 增加 manifest schema version 與 portable path policy。
- **測試**：`..`、絕對路徑、Windows drive component、未知 config archive；equal-width 與 unequal-width channel fixtures；確認不會在 output_root 外寫檔。
- **驗收**：惡意 fixture 以 `FormalDataError` 結束且 output_root 外無檔；正式來源重跑的 manifest hash／rows 與既有基線一致，或由資料 owner 明確批准差異。
- **依賴**：DATA-001 contract；資料 owner 對 568–600 raw width 差異的決策。
- **Rollback**：先 revert policy enforcement，保留 regression tests；禁止以 force overwrite raw source 回復。
- **建議 commit**：`test(data): cover archive traversal` → `fix(data): constrain stage2 output paths` → `docs(data): record channel alignment policy`。
- **Effort/Risk**：S–M／中；policy 選擇可能改變未來 materialization 行為，必須保留 fingerprint 對照。

### R6 — Web origin、token 與錯誤脫敏

- **目標**：本機展示預設安全，LAN 模式必須明確啟用；未授權 WebSocket 不能控制 reset／confirm／dataset。
- **修改範圍**：`web/server.py`、`web/live.py` protocol；新增 `tests/test_web_server.py` 或不啟動真 socket 的 handler fixture；README 展示設定。
- **不修改**：LiveDemo 的模型、scenario、metrics、session schema。
- **步驟**：
  1. 將 bind default 改 localhost，加入 `--host`／`--allowed-origin`／optional token。
  2. `check_origin()` 僅接受 allowlist；token 以 constant-time compare，不寫入 log。
  3. command payload 做 schema/型別/enum 驗證。
  4. 例外詳細內容留 server log，以 correlation id 回傳固定錯誤碼。
- **測試**：allowed/disallowed Origin、missing/wrong token、malformed JSON、unknown command、path-containing exception；localhost demo smoke。
- **驗收**：預設啟動只在 localhost；未授權控制命令不改 HUB 狀態；client message 不含絕對路徑或 traceback；授權展示流程仍可完成。
- **依賴**：使用者需決定發表日是否允許 LAN mode；不需要模型變更。
- **Rollback**：revert server security commits；保留測試與明確的 temporary LAN flag，不恢復無條件 `True`。
- **建議 commit**：`test(web): cover origin and command validation` → `fix(web): restrict websocket access` → `fix(web): sanitize client errors`。
- **Effort/Risk**：M／中；錯誤的 allowlist 可能影響展示連線，驗收需含 local default。

## B. 下一輪處理

### R4 — 統一 run metadata、environment 與 fingerprint

- **目標**：exp1–3 與 exp6 使用同一個 versioned metadata contract，能回答資料、程式、參數、軟硬體與 output identity。
- **修改範圍**：新增 `core/run_metadata.py`；`experiments/exp1_cold_start.py`、`exp2_scale_growth.py`、`exp3_trend.py`、`exp6_osr_benchmark.py`；manifest export／private provenance sidecar。
- **不修改**：metrics 定義、split、threshold、detector math、歷史數值；不把絕對來源路徑放入 shared result。
- **步驟**：
  1. 定義 `schema_version`、run_id、commit、dataset fingerprint/strategy、resolved config、Python/package versions、OS/hardware optional fields。
  2. fallback fingerprint 改 content SHA-256 或 formal mode 缺 manifest 就 fail。
  3. exp1–3 先 metadata-only migration，再對一個 fixture 做 before/after metric diff。
  4. portable manifest 與 local private provenance 分開。
- **測試**：same-size/same-mtime different content fingerprint；metadata schema parser；package/hardware unavailable 明確標記；exp1–3 fixture metrics byte/tolerance regression。
- **驗收**：四個入口輸出可被同一 parser 讀取；summary 不含 user-specific absolute path；相同 code/data/config 可識別為同一 run identity。
- **依賴**：ENV-001 支援版本政策、DATA-003/004、R1 schema。
- **Rollback**：保留舊 summary reader；以 schema version 分支讀取，不刪除舊結果。
- **建議 commit**：`feat(metadata): add versioned run contract` → `refactor(exp1-3): attach run metadata` → `refactor(exp6): record environment metadata` → `test(metadata): enforce provenance schema`。
- **Effort/Risk**：L／中；需避免 metadata-only 變更誤改 metrics。

### R5 — CI 與高風險測試矩陣

- **目標**：每次 push/PR 自動執行核心測試與高風險 contract tests，故意失敗時 workflow 必須失敗。
- **修改範圍**：`.github/workflows/tests.yml`、`pyproject.toml` dev extras、`tests/` fixture；不加入 1.6 GB raw archives。
- **不修改**：正式 data、GPU dependency、論文結果；不以降低 assertion 換取綠燈。
- **步驟**：
  1. 依 ENV-001 決定 Python/OS matrix，先 CPU-only Linux/Windows。
  2. 加 data loader、resume/failure、aggregate、Web protocol、exp1–3 metadata、中文 path、deterministic seed tests。
  3. 若採 pytest/coverage，保留 unittest discover 相容入口並設高風險檔案的合理門檻。
  4. 保存短期 test artifact，不上傳 raw data/secrets。
- **測試**：本機跑 workflow 等價命令；注入一個故意失敗 test 確認 job 非 0；檢查 no silent skip。
- **驗收**：PR required check；Linux/Windows fixture tests 綠；Web/loader/exp1–3 至少各有正負案例；沒有秘密與 raw data artifact。
- **依賴**：ENV-001、R1/R2/R6 的 fixtures；不要先安裝 TensorFlow/GPU。
- **Rollback**：停用 workflow job 不刪除本機 tests；保留 branch protection 變更紀錄。
- **建議 commit**：`test: add high-risk fixture contracts` → `ci: run core tests on supported platforms` → `ci: publish bounded coverage`。
- **Effort/Risk**：M–L／中；Windows dependency resolution 是主要風險。

### R7 — 設定與 monitor API contract

- **目標**：減少 exp6 與 exp1–3 的設定分叉，並讓未 fit 的 monitor 以清楚錯誤失敗。
- **修改範圍**：`core/runner.py`、`core/monitor.py`、新增 typed config/schema tests；逐步接入 exp6 parser。
- **不修改**：公開 CLI option 名稱、預設 detector、模型數學。
- **步驟**：先加入 `_require_fitted()`；再建立 canonical config object 與 precedence；逐一替換 parser glue，保留舊 flags。
- **測試／驗收**：pre-fit score/classify/project 全部是明確 RuntimeError；四個 CLI 的 canonical method／default 一致；舊命令仍可解析。
- **依賴**：R4 metadata；先完成 TEST-002 fixture。
- **Rollback／commit**：`fix(monitor): guard unfitted inference` → `feat(config): add canonical experiment config`，可各自 revert。
- **Effort/Risk**：S + M／低到中。

## C. 中期改善

### R8 — 先 profiling，再做 data cache 或 k-NN 批次化

- **目標**：用實際 load/reload、class count、reference-bank size 與 batch size 找瓶頸，不因猜測改數值路徑。
- **檔案／非範圍**：新增 benchmark script／report，可能改 `core.data` cache 或 `core.openset` batching；不改 threshold、score direction、正式 output。
- **步驟／測試**：記錄 wall time、peak memory、cache hit；content fingerprint+schema 作 cache key；score/order 與 uncached path regression。
- **驗收／rollback**：達到預先設定的 target-scale改善才合併；否則只保留 benchmark 報告。commit 可拆 `bench(perf)` → `feat(data): opt-in cache` → `feat(knn): batch distances`。
- **Effort/Risk**：M–L／中；目前 baseline 不支持高優先度。

### R9 — Current documentation、troubleshooting、Windows onboarding

- **目標**：新成員可從安裝、materialize、validate、單次 Mahalanobis/k-NN、matrix、resume、aggregate 一路走完。
- **檔案／非範圍**：更新 `README.md`、新增 `docs/Lineage_Operations.md`，標示 `docs/` historical Ancestor；不重寫歷史論文文件。
- **步驟／驗收**：每個 command 在 Windows PowerShell 與 Linux 各 smoke 一次；current links 全部可解析；明確說明 PolarMap 固定 Mahalanobis、known/unknown、threshold calibration、output schema。
- **Rollback／commit**：文件可單獨 revert；`docs: add Lineage operations runbook`、`docs: clarify historical links`。
- **Effort/Risk**：S–M／低。

### R10 — Orchestration 分拆（先 contracts 後 refactor）

- **目標**：把 exp6 run、matrix runner、LiveDemo.tick 的純驗證／scoring／serialization 與副作用分開，降低維護成本。
- **非範圍**：不重新設計 detector、不改 public function signature、不改 Web flow 或 metrics。
- **步驟／測試／驗收**：先為每個邊界建立 fixture contract，再每次只抽一個 helper；輸出 JSON/CSV schema、metric rows、event order 與 runtime regression 保持相容。
- **Rollback／commit**：每個 helper 一個可 revert commit；禁止「重構整個專案」單一 PR。
- **Effort/Risk**：L／中；依賴 R1、R5、R7。

## D. 長期研究（非工程阻塞）

以下不應插隊到資料／證據完整性之前：多 known-class OSR、跨工況 domain shift、threshold calibration confidence intervals、bootstrap／paired statistical tests、class imbalance／unknown composition sensitivity、robustness/noise、部署監控與 drift。每一項都必須保留目前 health-only 54-run 作為 baseline，另開 schema version 與結果目錄，不覆蓋既有正式結果。

## 本輪完成界線

本輪沒有修改演算法、資料、split、threshold、正式輸出或使用者未提交檔案；只新增／更新 `reports/project_health_audit/` 並逐階段 commit＋push。下一步應由使用者從 R1、R2、R3、R6 中選擇，不要一次執行所有 roadmap。
