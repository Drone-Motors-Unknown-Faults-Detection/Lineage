# `ancester` Open Set / exp6 任務進度

## P1 — Git 與 repository 基線

本報告由 P1 建立，記錄本任務開始時可重現的 Git 狀態與推送安全檢查。原始工作樹中的未提交檔案未被修改、覆蓋或加入本 commit。

| 項目 | 結果 |
|---|---|
| Lineage repository | `https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage.git` |
| local repository path | `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\Lineage` |
| 原始工作樹 branch | `feat/knn-openset-comparison` |
| 原始工作樹 HEAD | `a28763c0c968d317b15305a54f8a3ed4829d6fbe` |
| 原始工作樹 upstream | 未設定 |
| 原始工作樹 push remote | `origin`（Lineage organization repository） |
| 同名遠端 branch | `origin/feat/knn-openset-comparison`，HEAD `dd0190f7f4de7f3f624292cd32a98d12e413b4e1` |
| working tree | 不乾淨，但只有一個原有未追蹤檔案 |
| 原有未提交檔案 | `core/openset.py`（未加入本階段） |
| P1 隔離工作樹 | 由同名遠端 branch 建立；本報告在此工作樹提交 |
| 本任務候選 push 目標 | `origin feat/knn-openset-comparison`；先以遠端最新 HEAD 為基線，不覆蓋舊遠端內容 |

### P1 唯讀檢查

原始工作樹執行過：

```text
git status --short
git branch --show-current
git branch -vv
git remote -v
git rev-parse HEAD
git log --oneline --decorate -n 30
git diff
git diff --cached
git submodule status
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

結果重點：

- 原始 branch 沒有 upstream；不可把本地舊 HEAD 當成遠端最新狀態。
- `origin/feat/knn-openset-comparison` 比原始本地 HEAD 多 8 個 commit；原始本地 HEAD 是遠端 branch 的祖先。
- 原始工作樹的 `core/openset.py` 是使用者既有未提交檔案；同名遠端 branch 也已經有 tracked `core/openset.py`，因此沒有用 checkout、reset、clean 或 merge 去覆蓋該檔案。
- `git submodule status` 沒有列出有效 submodule；Git wrapper 在目前 Windows PATH 缺少 `basename`/`sed`/`git-sh-setup`，但不影響本次沒有 submodule 的判斷。
- `git diff` 與 `git diff --cached` 沒有 tracked/staged diff；未追蹤檔案內容未被 stage。

### Push dry-run

原始本地 HEAD 執行：

```text
git push --dry-run origin HEAD:refs/heads/feat/knn-openset-comparison
```

結果為 `non-fast-forward`，原因是本地 `a28763c` 落後遠端 `dd0190f`。因此本階段沒有從原始工作樹推送舊 HEAD；改用不含使用者未提交檔案的隔離工作樹，並在遠端最新 branch 上建立本 P1 commit，避免覆蓋遠端歷史。

## P2 — `Ancestor` 正式來源核對

使用者已提供並確認正式來源 URL：

`https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor`

雖然任務文字曾使用拼字 `ancester`，本次以使用者提供的完整 URL 為準，不再猜測其他 repository。

| 項目 | 已核對結果 |
|---|---|
| repository | `Drone-Motors-Unknown-Faults-Detection/Ancestor` |
| visibility | private；目前 GitHub 帳號可讀取 |
| default branch | `main` |
| source commit | `1ef4a891ae02dc95910f747a5163bb2edd608f28` |
| latest commit | `文件整理` |
| repository description | `未知故障預測核心程式碼` |
| license | GitHub metadata 未提供 license |
| Git LFS | `.gitattributes` 不存在；`git lfs ls-files` 無輸出 |
| releases / tags | 無 release、無 tag |
| tree 中實際資料檔 | 0 個 CSV、ZIP、NPY/NPZ、HDF5、Parquet 或 checkpoint |
| history 中實際資料檔 | 未找到上述資料檔路徑 |
| manifest / checksum | repository 未提供 |

### 文件所描述的正式資料格式

Ancestor 的 README 與 Step 1/2/4 文件一致描述正式資料應位於：

```text
data/Step-{1|2|3}/myfeature/{Motor}/{RPM}/{Screws}/
└── {Motor}_Group_feature_data_clean.csv
```

文件可核對出的 9 個正式工況為：

```text
T1/6000rpm, T1/8000rpm, T1/11000rpm
T2/6000rpm, T2/8000rpm, T2/11000rpm
T3/6000rpm, T3/8000rpm, T3/11000rpm
```

class mapping 為 10 類：

```text
0: 8screws      Healthy（known）
1: 1screw       Faulty 1（known）
2: 2screws      Faulty 2（known）
3: 3screws      Faulty 3（known）
4: 4screws      Faulty 4（known）
5: 5screws      New Faulty 1（unknown）
6: 6screws      New Faulty 2（unknown）
7: 7screws      New Faulty 3（unknown）
8: 3_14screws   New Faulty 4（unknown）
9: 4_146screws  New Faulty 5（unknown）
```

文件也指定：105 維特徵、`*_Group_feature_data_clean.csv` 為 IQR scale=1.5 逐列過濾版本，Step 4/5 使用 clean CSV；但這些都是 provenance/documentation，並不是目前已取得的資料物件。

### P2 驗收結論

- source repository、owner、URL、branch、source commit 已唯一確認。
- 文件格式、9 工況、class mapping、known/unknown 語意已確認。
- 實際正式資料本體沒有在 Ancestor Git tree、歷史、release 或 LFS 中；目前 workspace 與常用使用者資料目錄也沒有對應的 clean CSV 或 `data.zip`。
- 因缺少正式資料檔、manifest/checksum 與每工況樣本數，dataset fingerprint、split 樣本數、資料完整性與 P3 loader 初始化尚不能驗證。

P2 的 repository provenance 已完成，但「正式資料取得」是 P3 的必要前置，不能用 synthetic/demo data 代替，也不能宣稱 54 個正式 runs 已完成。

## 後續解除 P3 阻塞所需資訊

請提供以下任一項：

1. Ancestor 正式資料的實際資料根目錄（包含 `data/Step-*/myfeature/.../*_Group_feature_data_clean.csv`）；或
2. `data.zip`、`階段1.zip`、`階段2.zip`、`階段3.zip` 的受控下載位置；或
3. 可讀取該資料的 Git LFS／雲端／共享資料權限與下載方式。

取得資料後，才會進入 P3，建立 fingerprint、逐工況列樣本數、驗證 loader、split 互斥性，再逐階段修正程式並執行正式實驗。

## 2026-09-19：本機正式資料搜尋重新開工

使用者指定的唯讀資料根目錄 `D:\schoolshit\fcu\專題\馬達研究` 已確認存在並可讀取。本次沒有修改該目錄；完整 P1 inventory 已放在 [reports/raw_data_audit/](raw_data_audit/)。

| 階段 | 狀態 | 證據 | Commit | 下一步 |
|---|---|---|---|---|
| Raw data inventory | completed | 154 files、2 directories、4.598 GiB、3 outer ZIP、796 archive entries | `731313f` | 解析 raw／feature metadata |
| Data validation | completed with feature gap | 450 raw CSV、9/9 conditions、每 condition 50 files／10 classes／5 channels／10,000 rows；60 clean feature CSV、105 維且數值欄無非數值 | `061ec8b` | 建立 Lineage contract 對照 |
| Lineage data integration | pending implementation | P3 mapping confirms raw source is complete; T1/T3 features present; T2 features missing | — | 建立 configurable source adapter/conversion |
| Credibility issue 1 | fixed in working tree | Albert log `2026-09-18-22-44-35`: `rows=[]`, `n_datasets=0`, all summary metrics `NaN`, exit code 0 | pending | exp6 now fails fast on missing/incomplete formal data; regression test added |
| Credibility issue 2 | fixed in working tree | Albert README claims one calibration philosophy, but legacy detector calibrates on training distances (`core/mahalanobis.py` legacy path), producing 83.1% healthy false positives | pending | formal exp6 rejects legacy training-distance threshold; regression test added |
| Credibility issue 3 | fixed in working tree | Albert exp6 log and README report one seed (`seed=42`) and no across-seed uncertainty; this cannot support stability claims | pending | `experiments/exp6_matrix.py` emits a pending matrix and runs fixed seeds `42,123,2026` with resumable per-run status |
| exp6 factory integration | fixed in working tree | old Albert exp6 imported `core.detectors.ALL_DETECTORS`; new entry point imports `core.openset.create_openset_detector` | pending | factory mock, alias and source-inspection regression tests pass |
| Mahalanobis default | verified | `core.openset.create_openset_detector()` 預設 `mahalanobis`；11 tests passed | — | 保持回歸測試 |
| PolarMap base | pending | 只存在 `origin/main` 的 `core/geometry.py`／exp4 | — | 讀取 main 版本並驗證 |
| k-NN method | verified | factory、CLI、comparison tests；11 tests passed | existing feature commits | 不改變既有介面 |
| Experiment runner | pending | feature branch 沒有正式 exp6 matrix runner | — | 先完成資料與 factory |
| Seed 1 runs | blocked | 正式資料尚未完成 contract validation | — | — |
| Seed 2 runs | blocked | 正式資料尚未完成 contract validation | — | — |
| Seed 3 runs | blocked | 正式資料尚未完成 contract validation | — | — |
| Aggregate report | blocked | 不得以歷史 output 或 synthetic data 冒充正式 runs | — | — |

P1 原則：raw ZIP 保持在來源目錄；所有 inventory、驗證摘要與後續轉換輸出只放在 Lineage 的受版控報告或 ignored data/cache 路徑。未完成 P2/P3 前，不宣稱正式資料已可直接跑 exp6，也不執行 54-run 矩陣。

## P2 — raw data content validation

P2 以唯讀 ZIP stream 逐檔解析完成：

- 450 個 raw CSV 全部可讀；9 個正式工況全部存在。
- 每個工況固定 50 檔：10 個 screw configuration × 5 個 raw channel。
- 每個 raw CSV 都有 10,000 個資料列；檔案內列長一致，malformed row 合計 0。
- raw channel 檔案的欄數會依實際量測檔案而變（跨檔 568–600），不能把 raw array 欄數誤稱為 Lineage 的 105 維 feature。
- T1 與 T3 各有 30 個 clean feature CSV（3 RPM × 10 class）；每檔 105 欄，所有 body fields 都通過 numeric 檢查。
- T2 三個工況各有完整 raw CSV，但目前沒有 `myfeature.zip`／105 維 clean feature CSV；這是正式接入前必須處理的轉換缺口。
- model.zip 只列為 checkpoint 候選，沒有載入；notebook／Python 檔只作為 preprocessing provenance，不直接執行。

P2 產物：

- [raw validation](raw_data_audit/raw_validation.csv)
- [feature validation](raw_data_audit/feature_validation.csv)
- [condition summary](raw_data_audit/condition_summary.csv)
- [candidate inventory](raw_data_audit/candidate_inventory.csv)
- [P2 progress](raw_data_audit/p2_progress.json)

目前可以確認「9 個工況的 raw source 完整存在」，但不能把 T2 raw 直接當成已完成的 Lineage 105 維 feature source；P3 會把 raw/provenance 與 Lineage loader contract 做逐項對照，並決定可重現的 T2 conversion 方案。

## P3 — Lineage contract mapping

P3 mapping 已完成，詳見 [formal_contract_mapping.md](raw_data_audit/formal_contract_mapping.md)。三個 outer archive 的 SHA-256、nested condition archive metadata 與現有 clean-feature entry metadata 已寫入 [formal_source_manifest.json](raw_data_audit/formal_source_manifest.json)。

結論是：本機資料是可信的 9-condition formal raw source，但不是目前 loader 可直接讀的 `data/Step-*/myfeature/.../*_Group_feature_data_clean.csv` 目錄。T1/T3 的 60 個 clean feature 檔可作為已存在 processed reference；T2 的 150 個 raw CSV 必須透過可重現、只寫入 ignored processed root 的轉換補齊，不能用 synthetic 或歷史 output 代替。P3 mapping 本身不修改演算法或 exp6。

## P4 — formal data adapter and materialization

P4 已完成：`core/formal_data.py` 現在提供不依賴個人電腦路徑的正式資料轉換器。呼叫者必須明確傳入 `--source-root` 與 `--output-root`；轉換器會拒絕把輸出寫進 raw source 目錄。

### 已實作的轉換規則

1. Stage 1 / Stage 3：從巢狀 `myfeature.zip` 原樣複製 60 個既有 `*_Group_feature_data_clean.csv`，並檢查 105 個數值欄位。
2. Stage 2：從巢狀 `csv.zip` 讀取 T2 的 5 通道矩陣；每個視窗計算 15 個統計特徵，X/Y/Z 各加 10 個轉頻諧波 FFT 特徵，合計 105 維。
3. Stage 2 clean：依既有 T1/T3 檔案逐列比對確認的規則，對每個 feature 欄位套用 `Q1 - 1.5*IQR` 至 `Q3 + 1.5*IQR`，任一欄超界就移除整列。
4. 每筆輸出均寫入 materialization manifest，記錄來源 archive/member、SHA-256、清理前後列數與輸出路徑；raw source 永遠只讀。

### 實際物化驗收

```text
output: data/formal_local/       （Git ignored，不提交資料本體）
files: 90 = 30 copied Stage-1 + 30 converted Stage-2 + 30 copied Stage-3
conditions: 9/9 motor×rpm combinations
classes: 10/10 configurations per condition
feature shape: every file has 105 numeric columns and no NaN
rows after clean: 180–387 per class file
```

Smoke test（T2/8000rpm/8screws）實際讀取巢狀 ZIP 並產生 `599 → 368` clean rows；完整物化亦已由 Lineage `discover_datasets` 找到 9 組資料池，`load_pools` 每組都包含健康 `8screws` 基準。16 個單元測試通過，其中包含 feature-name 順序、1.5-IQR 規則、T1/T2/T3 channel alias 與禁止寫回 source 的安全測試。

本階段 commit：`2cac19f45056e382f59eaa03bb275d8499389268`（已推送至 `feat/knn-openset-comparison`）；正式資料本體與 manifest（含本機絕對路徑）不納入 Git。

## Credibility issue evidence and repair sequence

| 編號 | 問題與證據 | 影響 | 修正與驗證 |
|---|---|---|---|
| C1 | Albert exp6 在 `discover_datasets()` 回傳空集合時仍建立空摘要；log `2026-09-18-22-44-35` 明確記錄 `n_datasets=0`、`rows=[]` 與全 NaN | 空執行可被誤讀成 benchmark 完成 | exp6 對缺資料、重複條件、非 9 工況直接丟出非零錯誤；`tests/test_exp6_benchmark.py::test_missing_formal_data_fails_instead_of_nan_success`；已由 `e33ddb2` 固化 |
| C2 | Albert README 宣稱所有方法共用 calibration 95th percentile，但 legacy Mahalanobis 路徑在 `core/mahalanobis.py` 以 training distance 自校準；既有結果健康誤報 83.1% | 方法比較不是同一 threshold policy，主結論不公平 | 正式 exp6 限定 shared factory 的 `mahalanobis` / `knn`，兩者都只用 known calibration；新增 metadata 與 threshold regression，已由 `999da4c` 固化 |
| C3 | Albert exp6 只有 `seed=42` 一輪；README 的跨 9 工況平均沒有 seed variation | 無法知道結論是否跨隨機切分穩定 | `exp6_matrix.py` 先寫完整 pending matrix，再每 run 原子保存 summary/results/log，resume 只跳過通過 schema 的 completed run；P13 產生 mean±std；已由 `7be0419` 與後續矩陣修正固化 |

C2 的修正不刪除 `core.mahalanobis` 的 legacy 相容實作；它只禁止把不符合 shared calibration policy 的 legacy threshold 混入正式 Mahalanobis-vs-kNN 結果。歷史 legacy 結果仍可作為明確標示的診斷對照，但不會被當成正式公平比較。

## P7 — exp6 factory integration

`experiments/exp6_osr_benchmark.py` 直接呼叫 `core.openset.create_openset_detector`；exp6 不再 import `core.detectors`、不再維護另一份 detector registry 或 threshold policy。`core.openset.canonical_openset_method` 將 `k-nn` / `k_nn` / `maha` 正規化為 `knn` / `mahalanobis`，結果 metadata 同時保存 requested 與 canonical method。factory integration、alias、invalid method 與 exp6 呼叫 factory 的測試均通過。

## P8 — PolarMap 的 Mahalanobis 幾何基準固定

`core/geometry.py` 的 `PolarMap` 不再跟著 Open Set detector switch 改變幾何基準：不論該次 rejection detector 是 `mahalanobis` 或 `knn`，半徑、白化方向與 ray cosine 都使用同一個 Ledoit–Wolf Mahalanobis 模型，且只用 monitor 的 known train/calibration split fit。摘要固定寫入 `polarmap_base_method=mahalanobis`；health-only monitor 不會虛構 fault ray。兩個 regression tests 已確認 Mahalanobis 與 kNN monitor 在同一 seed 下產生完全相同的幾何量。

## P9 — 正式 54-run 矩陣

`output/exp6_formal_matrix/matrix_manifest.json` 記錄 9 工況 × seeds `{42,123,2026}` × methods `{mahalanobis,knn}`，共 54 個 run。每個 run 的 summary 僅保存 manifest 指定工況的一列，並以 atomic JSON、CSV、log 寫入；不完整或工況不符的舊 summary 不會被 resume 誤判為完成。實際執行結果為 `54/54 completed, 0 failed, 0 missing`，資料 fingerprint 全部一致。矩陣契約修正與 strict regression test 在 `ff49e3b`，三個 seed 的結果分別在 `6b9d935`、`2efae34`、`4babc9a`。

## P10 — 跨 seed 彙整與實際差異

`experiments/aggregate_exp6.py`（程式 commit `bfe9837`）僅接受完整且 fingerprint 一致的矩陣，輸出 `aggregate.json`、三個 CSV 與 `aggregate.md`，並計算每工況 mean±std 及同一工況/seed 的 paired difference。正式 27 對配對結果（9 工況 × 3 seeds）如下；完整 artifacts 隨 `4babc9a` 推送：

| 指標 | Mahalanobis mean±std | kNN mean±std | kNN − Mahalanobis |
|---|---:|---:|---:|
| known accuracy | 0.946214 ± 0.040142 | 0.945683 ± 0.043856 | −0.000531 |
| open-set accuracy | 0.998849 ± 0.000887 | 0.998842 ± 0.000937 | −0.000007 |
| AUROC | 1.000000 ± 0.000000 | 1.000000 ± 0.000000 | 0.000000 |
| unknown F1 | 0.999412 ± 0.000453 | 0.999409 ± 0.000478 | −0.000003 |

兩種方法在這份正式資料上 AUROC、AUPR、TPR95 對應 FPR 與 unknown recall 都完全相同；Mahalanobis 在 known accuracy、open-set accuracy、unknown F1 的平均值略高，但差距小於 0.06 個百分點。這表示目前資料的故障群與健康群在 105 維特徵空間中已高度可分，kNN 沒有提供額外排序收益；Mahalanobis 的全域 covariance whitening 在小幅 seed 波動下較穩定。這是資料與特徵的實驗結論，不宣稱可外推到尚未測試的資料分布。
