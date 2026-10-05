# #22 原待辦核對：hard600 outer 已執行，未通過改善契約

2026-10-05，Asia/Taipei。本文件更正 issue 原 checkbox 的進度，不修改封存研究產物。

## 完成證據

exp13 的 E02 是 hard600 對角距離＋train 子集的距離加權 5NN；E04 是同一距離＋全部 known train 的 5NN。E01／E03 為各自 identity 配對基線。E10／E12 另測同學習空間的 factory Mahalanobis-LW／k-NN；E08 使用原 LMNN Eq.15 的三項 energy 分類。這正是原待辦的 outer，不是以後續不同研究代替。

本輪唯讀核對 `output/fault_type_citation_audit/2026-10-05-23-51-20/existing_evidence_verified.json.gz`：

| 項目 | 結果 |
|---|---|
| 90 CSV／28,910 筆／105 維 | 指紋 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d 一致 |
| 九份 hard600 權重＋solver diagnosis／protocol | 逐檔實際 SHA 與 outer protocol 指定一致 |
| E protocol seal | 9ca9be082013349680b642e509be761d84ca150a947429251bd1c50f86ed1a8b |
| E evaluation seal | f7b055a5f3081d0c0718fa52d0705c0edd29528f2cbc5cdfb9617101a41cb60a |
| E verification seal | 66b5dce1ce08d3d0dd778faac7b13ab3893e5097372c46ae1d275ec65cd084d5 |
| E report seal | cc05eabc98cfce711dda0999032fec524d0ea3ac720d82cf285365a7fa4b277c |
| 實際 outer 評估 | 108 組、失敗清單空、1,040,760 筆預測紀錄、28,910 unique samples |
| 本輪訓練／新預測 | 0／0；上述為既有封存核對 |

完整參數、每 motor／RPM／seed 結果、來源與備份已在 [exp13 結果](../metric_classification_v1/final_findings.md) 與 [索引](../metric_classification_v1/result_index.json)。本輪只驗 seals、綁定與來源 SHA，不冒稱重新推論全部預測；先前 exp13 verification 保存逐筆重推證據。

## 配對結果與收尾理由

固定 seed0、三 motor 等權描述平均，fault accuracy 僅 true known faulty：E01 28.475% → E02 24.968%，下降 3.507 個百分點；E03 28.464% → E04 24.809%，下降 3.655 個百分點。三 seeds 全部保留，不能取 E06 seed2 的較高值替代主成績。E 方法 T1 unknown recall 仍為 0%；12 方法全部未過可靠性契約。

之後 M 批 216 組／24 方法也全部 FAILED。既有各批及無效／未完成格子見 [完整研究報告](../research_closeout_20261005/final_report.md)。本輪收尾，不啟動預先規劃但未執行的 N／Group DRO，不把它寫為算法已完成。#22 可依本輪階段收尾結案；#9 仍追蹤來源與獨立研究資格。

研究分層：用途與產物核驗 VERIFIED；可靠提升 FAILED；fresh final INCOMPLETE；session／原始錄製／視窗／物理一致性 UNKNOWN。正式 default105／linear／LW、PolarMap 與可切換 factory k-NN 不改。
