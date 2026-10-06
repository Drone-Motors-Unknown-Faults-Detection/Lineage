# 研究收尾與老師回覆

交付核對2026-10-06（Asia/Taipei）。本輪沒有新訓練與新預測；#22原hard600外層已由既有E02／E04核對完成，下降約3.507／3.655百分點。最後M216評估、24方法均未通過固定可靠性契約；停止本階段搜索，不啟動Group DRO。

## 正式文件

- [完整研究Markdown](research_report.md)與同目錄research_report.docx：原完整數值及附錄保留，加hard600核對和本輪文獻勘誤。
- [給張老師的說明Markdown](../teacher_reply_20261005/reply.md)與同目錄reply.docx：兩個問題在第2–5節直接回答，第8節列完成度。獨立文件含七個明確分頁，八個邏輯段落；沒有渲染結果，不聲稱實際八頁。
- [文獻清冊與尚未完成事項](../citation_audit_20261005/README.md)：#19仍OPEN。
- [結構與內容QA](document_qa.json)：完整報告39表／773列／5原生OMML公式；老師回覆7表／39列。全部表格逐格一致，ZIP CRC通過。

兩份Word已用bundled renderer實際嘗試，均找不到soffice.exe。LAYOUT_UNVERIFIED代表逐頁排版未驗收，正式內容核對完成。沒有使用使用者桌面LibreOffice或更動科學依賴。閱讀Word時仍需檢查換頁、長表、公式與字型；不將內容完成稱全部版面驗收通過。

## 保存位置

原D槽未掛載，無權限提升繞過；正常權限唯讀查核也只有C槽，D備份本輪未完成。新3ZIP暫存於C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/lineage_document_backups/2026-10-06。這是本機暫存，非長期或異地備份；正式小型文件與完整稽核JSON／gz另外推至GitHub。

whole SHA、所有成員SHA與CRC結果見output/fault_type_archive/2026-10-06-18-29-09/archive_index.json及其verification索引。沒有覆寫舊D槽備份、data或sealed models。

## 尚未解決

模型可靠性FAILED；原始recording/session/window資格UNKNOWN；fresh final與每類獨立test群不足INCOMPLETE。#20可按回覆文件交付結案，不代表老師問題一的可靠模型已通過。#22按有限研究收尾結案，不連帶關閉#9。#19關鍵全文與身分仍待核，不能關閉。
