# fault_type_continuous_report_v2 技術手冊

2026-10-02 補寫已有程式，文件不冒称在原實作之前登錄。後續更改先更新本文件。共同資料／motor roles／公式／固定參數見 [study 手冊](fault_type_continuous_study.md)。

## 實驗方法與 CLI

修正 partial-method 報告：缺 fold 不產完整均值，per-fold delta 與相同fold/seed/test IDs對照。由 saved predictions 重算 metrics，保留 failures，綁 reporter SHA；不改 sealed scientific code／params／threshold。

repo 根目錄執行：
```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_report_v2 --protocol output/fault_type_continuous_registry/2026-10-02-18-40-41/protocol.json --evaluation output/fault_type_continuous_evaluate/2026-10-02-18-47-45/evaluation.json --verification VERIFIED_JSON --baseline output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json --previous output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json
```

run(...) 與 main() 雙介面；setup_run 產生 logs/output。科學 Python3.10.19，相容測試3.14.6；所有旧資料已曝光，研究屬 exploratory。

## 參考與本地約定

此 v2 為本地報表工程修補，配對差異／零分母／互斥警報是明確操作定義。方法與文獻作者資料詳見 fault_type_continuous_study.md；未改原演算法。

## 預期與實測分開

VERIFIED_JSON 替換為 study verify 的實際 verified.json 路徑。數值須與 saved predictions 完全相符，缺格 INCOMPLETE。輸出 summary/json.gz、tradeoff.csv、result_index；不輸出部署 winner。未達 health/unknown/class gates 記 FAILED；來源未知不可得 C。

預期不保證提高分數；缺失 motor/session/window 證據保留 UNKNOWN，每類至少兩個獨立test groups 的原 guard 不放寬。B/C 的門檻見封存 reliability_contract，程式能執行不能當模型可靠。

## 影響程式碼範圍

experiments/fault_type_continuous_report_v2.py、core/fault_type_reliability.py、experiments/fault_type_mechanism_report.py、core/fault_type_metrics_v2.py。本次補文件未更改 scientific code 或正式資料。
