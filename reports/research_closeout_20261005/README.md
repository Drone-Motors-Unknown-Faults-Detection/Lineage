# 單顆馬達研究收尾交付

主報告為 [final_report.md](final_report.md)，依 2026-10-05 最新要求存入 GitHub 專案。全文包含資料分工、十二批證據、方法與有限改編、40篇文獻來源及閱讀範圍、完整方法主表、各 M seed、逐 motor／RPM／配置與失敗原因。報告主題為「單顆馬達訓練與跨馬達校準的開放集故障辨識研究」。

本階段採 B 收尾。M216 評估與工程核驗完成，1,134 配對已核對，24 方法可靠性全部 FAILED。N Group DRO 仍為已規劃未實作，不新增訓練。來源獨立性 UNKNOWN、fresh final INCOMPLETE。正式105維、Mahalanobis–LW、k-NN factory與PolarMap不改。

## 數值與索引

- `output/fault_type_research_closeout/2026-10-05-22-34-03/`：原盤點、完整壓縮 method_catalog、decision_record、重算 fold_support。
- `output/fault_type_research_closeout/2026-10-05-22-53-29/`：與主報告相同內容的 Markdown、Word 原稿、逐格 content_qa、arm_inventory、完整 M 交付及增補 checkpoint_inventory。
- `reports/feature_self_challenging_v1/result_index.json`：M各階段實體SHA、語意seal及六ZIP恢復入口。
- `delivery_index.json`：本次文件、備份與提交來源索引。

完整逐筆預測與模型沿各批 artifact_location.json 的 primary 路徑，不能拿 compact 摘要冒充原始 predictions。大型模型／原始預測仍在既有 D 槽；小型索引與文件入 Git。

## 驗收與維護

新盤點／formatter 11項測試在Python3.10.19及3.14.6各通過。原618項完整科學驗收先前已完成，本回合未重跑。Word37表格／751列逐格與Markdown一致，5原生公式、40原文超連結與ZIP CRC通過。bundled renderer 缺少soffice.exe，LAYOUT_UNVERIFIED；未使用desktop LibreOffice，沒有逐頁PNG視覺驗收。

日後維護先修改 `report_body.md` 與 `references.json`，透過 `build_report.py` 使用封存summary產生新的日期目錄，保留舊版本。科學wrapper的 `--document-runtime` 指定loader所解析的bundled Python；`--word`／`--renderer` 為可選文件入口。不得改sealed演算法、刪失敗格或在test上重新調參。既有output版本和Git歷史都保留。

備份：`D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-05/research_closeout_20261005/archives/fault_type_2026-10-05-22-53-29.zip`，1 ZIP／16 members SHA／CRC PASS，保留原檔。同機D槽不稱異地備援。
