# 實驗14來源、改編與接續帳冊

2026-10-03，Asia/Taipei。exp14編號已查GitHub main及本分支，未使用。先寫手冊再實作；尚未fit正式資料，不填改善數字。

## 搜尋與來源

英文查詢 `Sugiyama local Fisher discriminant analysis 2007 multimodal original paper` 與官方LFDA程式；來源為 [JMLR原論文](https://www.jmlr.org/papers/volume8/sugiyama07b/sugiyama07b.pdf)、[作者出版目錄](https://www.ms.k.u-tokyo.ac.jp/sugi/publications.html)、[官方實作](https://contrib.scikit-learn.org/metric-learn/_modules/metric_learn/lfda.html)。已讀§3.1–3.3、Eq.9–12、演算法圖、§6限制及官方fit程式；PDF公式頁已渲染。不宣稱逐頁35頁全文讀畢。引文／公式只是設計來源，原文成績不替代本站測試。

原法權重、scatter、generalized eigen與weighted embedding保留；新增固定ridge、零尺度保護、固定子集與兩個秩。原始書目與逐項變化詳見手冊。原文不保證未知類別偵測／馬達domain transfer，affinity敏感性是待反證限制。

H14：局部結構保留比PCA更有助於同條件跨馬達分類。四個matched表示法、同train子集、同known classifier/reference、同cal與test；比較classifier／detector分開。只改善平均但healthy gate／最弱類別／unknown保護失敗，不能宣稱可靠性達標。

## 工程測試

新增15項：9項公式／秩／重跑與6項數值來源。第一次門檻污染測試因factory frozen dataclass不可直接賦值而ERROR；改用dataclasses.replace構造被污染副本，未修改factory保護或研究門檻。Python3.10.19及3.14.6各15項通過；完整回歸正在執行。synthetic smoke僅工程，不是研究成績。

## 儲存與限制

C槽保留門檻不能下調。大型本批產物直接寫D槽已授權專案範圍，standard logs/output保留compact索引。既有90CSV、歷史manifests／模型／報告不覆寫；formal default不變。motor角色依文件支持，raw/session/window/IQR/units/mount/load UNKNOWN，全部樣本test已曝露；new source verifier不能清除此歷史。

待辦為完整回歸、protocol lock／提交推送、9模型fit、來源重建／提交、144評估／reinfer／report、D槽archive SHA/CRC、可靠性契約與下一個有界方法。
