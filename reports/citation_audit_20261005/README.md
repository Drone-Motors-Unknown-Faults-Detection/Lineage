# 文獻稽核與未解項

截至2026-10-06。固定 main、研究、引用歷史、Ancestor 四版本共895個文字／notebook檔；5,592筆候選、206個URL、125筆HTTP書目查詢。這些數字含重複版本、軟體與非論文提及，不是閱讀論文數。

新清冊有117個來源條目（B40＋S16＋其餘P候選，明確aliases合併）。21 VERIFIED只表示原來源PDF bytes取得，66 METADATA_ONLY只核書目，28 UNVERIFIED、2 AMBIGUOUS。七項B內容卡及相關原文查核是局部閱讀；絕不將全部書目改成全文相符。

## 可閱讀交付

- [清冊表](../../output/fault_type_citation_catalog/2026-10-06-18-25-44/catalog.md)
- [機器清冊](../../output/fault_type_citation_catalog/2026-10-06-18-25-44/paper_catalog.json)
- [原文章節、有限適配、14項勘誤](content_notes.md)
- [取得與搜尋紀錄](../../output/fault_type_citation_catalog/2026-10-06-18-25-44/search_log.json)
- [ID一致性結果](../../output/fault_type_citation_catalog/2026-10-06-18-25-44/consistency.json)
- occurrences與unresolved為同目錄的JSON.gz；5,028候選尚未人工逐條判定是否真正論文引用，含程式／紀錄false positives，不當作5,028篇未讀論文。
- [固定範圍、檔案SHA、行與cell原定位](../../output/fault_type_citation_audit/2026-10-06-00-04-16/citation_scope.json)

## 重要未解

Ancestor論文轉錄缺p.89以後的完整參考文獻表；正文部分作者年分不能唯一辨識。README的Gebraeel2005、Wang2008仍AMBIGUOUS。部分付費來源、EWMA／CUSUM公式及跨語言候選未完整核對。沒有取得原文不代表來源不存在。合法來源連結可交付，未獲再散布授權的全文不推GitHub。

因此#19部分完成，保留OPEN。新研究交付與老師文件使用已核實的範圍和明確限制；沒有宣稱全專案文獻驗收完成。

## 更正紀錄

補入獨立URL、裸DOI、完整notebook source；明確排除notebook outputs且不執行。修正Markdown DOI括號及中文標點、Git中文路徑被quoted而漏掃的問題，Ancestor論文全文.md／html已納入。各早期掃描保留，00:04:16為最後範圍版本。核心新測試在Python3.10.19／3.14.6各15項通過。沒有新模型或效能變動，正式fingerprint與exp13九權重SHA核對一致。
