# fault_type_continuous_inventory 技術手冊

2026-10-02 補寫已有程式，文件不冒称在原實作之前登錄。後續更改先更新本文件。共同資料／motor roles／公式／固定參數見 [study 手冊](fault_type_continuous_study.md)。

## 實驗方法與 CLI

唯讀核對兩份 parent result index、artifact/model SHA、fit audits 與正式來源 fingerprint，記錄套件／磁碟。pip freeze 失敗保留實際 exit/error，pip list 僅作版本快照，不稱完整 lock。不訓練、不抽新 split。

repo 根目錄執行：
```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_inventory --data-root data/formal_local
```

run(...) 與 main() 雙介面；setup_run 產生 logs/output。科學 Python3.10.19，相容測試3.14.6；所有旧資料已曝光，研究屬 exploratory。

## 參考與本地約定

檔案盤點、版本快照與 SHA 是本地操作約定，無新預測算法；父方法來源與閱讀深度見 ../../reports/continuous_research/source_ledger.md。

## 預期與實測分開

來源 hash 不一致拒絕；來源不變、可追溯盤點支持工程接續。41 artifact SHA、9 model 與234 audits 是本次已存 inventory 的核對數，非新試驗數。

預期不保證提高分數；缺失 motor/session/window 證據保留 UNKNOWN，每類至少兩個獨立test groups 的原 guard 不放寬。B/C 的門檻見封存 reliability_contract，程式能執行不能當模型可靠。

## 影響程式碼範圍

experiments/fault_type_continuous_inventory.py、core/formal_data.py、core/fault_type_features.py、experiments/fault_type_fixed_calibration.py。本次補文件未更改 scientific code 或正式資料。
