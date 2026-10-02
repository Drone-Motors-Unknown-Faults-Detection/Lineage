# fault_type_continuous_smoke 技術手冊

2026-10-02 補寫已有程式，文件不冒称在原實作之前登錄。後續更改先更新本文件。共同資料／motor roles／公式／固定參數見 [study 手冊](fault_type_continuous_study.md)。

## 實驗方法與 CLI

純 synthetic 八arm sanity：固定 fixture、subset seed0、同 registry parameters，測 transform/inference 決定論、metric 收斂與分類／拒絕分支分離。無真實 test、無資料 independent claim。

repo 根目錄執行：
```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_smoke
```

run(...) 與 main() 雙介面；setup_run 產生 logs/output。科學 Python3.10.19，相容測試3.14.6；所有旧資料已曝光，研究屬 exploratory。

## 參考與本地約定

Weinberger & Saul（2009），Distance Metric Learning for Large Margin Nearest Neighbor Classification，JMLR，https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf；本地對角改編詳 study。synthetic sanity 是工程約定。

## 預期與實測分開

八arms deterministic 且 matched branch 相符為工程 PASS；失敗則拒絕進正式研究。兩 runtime 先前均 PASS，不能算新 motor 的準確率。

預期不保證提高分數；缺失 motor/session/window 證據保留 UNKNOWN，每類至少兩個獨立test groups 的原 guard 不放寬。B/C 的門檻見封存 reliability_contract，程式能執行不能當模型可靠。

## 影響程式碼範圍

experiments/fault_type_continuous_smoke.py、core/fault_type_continuous.py、core/openset.py、experiments/fault_type_mechanism_smoke.py。本次補文件未更改 scientific code 或正式資料。
