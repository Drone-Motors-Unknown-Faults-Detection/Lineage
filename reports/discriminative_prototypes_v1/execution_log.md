# 實驗15執行紀錄

2026-10-03，Asia/Taipei。先手冊、再core／runner／測試；不改任何sealed基準程式或正式default。

初版九項測試在兩環境各一項斷言失敗：既有decision('8screws',0,0)回傳8screws標籤，測試誤期待healthy字串。修正測試期待值後九項通過，未改正式decision。新增六項來源／用途測試後兩環境各15通過，涵蓋梯度有限差分、奇異tie、重現、未收斂不得推論、raw threshold零值、prototype/calibration污染、子集ID來源、selector與缺失inventory。

`python -m experiments.fault_type_discriminative_prototypes smoke` 於 `.venv310/Scripts/python.exe` 與 `venv/Scripts/python.exe` 各成功，輸出 `output/fault_type_discriminative_prototypes_smoke/2026-10-03-15-21-07`、`2026-10-03-15-21-09`；都是合成工程測試，不是正式研究成績。兩環境新CLI --help均成功。

完整回歸正在 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-15-22-01` 與 `output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-15-22-13` 執行；此時不填預期通過數。下一步程式提交、protocol封存／提交、fit、train/cal來源重建／提交後才讀本批test。

上一階段實驗14成果 `11a548d77cf2a2e58f7ca56098a5633422b24a47`、實驗13 `0cd05288a204da39a4aac64cd89b91efaf7a481f` 均已push、remote一致。282個無關tracked刪除保留；沒有新issue／PR／聊天或第三方上傳。
