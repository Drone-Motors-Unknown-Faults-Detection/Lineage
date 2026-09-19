# ML／實驗可靠度基線

## 已被目前程式與測試支持的契約

- formal exp6 將 `8screws` 當 known health，其餘配置作 unknown positive；threshold 只由 known train/calibration split 的 quantile 取得，unknown/test 只在 scoring 後計算 metrics。
- Mahalanobis 與 k-NN 都在相同 `RobustScaler`（只 fit training split）、相同 60/20/20 split、相同 seed 與同一個 detector factory 下比較；score direction 統一為「越大越 unknown」，`score > 1` 才 reject。
- exp6 結果保存 dataset fingerprint、commit SHA、Python version、method、split、threshold strategy、每工況的 train/calibration/known/unknown 樣本數與 metrics。
- k-NN 對每一類獨立建立 reference bank，`effective_neighbors = min(k, n_train)`；空輸入、單樣本與 invalid input 有單元測試。
- PolarMap 明確以 Mahalanobis 幾何為基底；切換展示用 Open Set method 不會改變其幾何，已有 regression test。

## 本基線仍需查證的可靠度面向

| 面向 | 目前證據 | 稽核狀態 |
|---|---|---|
| 9 工況 discover／duplicate | exp6 會檢查數量與 duplicate pair | 需補 class／檔案層級 schema 檢查 |
| 缺檔／缺 class | loader 會忽略沒有 clean CSV 的 config，最後只強制 health 存在 | 已列為資料可靠度候選 finding |
| channel window 對齊 | stage2 converter 取所有 channel 寬度最小值 | 已列為需明確政策與測試 |
| dataset fingerprint | 有 manifest 時使用 archive／file hash；無 manifest 時使用 size + mtime | 已列為 fallback 證據強度風險 |
| exp1–3 reproducibility | seed、method、split 有保存，但舊 summary 缺完整 fingerprint／環境欄位 | 已列為可重現性 finding |
| failed run／resume | matrix 有 status 與 resume；`_is_complete` 目前只驗 summary | 已列為結果可信度候選 finding |
| leakage／test threshold | 目前 exp6 code path 未發現 unknown 參與 threshold 的證據 | 不列為 bug；保留 regression test roadmap |

## 評估原則

本稽核不因正式結果漂亮就推論方法正確，也不因未覆蓋就宣稱 leakage。只有能以程式碼、測試、現有 artifact 或可安全重現命令支持的項目才會進入 `findings.csv`；其餘標記為「需驗證」並交給 roadmap 的測試任務。

## 正確性／資料可信度 findings

### DATA-001：loader 沒有完整 formal schema fail-fast

`core.data.discover_datasets()`（54–65 行）只要找到任一 clean CSV 就列出工況；`load_pools()`（68–88 行）會跳過缺檔 config，將 DataFrame 只保留 numeric columns，最後只檢查 105 維與健康類存在。現有 formal manifest 實際有 9 工況、10 config、90 個 105 維檔案，因此「目前資料正確」不等於「loader 會拒絕部分資料」。這是 P1 的資料完整性風險，建議在 exp6 入口加入 exact contract validator。

### DATA-002：Stage-2 channel 寬度採最小值靜默截斷

`core.formal_data._convert_condition()`（337–353 行）使用 `min(widths.values())` 後切片；既有 raw audit（`reports/ancester_openset_exp6_progress.md:163`）記錄 channel 寬度跨檔為 568–600。這不代表目前結果錯誤，但表示資料對齊政策是隱含的；應在 manifest 寫出原始寬度與截斷數，或改成 mismatch fail-fast，並由資料擁有者決定。

### EXP-002：resume 只驗 summary

`experiments.exp6_matrix._is_complete()`（77–100 行）會驗 summary 的狀態、seed、method、工況與 fingerprint，但沒有驗 `results.csv`、`run.log` 是否存在或符合 schema。matrix 本身已能把 incomplete 狀態以非零退出（222–249 行），因此本 finding 是「證據檔案完整性」而不是已完成的 exit-code 問題。

### REPRO-001：exp1–3 metadata 未達 exp6 追溯標準

exp6 summary 有 fingerprint／commit／Python／config；相對地，既有 exp1–3 summary 只保存 motor/rpm、seed、method 與指標。這是可重現性缺口，不是模型指標計算已被證明錯誤。實作時應先建立共同 metadata schema，再逐一補入歷史實驗。

### REPRO-002：exp6 尚未保存完整軟硬體環境

目前 `experiments.exp6_osr_benchmark.run()`（239–267 行）保存 Python 與 commit，但沒有 package version、OS／CPU／GPU／CUDA 或完整 resolved CLI config。這不否定現有 54-run 結果，只表示結果 artifact 還不能完整回答「在哪個數值環境重現」；應用 portable metadata 補強，未知硬體欄位要明確標成 unavailable。
