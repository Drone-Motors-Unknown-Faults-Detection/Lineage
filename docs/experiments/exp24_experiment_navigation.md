# exp24：實驗證據總覽與操作導覽

2026-10-06事前範圍。本項整理既有實驗及CSV逐筆演算展示，不新增演算法、切分或成績搜尋。成功條件為來源可查、七題完整、模式切換不改數字、未知答案確認前不顯示、三流程實際操作可重現。若來源不足或與PR36重疊，列出限制，不偽造結果。

## 方法與來源

先唯讀列研究分支及固定main的實驗入口、手冊、result_index、Q–M批次與250項方法／分數清冊。SHA限定原檔bytes與Git blob，來源缺失另列。舊main實驗1–8按固定commit閱讀，不恢復研究checkout已刪文件。來源：既有core.monitor、core.openset、ScaleGrowthSession、TrendMonitor及封存研究；文獻與適配說明重用exp23清冊，不另稱新原創方法。

再用七題說明資料用途、模型與成功條件，區分證據／解釋／推論／資料不足。流程以Mermaid及SVG維護，CSV重播不稱設備連線。介面重用web.live.LiveDemo的tick、confirm、scenario與core.data的既有切分；web僅編排，不另算距離、分群或趨勢。確認後完整標記配置池重新切train/cal/holdout並重擬合，非25筆增量學習。

## 範圍及預期反證

| 類別 | 檔案 |
|---|---|
| 盤點入口 | experiments/fault_type_navigation_inventory.py（run/main及setup_run） |
| 導覽文件 | docs/navigation/實驗總覽.md、結果白話解讀.md、UI操作腳本.md、研究流程.mmd／svg、示範腳本.md |
| 獨立介面 | web/guide.py、web/static/guide.html／js／css；不覆寫PR36的server.py／index.html／experiments.js |
| 重用不修改 | web/live.py、core/monitor.py、core/openset.py、experiments/exp2_scale_growth.py、exp3_trend.py |
| 驗證 | tests/test_navigation_*.py；logs/navigation_*及output/navigation_* |

PR36尚未合併時獨立導覽不提供它的iter_run/SSE。既有web.server入口保留。舊API主線整合要待PR36落定，不能稱已改main首頁。缺正式data時可開空狀態頁，禁止以fixture冒充研究。

盤點CLI：`python -m experiments.fault_type_navigation_inventory`。導覽CLI（實作後驗收）：`python -m web.guide --data-root data/formal_local --port 8601 --seed 42`。資料唯讀、未知不fit、預設105/LW不變。未有實際瀏覽器截圖、事件與模式等價測試時，UI驗收未完成。
