# Q 重現與續跑

從 result_index.json 的 repo 進入工作目錄；科學環境 .venv310 Python3.10.19/sklearn1.7.2，不能跨runtime讀joblib。既有 protocol/lock SHA不可改。手冊 docs/experiments/fault_type_continuous_study.md 說明fit/evaluate/verify；已完成階段不需重訓。formal CSV與父模型依賴需由parent indices定位；D備份不含raw或formal data。

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_study verify --protocol output/fault_type_continuous_registry/2026-10-02-18-40-41/protocol.json --data-root data/formal_local --lock output/fault_type_continuous_fit/2026-10-02-18-42-53/locked_study.json --evaluation output/fault_type_continuous_evaluate/2026-10-02-18-47-45/evaluation.json
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_report_v2 --protocol output/fault_type_continuous_registry/2026-10-02-18-40-41/protocol.json --evaluation output/fault_type_continuous_evaluate/2026-10-02-18-47-45/evaluation.json --verification output/fault_type_continuous_verify/2026-10-02-23-26-52/verified.json --baseline output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json --previous output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json
.\.venv310\Scripts\python.exe -m experiments.fault_type_continuous_acceptance
.\venv\Scripts\python.exe -m experiments.fault_type_continuous_acceptance
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_delivery --index output/fault_type_archive/2026-10-02-23-36-18/archive_index.json
```

setup_run建立新timestamp；不覆蓋既有artifact。不將reinference當新增實驗，不在未知test上調參。備份確認完保留原檔；8 ZIP的whole/member SHA與CRC在索引/verification。源程式、predictions或parent缺失即拒絕，不能靜默降級驗證。
