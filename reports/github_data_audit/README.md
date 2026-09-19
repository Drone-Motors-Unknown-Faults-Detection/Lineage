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
