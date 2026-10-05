# 指定 issue 交付盤點

本輪以研究分支 `research-improvements-20260920` 的 `e58e37307af4f10655f05c672c84623867c98c6f` 接續。main 固定版本為 `64cb71d84663e1745ec54db74abad68def67e8e6`。實際工作樹是 `C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree`。原有 282 個 tracked deletions、1,334 個 untracked entries 保留，不全量 stage。

已完整讀取本地 AGENT.md、遠端 main AGENT.md、本輪 .txt 與前一份收尾 .txt。main 的 health 搬移與 reports 整理不套到尚未合併的研究分支；依本輪指定交付研究 Markdown 與 evidence 索引，不恢復 main 已刪目錄。寫作指定文章取得回傳 non-retryable error；採 AGENT.md 已列出的五項規則，不宣稱讀過文章全文。

## 原要求與實際進度

| Issue | 證據與現況 | 本輪待交付 |
|---|---|---|
| #22 | 上輪完整報告、M216 核驗、1,134 配對與備份已在 e58e373；24 方法未通過契約 | 對原 checkbox 核實 hard600 outer，補交付回報與收尾理由 |
| #19 | 原 body 要求全部專案引用及內容；沒有 comments | main、研究、明確歷史與 Ancestor 引用範圍清冊、內容與主張判定、勘誤 |
| #20 | 原 body 要求回覆張老師；沒有 comments | 獨立老師回覆 Markdown 與 Word，核對歷史 A/B 與當前結果 |

初步查到 exp13 的 E02／E04 為 hard600 子集／全部已知 train 的距離加權 5NN outer，E10／E12 是同空間 factory detector 消融。需要核對其 protocol、verification 與 summary 後才能認定原待辦已執行；不以後續不同方法代替。

正式資料 fingerprint 保持預期值 `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`，本輪另做唯讀核對。Python 科學環境為 3.10.19／3.14.6；文件使用 bundled Python，沒有升級科學依賴。本輪不重跑已驗證的 2,490 次歷史研究。

## Albert 工作隔離

PR #36 尚未合併，head `544d4ed8c6516622e2f46c095351f9483a61635c`，作者 JW-Albert。範圍為 web、exp1／3／4、health_monitor、iter_run 測試及其文件。PR #32 的 health 搬移及 reports 整理已在 main。上述程式本輪不修改；剩餘 issues 在三項交付後重新盤點。

## 驗收層次

工程及文件可完成。可靠性 FAILED、fresh final INCOMPLETE、raw/session/window 證據 UNKNOWN 分別保留。Word 若 bundled renderer 缺少 LibreOffice，保存真實錯誤並標示 LAYOUT_UNVERIFIED，不能稱逐頁 QA 已完成。

## 執行紀錄

- 起始 GitHub 讀取：#22、#19、#20 body 與 comments 均已讀；三者 comments=0。
- 使用 GitHub connector；comments 第一次參數名稱不符，改用 repo_full_name 後成功。
- git fetch 只更新 remote tracking refs；沒有 merge、checkout 或修改 Albert 分支。
- 網路取得寫作文章失敗，未繞過限制。
