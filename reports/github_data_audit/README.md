# GitHub data audit — Lineage formal data contract

本報告是 GitHub 帳號／組織資料調查的 P0/P1 紀錄。這一階段只定義 Lineage 所需資料與安全推送狀態，不修改 Open Set 演算法、不執行 54 組正式實驗，也不把大型資料搬入 repository。

## P0：本機 Lineage 與推送目標

| 項目 | 結果 |
|---|---|
| Repository | `https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage.git` |
| 原始本機路徑 | `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\Lineage` |
| 原始目前 branch | `feat/knn-openset-comparison` |
| 原始目前 HEAD | `a28763c0c968d317b15305a54f8a3ed4829d6fbe` |
| 原始 upstream | 未設定 |
| 遠端 | `origin` → Lineage organization repository |
| 本任務推送 branch | `feat/knn-openset-comparison`（已由前一階段在遠端建立同名 branch） |
| 原有未提交檔案 | `core/openset.py`，未修改、未 stage、未提交 |
| 原始工作樹 | 不乾淨，只有上述一個未追蹤檔案 |
| 原始 HEAD push dry-run | `non-fast-forward`；遠端同名 branch 較新，沒有覆蓋遠端歷史 |

本次調查使用與遠端 branch HEAD 對齊的隔離工作樹，避免同步或產生報告時覆蓋原始 `core/openset.py`。P0 不建立空 commit；資料契約完成後才建立 P1 commit。

## P1：Lineage 資料契約

### 證據鏈

目前任務 branch（遠端 `feat/knn-openset-comparison`，commit `dd0190f7f4de7f3f624292cd32a98d12e413b4e1`）的 loader 與比較程式，及最新 `main` branch 的 exp4/exp5/exp6 程式，共同定義下列需求。branch 之間若內容不同，後續 inventory 會保留 branch-to-commit 對應，不會因相同或相近內容省略 branch。

| 項目 | Lineage 需要的內容 | 證據檔案與行號 |
|---|---|---|
| 資料根目錄 | CLI `--data-root`；預設 `data`，不可依賴電腦絕對路徑 | `core/runner.py:18-24,51-59`；main 的 `experiments/exp6_osr_benchmark.py` |
| 預期路徑 | `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv` | `core/data.py:1-5,54-66`；`AGENT.md:49-50` |
| 檔案格式 | clean CSV；每個 screw configuration 一個檔案 | `core/data.py:68-87` |
| 特徵維度 | 105 個數值 feature，最後一欄為 label | `core/data.py:17-18,76-83`；`README.md:298` |
| 必要健康類 | `8screws`，作為健康基準 | `core/data.py:17,86-87`；`README.md:194-198` |
| 其他 class | `1screws`/`1screw`、`2screws`、`3screws`、`4screws`、`5screws`、`6screws`、`7screws`、`3_14screws`、`4_146screws`；實際 loader 以資料目錄與檔案為準 | `README.md:194-198`；`core/data.py:68-87` |
| 正式工況 | 9 組：T1/T2/T3 × 6000/8000/11000 rpm；loader 不硬編碼名稱，而掃描實際 `Step-*` 目錄 | `Ancestor/README.md` data section；`core/data.py:54-66` |
| Known / unknown | 正式 OSR 需從相同資料契約明確分配 known 與 unknown；目前比較工具以 `8screws` holdout 作 known、其他 configuration 作 unknown | `experiments/compare_openset.py:53-90`；`Ancestor/docs/Step4_Unknown_Detection.md` |
| Split | 每個 class 的 train/calibration/holdout = 60/20/20；索引互斥 | `core/data.py:91-104`；`core/monitor.py:45-71` |
| Normalization | RobustScaler fit 在 training split，之後同一 scaler transform calibration/holdout/test | `core/monitor.py:45-84`；`core/openset.py:14-18` |
| Mahalanobis | factory 預設 `mahalanobis`；class-conditional covariance，threshold 由 known calibration quantile 決定 | `core/openset.py:179-195`；`core/monitor.py:82-90,138-145` |
| k-NN | factory 可切換 `knn`；reference bank 只用 training split，k 預設 5，calibration 只用 known class | `core/openset.py:72-177` |
| Threshold | normalized score `> 1` 判 unknown；分數越大越 unknown；test/unknown 不得參與 threshold | `core/openset.py:14-18,75-78`；`experiments/compare_openset.py:3-4,146-149` |
| PolarMap | 在目前 task branch 的 tree 尚未存在；最新 `main` 才有 geometry/exp4，後續 branch inventory 會分別記錄 | feature branch tree；latest `main` `core/geometry.py` / `experiments/exp4_polar_map.py` |
| exp6 | 目前 task branch tree 尚未存在；最新 `main` 有 `experiments/exp6_osr_benchmark.py`，後續逐 branch inventory 會確認 | feature branch tree；latest `main` exp6 |
| Checkpoint | 目前 Lineage data loader / OSR code 不以 checkpoint 讀取資料；若候選 repository 只有 checkpoint，分類為 `E_CHECKPOINT_ONLY` | `core/data.py`、`experiments/compare_openset.py` |
| Raw data | 正式 Open Set 比較需要 processed 105 維 clean features；raw 10 kHz waveform 只是 Ancestor preprocessing input，不能冒充已可直接跑 exp6 的資料 | `AGENT.md:49-50`；`Ancestor/docs/Step2_Feature_Extraction.md` |
| PolarMap 額外資料 | 最新 main 的 PolarMap 需要同一 monitor 的白化特徵、class directions 與 calibration holdout；不另創資料來源 | latest main `core/geometry.py`、`experiments/exp4_polar_map.py` |

### 資料必要性分級

- **必要**：每個正式工況的 105 維 `*_Group_feature_data_clean.csv`，至少包含 `8screws` 與所有 OSR 需要的故障 configuration。
- **必要 metadata**：資料來源 repository、branch、commit SHA、檔案清單、大小／checksum 或穩定 fingerprint、label mapping、split policy。
- **可選**：raw waveform、未過濾 `*_Group_feature_data.csv`、模型 checkpoint；它們不能在缺少 clean features 時被宣稱可直接供 exp6 使用。
- **不可接受替代品**：synthetic、toy、demo、debug subset、只有 LFS/DVC pointer、只有 checkpoint、只有 README 範例。

### 目前 branch 的重要差異

任務 branch 的 k-NN factory 與 `compare_openset.py` 已存在，但它的 tree 沒有 `PolarMap`、`exp5_cross_condition.py` 或 `exp6_osr_benchmark.py`；最新 `main` 已包含這些功能。完整 GitHub audit 必須把兩個 branch 都列出，不把其中一個 branch 的檔案誤當成另一個 branch 已存在。

## P1 驗收

- 已閱讀 Lineage 的 AGENT/README、loader、monitor、Mahalanobis、Open Set factory、CLI、comparison experiment、gitignore 與測試入口。
- 已列出 path、format、features、labels、9 conditions、known/unknown、split、normalization、threshold、factory、PolarMap/exp6 branch 差異。
- 尚未判定 GitHub 上哪一份資料是正式來源；那是 P2–P4 的調查工作。

## 可恢復進度

機器可讀進度見 [progress.json](progress.json)。P2 起將建立 repository、branch、file、candidate inventory；每完成一個 repository 便更新、檢查、commit、push，再處理下一個。

## P3 repository audit — Ancestor

第一個依字典序處理的 repository 是 `Drone-Motors-Unknown-Faults-Detection/Ancestor`。已使用 GitHub API 取得所有 branch，並在 recursive tree 沒有截斷的情況下記錄完整 file entries；兩個 branch 即使內容有重疊，仍分別保留：

| Branch | HEAD | Tree mode | File entries | LFS/DVC | Audit status |
|---|---|---|---:|---|---|
| `main` | `1ef4a891ae02dc95910f747a5163bb2edd608f28` | recursive | 1334 | 0 / 0 | completed |
| `original` | `2708e0d31d7904aa38af8d08b9950d91b5f9c7c7` | recursive | 152 | 0 / 0 | completed |

Ancestor 的完整分支與檔案 inventory 位於：

- [repository metadata](repositories/Drone-Motors-Unknown-Faults-Detection__Ancestor/repository.json)
- [branch audit](repositories/Drone-Motors-Unknown-Faults-Detection__Ancestor/branches.json)
- [branch inventory](branch_inventory.csv)
- [file inventory](file_inventory.csv)

兩個 branch 的 tree 都沒有實際 `data/`、`*_Group_feature_data_clean.csv`、archive、LFS pointer、DVC metadata 或 checkpoint data object。README／docs 只描述資料應放在 `data/Step-*`，因此目前分類是「referenced-but-missing」，不是正式資料候選。

## P3 repository audit — GPU-Learning-PyTorch

`Drone-Motors-Unknown-Faults-Detection/GPU-Learning-PyTorch` 是 public、MIT、非 fork、非 archived repository。API 回報只有一個 branch；該 branch 的 recursive tree 沒有截斷：

| Branch | HEAD | Tree mode | File entries | LFS/DVC | Audit status |
|---|---|---|---:|---|---|
| `main` | `156de327373017df07e7feb4c4dd8664d70cc98a` | recursive | 66 | 0 / 0 | completed |

完整檔案 inventory 已加入 [file_inventory.csv](file_inventory.csv)，repository metadata 與 branch audit 位於 `repositories/Drone-Motors-Unknown-Faults-Detection__GPU-Learning-PyTorch/` 的同名檔案。此 repository 只有 GPU/CUDA 設定、MNIST/CIFAR 訓練程式、log 與文件；找到的外部 URL 是 PyTorch wheel index，沒有馬達資料、105 維 clean features、9 工況或 checkpoint 可對應 Lineage。

因此此 repository 分類為 `F_IRRELEVANT`；外部下載 URL 僅記為 `D_POINTER_EXTERNAL`，不視為正式資料。

## P3 repository audit — GPU-Learning-Tensorflow

`Drone-Motors-Unknown-Faults-Detection/GPU-Learning-Tensorflow` 是 public、MIT、非 fork、非 archived repository。API 回報只有一個 branch，recursive tree 沒有截斷：

| Branch | HEAD | Tree mode | File entries | LFS/DVC | Audit status |
|---|---|---|---:|---|---|
| `main` | `c16c5e839914379af4005bef1c681a6cf9da6054` | recursive | 51 | 0 / 0 | completed |

此 repository 的檔案是 TensorFlow/CUDA 設定、MNIST/CIFAR 訓練程式、log、報告與文件；沒有 `data/Step-*`、馬達特徵 CSV、9 工況 label、LFS/DVC pointer 或可對應 Lineage 的 checkpoint。分類為 `F_IRRELEVANT`。

## P3 repository audit — Lineage

`Drone-Motors-Unknown-Faults-Detection/Lineage` 是 public、非 fork、非 archived repository。這次掃描以以下三個 branch HEAD 作為不可變的稽核邊界；稽核報告本身是在掃描後才提交回 feature branch，因此不能把稽核產物誤算成原始資料：

| Branch | HEAD | Tree mode | File entries | LFS/DVC | Audit status |
|---|---|---|---:|---|---|
| `backup_260806` | `3a699ab81c16503fff4ba2c2b8ec566202c24d7d` | recursive | 1339 | 0 / 0 | completed |
| `feat/knn-openset-comparison` | `1a48f22575270e6ea3ca36a4ec9979282d857957` | recursive | 158 | 0 / 0 | completed |
| `main` | `afcfcc419dab3103a86a8f95601d3af85890eb38` | recursive | 179 | 0 / 0 | completed |

三個 branch 都完成 recursive tree 掃描，沒有截斷；分支內也沒有真正的 `data/`、`*_Group_feature_data_clean.csv`、壓縮資料集、HDF5/NPZ/Parquet、checkpoint data object、LFS pointer 或 DVC metadata。`main` 的 `exp6_osr_benchmark` 與少量 `output/**/results.csv` 是程式碼／實驗結果，不是可重新載入的正式資料集；feature branch 的 k-NN 比較結果同樣是衍生輸出。`reports/github_data_audit/audit_one_repo.ps1` 裡出現的 Git LFS 文件網址是稽核工具字串，不是 LFS pointer；檔案內容偵測結果為 `lfs_detected=false`。

Lineage 候選 inventory 共記錄 43 筆：27 筆 `B_PROCESSED_DERIVED`（實驗結果或稽核報表）、12 筆 `C_SAMPLE_DEBUG`（web server sample）、4 筆 `D_POINTER_EXTERNAL`（PyTorch wheel／工具網址）。這些候選都沒有同時滿足正式資料的九項條件，因此不能把任何一筆宣稱為正式資料來源。

完整資料位於：

- [Lineage repository metadata](repositories/Drone-Motors-Unknown-Faults-Detection__Lineage/repository.json)
- [Lineage branch audit](repositories/Drone-Motors-Unknown-Faults-Detection__Lineage/branches.json)
- [organization inventory](account_inventory.json)
- [branch inventory](branch_inventory.csv)
- [file inventory](file_inventory.csv)
- [candidate inventory](data_candidates.csv)

## P4 candidate verification and final result

### 結論

目前 GitHub 組織可存取的四個 repository（Ancestor、Lineage、GPU-Learning-PyTorch、GPU-Learning-Tensorflow）中，**找不到可直接供 Lineage 正式 Open Set 實驗使用的資料集**。特別是沒有發現符合 `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv`、105 維特徵、`8screws` 健康類、9 組正式工況、known/unknown 可分配、60/20/20 split、可追溯來源與可重現讀取方式的完整物件。

### 整體完整性檢查

- Repository：`completed + inaccessible + failed = 4 + 0 + 0 = 4`。
- Branch：`completed + inaccessible + failed = 7 + 0 + 0 = 7`。
- Branch HEAD SHA 去重後為 7，與七個 branch 一一對應。
- Recursive tree file entries：Ancestor 1486、GPU-Learning-PyTorch 66、GPU-Learning-Tensorflow 51、Lineage 1676，共 3279 筆 branch-path entries；去重後 blob/tree SHA 共 1784 筆。
- LFS pointer、DVC metadata、submodule、release、workflow artifact、fork：四個 repository 均未發現（各項數量為 0）。

### 對後續實驗的含義

這次 audit 沒有修改 Mahalanobis、k-NN、PolarMap 或其他 Open Set 演算法，也沒有執行需要正式資料的 54 組實驗。要開始正式 benchmark，仍需由團隊提供或重新掛載符合上述契約的資料來源；在那之前，repository 內的 output CSV 只能作為歷史結果參考，不能當作正式訓練／校準／holdout data。

機器可讀狀態見 [progress.json](progress.json)。此 audit 的 `final_status` 為 `completed`，但「正式資料來源」的結果是 **not found**，不是資料已存在。
