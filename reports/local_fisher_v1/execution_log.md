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

## 15:14結果檢查點

上述為評估前紀錄，現由以下實際證據更新。fit/source封存提交 `34f38380c411b72f55112eb9945a0a9738606df6` 並push、確認remote相同後才evaluate。實驗13最終交付提交 `0cd05288a204da39a4aac64cd89b91efaf7a481f`，亦已push／核對。完整環境新增診斷五測試後3.10.19及3.14.6各437通過，pip check及原37CLI均PASS，詳實驗13最新execution_log。

`evaluate --protocol output/fault_type_local_fisher_lock/2026-10-03-10-08-32/protocol.json --lock output/fault_type_local_fisher_fit/2026-10-03-10-15-15/locked_study.json --source-verification output/fault_type_local_fisher_source_verify/2026-10-03-10-17-52/source_verified.json --data-root data/formal_local` 完成144格、0失敗、1,387,680筆預測、28,910個unique samples。evaluation SHA `6db88bb6d5b8f43d302dace9f2680f52c73faa5fdc4a687bc84096f478d266ef`。

同入口verify加 `--evaluation D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/local_fisher_v1/workspace/output/fault_type_local_fisher_evaluate/2026-10-03-10-21-09/evaluation.json`，於 `2026-10-03-15-06-27` 全144格逐筆重推／truth mutation通過；verification SHA `bb78f9365f2d56e7f5e70c70e7a844e1c69682628c8422ed477e5e45337033b6`。90CSV前後checksum相同。

report加baseline=`output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json`、previous=`output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json`，保存 `output/fault_type_local_fisher_report/2026-10-03-15-09-03/summary.json.gz`。SHA `7a5c3019d4eeefd2abf710c4c385c3fe9eecba4a426f61c71c30cc596da32731`，全部16方法main_screen FAILED。F02 seed0 fault accuracy33.420%、比C17+2.989百分點，但healthy誤報18.947%、最弱類別0%；固定契約未通過。全部seeds及分層結果保留。

backup入口封存D槽fit/evaluate/verify三ZIP，28+290+2=320成員，整檔／成員SHA與CRC均PASS；索引 `output/fault_type_local_fisher_backup/2026-10-03-15-09-14`。另用既有archive封存C槽report、protocol、source證據；兩次CLI在同一秒產生同一output timestamp，source索引覆寫protocol索引，但原ZIP兩者保留。重試protocol被既有no-overwrite guard正確拒絕（15-14-00、退出1），未刪ZIP。將依現存ZIP整檔SHA／BUNDLE_INDEX恢復單一compact索引並再次全成員驗證，不改sealed protocol／模型。此問題只在交付索引，不影響科學結果；後續多root使用單次CLI，避免秒級timestamp碰撞。

本階段commit只stage本批報告、compact產物、logs、archive索引，不stage正式data／joblib／大型預測／282無關刪除。提交hash於後續研究檢查點記錄；正式default、PolarMap、factory k-NN全部未變。

恢復索引為 `reports/local_fisher_v1/recovered_archive_index.json`；連同另三索引，fixed_delivery於 `2026-10-03-15-14-54` 驗證6ZIP／324成員全部SHA／CRC PASS。沒有刪除或覆寫任何ZIP，既有parent依賴仍沿用原封存。
