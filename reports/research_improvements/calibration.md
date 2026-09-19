# P2 Calibration

# P2 Calibration

## 已實作

- `health.thresholds.independent_percentile`：獨立 healthy calibration 的 90%、95%、97.5%、99% 分位數。
- `health.thresholds.ConformalCalibrator`：有限樣本 p-value `p=(1+#(calibration_score >= score))/(n+1)`，inclusive ties，支援 alpha 0.01/0.05/0.10。
- `ConditionAwareCalibrator`：exact condition → 較粗 condition → global 的固定 fallback，並輸出使用的 scope。
- `AlarmPolicy`：single、N consecutive、K-of-N、ratio、hysteresis。
- `evaluate_alarm_series`：false alarms/hour、false-alarm events、event-level unknown recall、detection delay、lead time、alarm duration、flapping。

## 正式資料結果

執行命令：

```powershell
venv\Scripts\python.exe -m experiments.calibration_ablation `
  --data-root data/formal_local `
  --output-root reports/research_improvements/calibration_ablation
```

共 3 seeds（42、123、2026），每個 row 使用 P1 的 validation + immutable test；這些 labels 只在 fit 完成後計算離線指標。結果檔：`calibration_ablation/summary.json`，fingerprint `c7ff515470004aeb443ad3a263bb91a2b9c626026042ee8f65d3f6a44d284046`。

| covariance + calibration | healthy FPR | unknown recall | AUROC | false-alarm events | event recall |
|---|---:|---:|---:|---:|---:|
| legacy + legacy self-threshold | 1.000000 | 1.000000 | 0.725476 | 0 | 1.000000 |
| legacy + independent q=.95 | 0.000000 | 0.279315 | 0.725476 | 0 | 0.666667 |
| Ledoit–Wolf + independent q=.95 | 0.002257 | 0.617260 | 0.808037 | 2 | 0.666667 |
| legacy + conformal alpha=.05 | 0.000000 | 0.278630 | 0.725476 | 0 | 0.666667 |
| Ledoit–Wolf + conformal alpha=.05 | 0.002257 | 0.616438 | 0.808037 | 2 | 0.666667 |

Ledoit–Wolf 的獨立校準相較 legacy 的獨立校準提高 AUROC 約 0.0826、unknown recall 約 0.338，但健康 FPR 也由 0 降到約 0.00226；這是 covariance 與 calibration 控制後的比較，沒有把 legacy self-threshold 的 100% FPR 差距全部歸因於 covariance。q/alpha 越寬鬆，unknown recall 上升但 false-alarm events 也上升；本資料的 event recall 對多數 policy 為 2/3，不能只看 sample accuracy。

## 限制

目前正式資料沒有事件邊界、timestamp 或人工 alarm label；上表的 event 指標是依固定 split 順序進行的離線 replay，只支持 simulation/replay 結論。要報告真實警報延遲、每小時誤報與 early-warning lead time，仍需 P7 的現場 metadata。
