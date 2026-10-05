# 實驗23 引用來源與文件證據稽核

本項是唯讀文件稽核，沒有新模型、訓練、切分或研究效能指標。先登錄範圍再執行引用清冊彙總。對應 #19、#20 與 #22 交付。

## 方法

以固定 Git ref 讀取 main、研究分支與明確引用的歷史快照；Ancestor 固定 commit 僅讀文字與 notebook Markdown／註解，不執行。掃描 Markdown、Python、JSON、BibTeX、文字、notebook；PDF／Word 透過 bundled 文書工具抽取。排除 data、模型、逐樣本預測、大型 ZIP、venv 與秘密。每個範圍保存 ref、檔案清單、SHA、行號或 cell。自動匹配只是候選引用，人工逐篇判定；不宣稱全部 Git 歷史已讀。

固定 main `64cb71d84663e1745ec54db74abad68def67e8e6`；起始研究 ref `e58e37307af4f10655f05c672c84623867c98c6f`；Ancestor 候選 `1ef4a891ae02dc95910f747a5163bb2edd608f28`。實際可讀範圍與取得失敗另列。

## 文獻與判定

原期刊／會議／arXiv／作者稿為內容依據；官方 API 文件只說明實作介面。paper_catalog、citation_occurrences、claim_audit、content_notes、change_log 與 search_log 分開保存。存在狀態 VERIFIED／METADATA_ONLY／NOT_FOUND_AFTER_SEARCH／AMBIGUOUS；內容狀態 SUPPORTED／PARTIAL／CONTRADICTED／UNVERIFIED。無全文不填虛構公式或作者成績。

此稽核本身是專案工程程序，沒有演算法論文來源。LMNN、MMMF scalar、Invariant Kernel、REx、RSC、MSP 等取用差異以原文章節及實際程式核對。封存程式與資料不改，必要勘誤另存。

`--verify-existing` 另用既有 formal catalog 重算 90 份 CSV 指紋，並核對 exp13 protocol／evaluation／verification／summary seals、九份 hard600 權重 SHA，以及歷史三個 matrix index。僅驗證、讀摘要，不重新訓練或重新產生預測；檢查與新文書輸出同樣使用 setup_run 保存。

## 預期與反證

預期每個實際找到的引用候選有 paper 或待辨識項目，且每篇有閱讀深度與主張判定。無法辨識、官方站無法取得、重要公式未確認均保留未解，不得以 URL 可打開宣布全文相符。既有成績不變；只讀彙總不得接觸 fit／cal／test 選參。

## 程式碼與輸出

| 範圍 | 位置 |
|---|---|
| 稽核入口 | experiments/fault_type_citation_audit.py，run(...) 與 main() |
| 共用 | core.logger.setup_run；Git 唯讀物件與標準函式庫 |
| 測試 | tests/test_fault_type_citation_audit.py |
| 執行證據 | logs/fault_type_citation_audit/、output/fault_type_citation_audit/ |
| 文件 | reports/citation_audit_20261005/、reports/teacher_reply_20261005/ |
| 不修改 | data、sealed ML core／experiments、web、experiments/health、Albert PR |

CLI：`.venv310/Scripts/python.exe -m experiments.fault_type_citation_audit --help`。來源與機器可讀清冊可使用本機合法快取；無散布授權全文不入 Git。
