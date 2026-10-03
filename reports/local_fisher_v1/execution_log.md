# 實驗14執行紀錄

2026-10-03，Asia/Taipei。工作樹／branch與實驗13相同；保留282個無關刪除。

| 階段 | 已完成證據 | commit／push |
|---|---|---|
| 手冊／程式 | 先手冊；15新測試於Python3.10.19與3.14.6各通過；smoke僅工程 | `e836a2a70c85bfbe1c61aef268d519592aa391d0`，remote一致 |
| protocol | 16方法、144格；固定10/20維、ridge與7鄰居；無selector | `e7aa28f319eac8a74fcefec6463812ea5331d954`，remote一致；提交後才fit |
| 完整回歸 | 3.10.19：432通過，176.342秒；3.14.6：432通過，173.813秒；pip check及原37 CLI均PASS；新增CLI兩環境--help另查PASS | output接受摘要參照實驗13同日紀錄 |
| fit | `fit --protocol output/fault_type_local_fisher_lock/2026-10-03-10-08-32/protocol.json --data-root data/formal_local`；九bundle×四projection全部成功，0缺失 | 本階段封存lock，不含大型joblib |
| source-verify | 同入口`source-verify --protocol ... --lock output/fault_type_local_fisher_fit/2026-10-03-10-15-15/locked_study.json --data-root data/formal_local`；九bundle重建四projection、classifier與factory參考／calibration，全部精確相符；test_numeric_reads=0 | 本階段封存source_verified |

協定SHA `3423a82e3ee76f7590902b1d0c091fb17c6b39d9407ad736f0285fd6e1489db4`。fit source主路徑 `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/local_fisher_v1/workspace/output/fault_type_local_fisher_fit/2026-10-03-10-15-15`；C槽compact lock及artifact_location位於標準output。source證據 `output/fault_type_local_fisher_source_verify/2026-10-03-10-17-52/source_verified.json`。兩環境完整接受摘要為 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-10-06-22/environment.json` 與 `output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-10-10-56/environment.json`。

目前未讀本批test進行評估、未取得LFDA accuracy；不把eigendecomposition／來源重建成功稱為可靠模型。下一步在fit／source證據commit+push後執行evaluate、verify、report及backup。formal fingerprint不變，raw獨立性UNKNOWN；歷史曝露／final guard INCOMPLETE保留。無selected winner。
