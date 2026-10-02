# fault_type_continuous_report 技術手冊

2026-10-02 補寫已有程式，文件不冒称在原實作之前登錄。後續更改先更新本文件。共同資料／motor roles／公式／固定參數見 [study 手冊](fault_type_continuous_study.md)。

## 實驗方法與 CLI

sealed Q_v1 原報表程式，保留原 SHA。只重算逐樣本產物／配對摘要，不訓練或挑 winner。它假設每方法9runs；遇 Q02/Q04 缺 fold 的情況不能完整報告，現行請用 report_v2。

repo 根目錄執行：
```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_report --help
```

run(...) 與 main() 雙介面；setup_run 產生 logs/output。科學 Python3.10.19，相容測試3.14.6；所有旧資料已曝光，研究屬 exploratory。

## 參考與本地約定

配對 IDs、缺失處理與描述性匯總為本專案約定，沒有新增分類算法；方法文獻見 fault_type_continuous_study.md。

## 預期與實測分開

預期全覆蓋時可彙整；partial 方法暴露原假設缺陷。沒有用此程式發布 Q 成績，不將缺 fold 均值冒充完整結果。help 僅查接口，實際報告使用 v2。

預期不保證提高分數；缺失 motor/session/window 證據保留 UNKNOWN，每類至少兩個獨立test groups 的原 guard 不放寬。B/C 的門檻見封存 reliability_contract，程式能執行不能當模型可靠。

## 影響程式碼範圍

experiments/fault_type_continuous_report.py、core/fault_type_reliability.py、experiments/fault_type_mechanism_report.py。本次補文件未更改 scientific code 或正式資料。
