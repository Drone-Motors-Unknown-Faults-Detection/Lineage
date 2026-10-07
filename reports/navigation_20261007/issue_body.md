## 研究分支導覽交付與主線整合邊界

本輪範圍：七問實驗總覽、白話解讀、流程圖、UI操作契約、示範腳本與獨立web.guide；原105維／LW／kNN factory／PolarMap不改。程式commit01862fe已推送research-improvements-20260920，詳細文件與截圖隨交付commit保存。

- [x] 24個研究家族／協議七問與來源索引，含失敗及未實作支線。
- [x] Mermaid與實看SVG；未知、隔離、確認、完整池更新、趨勢與限制。
- [x] 獨立8601三入口、兩模式與真實session狀態；未提前揭示候選配置答案。
- [x] CLI兩方法各595筆配對，mismatch0；兩Python各671測試PASS。
- [x] 瀏覽器健康→匿名未知→51筆候選→確認→兩known→重連，最終567筆完整落盤；A/B與窄屏另有截圖。
- [ ] 主線首頁整合：等待Albert PR #36合併／審閱後決定最小整合，不在本輪覆寫server.py/index.html/experiments.js。

文件位置：docs/navigation/README.md、實驗總覽.md、結果白話解讀.md、研究流程圖.md、UI操作腳本.md、示範腳本.md；reports/navigation_20261007/final_report.md與execution_log.md。

目前沒有fresh final，raw/session依據UNKNOWN，T1跨馬達unknown零召回未解決。此issue只追蹤導覽交付與主線整合，不關閉既有研究可靠性／引用稽核issue。舊部分QA log缺尾筆如實保留標PARTIAL；新導覽flush修補不改科學計算。

Co-authored-by: Codex <codex@openai.com>
