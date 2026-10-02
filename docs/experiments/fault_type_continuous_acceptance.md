# fault_type_continuous_acceptance 技術手冊

2026-10-02 補寫已有程式，文件不冒称在原實作之前登錄。後續更改先更新本文件。共同資料／motor roles／公式／固定參數見 [study 手冊](fault_type_continuous_study.md)。

## 實驗方法與 CLI

呼叫既有 acceptance，跑全套 unittest、pip check、CLI help，附 Python/環境/exit codes 到 setup_run output。原正式105/LW/k-NN/PolarMap regression 保留。不跨環境載入 joblib；不重新訓練科學矩陣。

repo 根目錄執行：
```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_acceptance
```

run(...) 與 main() 雙介面；setup_run 產生 logs/output。科學 Python3.10.19，相容測試3.14.6；所有旧資料已曝光，研究屬 exploratory。

## 參考與本地約定

acceptance 流程、native runtime 和 CLI檢查是本地工程約定，沒有引用論文提出新模型；方法原始出處見 fault_type_continuous_study.md。

## 預期與實測分開

各命令 exit0才工程 PASS。實際 passed數由當次 artifact 記錄；先前376不能當加入新tests後的數量。2026-10-02後續先改本手冊，再新增report_v2及solver_diagnosis的CLI help；全tests也包含train-only solver數值/用途/失敗checkpoint測試。之前的34help/378tests仍為獨立舊驗收紀錄。

27train fits完成後，先補本手冊再納入solver_report CLI與4個保存數值重算測試；最後验收應包含新report，不借用392當新數字。

預期不保證提高分數；缺失 motor/session/window 證據保留 UNKNOWN，每類至少兩個獨立test groups 的原 guard 不放寬。B/C 的門檻見封存 reliability_contract，程式能執行不能當模型可靠。

## 影響程式碼範圍

experiments/fault_type_continuous_acceptance.py、experiments/fault_type_mechanism_acceptance.py、tests/。本次補文件未更改 scientific code 或正式資料。
