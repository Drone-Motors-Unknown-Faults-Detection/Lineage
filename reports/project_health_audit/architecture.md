# 架構與 repository map

## Repository map

| 區域 | 內容 | 主要入口 |
|---|---|---|
| `core/` | 資料載入、正式資料 materialization、Mahalanobis、Open Set factory、monitor、trend、logger | `core.formal_data`、`core.openset` |
| `experiments/` | exp1 冷啟動、exp2 量尺擴張、exp3 trend、Open Set comparison、exp6 single/matrix/aggregate | 各模組的 `main()` |
| `web/` | Tornado WebSocket 展示、LiveDemo 與前端靜態資源 | `web.server`、`run_web.sh` |
| `tests/` | unittest：formal data、factory、Mahalanobis、k-NN、PolarMap、exp6 aggregate/matrix | `python -m unittest discover -s tests -v` |
| `docs/` | Ancestor 論文版文件與 Lineage 研究文件索引 | `docs/README.md` |
| `reports/` | GitHub／資料稽核、exp6 進度與結果說明 | `reports/ancester_openset_exp6_progress.md` 等 |
| `data/` | 由 `.gitignore`／外部正式資料提供的 Step-1/2/3 結構；目前 worktree 無追蹤 raw data | `core.data`、`core.formal_data` |
| `output/`、`logs/` | 產生的實驗輸出與日誌，非 source of truth | `core.logger`、exp6 writers |
| `pyproject.toml` | package metadata 與 runtime dependencies | Python 3.10.19 宣告 |
| `build_uv*.sh` | uv 環境建立腳本 | Linux/macOS 導向 |

## 主要資料與實驗流

```text
formal raw archives (read-only)
  → core.formal_data (Step-1/2/3 materialization + manifest)
  → data/Step-*/myfeature/{motor}/{rpm}/{config}/*.csv
  → core.data.discover_datasets / load_pools
  → 60/20/20 known split + RobustScaler (fit on train only)
  → core.openset factory
       ├─ Mahalanobis (class covariance + calibration quantile)
       └─ k-NN (class reference bank + calibration quantile)
  → normalized score (higher = unknown, >1 = reject)
  → metrics / CSV / JSON / plots / aggregate
```

Exp1 只用健康 class 起始；exp2 在操作員確認後將新 class 納入重新擬合；exp3 以相同 monitor 分數做 EWMA/CUSUM trend；exp6 將 9 個 motor×rpm 條件、3 seeds、2 detector methods 交給 matrix runner，完成後由 aggregate 產生 paired summary。

## 已確認的邊界與優點

- `core.openset.create_openset_detector()` 是 Mahalanobis／k-NN 的共用建立入口；exp6 目前直接使用它，測試已鎖定 factory default、alias 與 PolarMap 固定 Mahalanobis 基底。
- formal exp6 已保存 schema version、dataset fingerprint、commit SHA、split／threshold／score direction、每條件的 metrics 與 portable root label。
- raw source 與 materialized output 有 containment 檢查；Step-1/3 的 archive member 有相對路徑檢查；來源 manifest 紀錄 archive/file hash。
- matrix CLI 目前對 `incomplete` 回傳非零（`experiments/exp6_matrix.py:222-249`），故不把已修正項目重複列為 finding。

## 維護性觀察與已確認 findings

1. **ARCH-001（P1）**：`core.runner` 對 exp1–3/Web 有共用 CLI helper，但 exp6 自有 parser，結果 metadata schema 也不同；缺少單一 resolved-config/result contract。
2. **ARCH-002（P2）**：`exp6_osr_benchmark.run()`、`exp6_matrix.run_matrix()`、`web.live.tick()` 分別約 131、110、79 行，同時處理 orchestration、狀態更新與輸出副作用；不是已證明的數值 bug，但會提高失敗路徑測試成本。
3. **ARCH-003（P2）**：`OpenSetMonitor.score/classify/project`（102–113 行）沒有 fitted-state guard；錯誤可讀性不足，適合以小型 API contract test 先修補。
4. `core.data.load_pools()`、formal materialization、Web dataset reload 各自承擔部分資料 schema 假設；DATA-001 已將這件事提升為資料可靠度 finding。
5. `pyproject.toml`、`build_uv.sh`、`build_uv_mac.sh` 與目前 Windows 3.12 venv 的支援宣告不一致；ENV-001 已將環境問題提升為 finding。

ARCH-001～003 已加入 `findings.csv`；後續 roadmap 會把共用 metadata、API guard、CI 與大型函式拆分成不同 PR-sized 任務，避免「重構整個專案」這種不可驗收的工作。
