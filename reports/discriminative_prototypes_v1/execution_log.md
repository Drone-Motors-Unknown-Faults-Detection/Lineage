# 實驗15執行紀錄

2026-10-03，Asia/Taipei。先手冊、再core／runner／測試；不改任何sealed基準程式或正式default。

初版九項測試在兩環境各一項斷言失敗：既有decision('8screws',0,0)回傳8screws標籤，測試誤期待healthy字串。修正測試期待值後九項通過，未改正式decision。新增六項來源／用途測試後兩環境各15通過，涵蓋梯度有限差分、奇異tie、重現、未收斂不得推論、raw threshold零值、prototype/calibration污染、子集ID來源、selector與缺失inventory。

`python -m experiments.fault_type_discriminative_prototypes smoke` 於 `.venv310/Scripts/python.exe` 與 `venv/Scripts/python.exe` 各成功，輸出 `output/fault_type_discriminative_prototypes_smoke/2026-10-03-15-21-07`、`2026-10-03-15-21-09`；都是合成工程測試，不是正式研究成績。兩環境新CLI --help均成功。

完整回歸已完成：Python 3.10.19於 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-15-22-01` 通過452項、失敗0項（63.052秒）；Python 3.14.6於 `output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-15-22-13` 通過452項、失敗0項（65.918秒）。兩環境pip check與既有37個CLI檢查均成功；實驗13至15的CLI --help另行成功，不冒稱包含在37項內。下一步protocol封存／提交、fit、train/cal來源重建／提交後才讀本批test。

上一階段實驗14成果 `11a548d77cf2a2e58f7ca56098a5633422b24a47`、實驗13 `0cd05288a204da39a4aac64cd89b91efaf7a481f` 均已push、remote一致。282個無關tracked刪除保留；沒有新issue／PR／聊天或第三方上傳。

## 協定封存

程式／手冊提交 `8cfe68f3a177f61db7e12d69acf50ce4470a79ee` 並確認remote相同。`lock --parent-protocol output/fault_type_metric_classification_lock/2026-10-03-09-42-02/protocol.json` 完成，協定 `output/fault_type_discriminative_prototypes_lock/2026-10-03-15-23-33/protocol.json`，SHA `98acdccd2201bfdc701c384256196eb7397c19dadf0b5c28865996ecb2c49e08`。24方法、216評估，全部係數／seeds／roles／loss已鎖定；此時沒有正式fit或本批test結果。

本次fit命令：`.venv310/Scripts/python.exe -m experiments.fault_type_discriminative_prototypes fit --protocol output/fault_type_discriminative_prototypes_lock/2026-10-03-15-23-33/protocol.json --data-root data/formal_local`。協定提交／push後才執行；未知不fit／cal。完成fit與source-verify後另提交，再執行evaluate／verify／report。artifact主位置D槽版本目錄，C槽標準output索引保留。

接續時再次唯讀核對GitHub main的AGENT.md，blob仍為 `8f35a6bf14fa4747d63add1d6bc852b65bcb4784`，與先前已讀版本一致。普通sandbox網路查詢被拒，改用正常核准流程成功；沒有繞過權限。正式資料、sealed程式與282個無關刪除未改。

## 正式擬合

協定與雙環境驗收提交 `8927918784ef70cbac6a458b06aaeddb5f2a39ce`，push及remote SHA一致後才fit。正式fit於15:28:56開始、15:31:11完成；9個fold／seed bundles、108個原型模型全完成，其中36個static、72個最佳化版本。GLVQ／anchor均收斂，最大198次迭代；不代表全域最小值或跨motor可靠。

compact lock `output/fault_type_discriminative_prototypes_fit/2026-10-03-15-28-56/locked_study.json`，SHA `dfa6c1fd6dc1101c29abe11d148cbc317ceab91938cdb151c99807dbcb86f78b`。大型models／實際fit audits位於 `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/discriminative_prototypes_v1/workspace/output/fault_type_discriminative_prototypes_fit/2026-10-03-15-28-56/`；C標準output的artifact_location.json保存每份SHA。正式資料source_before與source_after完全相等。

15:31:33執行source-verify，用相同protocol、上述lock與data/formal_local重建全部模型；此時尚未評估本批outer test。待來源重建成功封存與提交後才evaluate。

15:33:10來源重建完成：9個bundles全部108模型的實際原型、初始化、train checksum、損失／梯度、optimizer狀態、train predictions及known calibration threshold一致，test_numeric_reads=0。`output/fault_type_discriminative_prototypes_source_verify/2026-10-03-15-31-33/source_verified.json`保存重建證據，status=VERIFIED_AVAILABLE_NUMERIC_SOURCES；只驗證可取得數值來源，raw/session仍UNKNOWN。
