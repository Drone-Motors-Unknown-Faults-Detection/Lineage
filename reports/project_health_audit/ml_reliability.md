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
