# fault_type_continuous_registry 技術手冊

2026-10-02 補寫已有程式，文件不冒称在原實作之前登錄。後續更改先更新本文件。共同資料／motor roles／公式／固定參數見 [study 手冊](fault_type_continuous_study.md)。

## 實驗方法與 CLI

固定 Q01–Q08、三fold、seeds0/1/2，共72 planned。綁 parent manifests、資料、code/來源卡 SHA、reliability contract；validation/selection 空，沒有 winner。先 commit/push protocol 才 fit；參數與文獻見 study 手冊。

repo 根目錄執行：
```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_registry --index reports/literature_expansion/result_index.json
```

run(...) 與 main() 雙介面；setup_run 產生 logs/output。科學 Python3.10.19，相容測試3.14.6；所有旧資料已曝光，研究屬 exploratory。

## 參考與本地約定

Weinberger & Saul（2009），Distance Metric Learning for Large Margin Nearest Neighbor Classification，JMLR10:207–244，https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf。本地 diagonal/mean/ridge 改編與 gain 表示詳見 study；封存與 no-selection 是本地操作約定。

## 預期與實測分開

任何 arms/params/environment/source SHA 變更拒絕；預期可重現同 protocol。已有 protocol b7870298… 封存；不重新生成覆蓋舊版，也不因較高 test score 變更規則。

預期不保證提高分數；缺失 motor/session/window 證據保留 UNKNOWN，每類至少兩個獨立test groups 的原 guard 不放寬。B/C 的門檻見封存 reliability_contract，程式能執行不能當模型可靠。

## 影響程式碼範圍

experiments/fault_type_continuous_registry.py、core/fault_type_reliability.py、experiments/fault_type_mechanism_registry.py。本次補文件未更改 scientific code 或正式資料。
