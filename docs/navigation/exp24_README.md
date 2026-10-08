# Lineage 導覽入口

給老師先讀：[實驗總覽](exp24_實驗總覽.md) → [結果白話解讀](exp24_結果白話解讀.md) → [研究流程圖](exp24_研究流程圖.md) → [示範腳本](exp24_示範腳本.md)。原始老師問題逐項回覆仍在[teacher reply](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/b3d68f145cfa187e208e38cae74bf33f68d7c367/reports/teacher_reply_20261005/reply.md)，本輪沒有覆寫。

實際操作：[UI操作腳本](exp24_UI操作腳本.md)，驗收與限制：[交付報告](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/b3d68f145cfa187e208e38cae74bf33f68d7c367/reports/navigation_20261007/final_report.md)。原稿Mermaid及SVG都在本目錄。研究模式可展開完整七問表，不改計算。

在研究checkout根目錄執行：

```powershell
python -m web.guide --data-root D:/schoolshit/專題/src/Lineage/data --port 8601 --seed 42
```

開啟 http://127.0.0.1:8601 。先選T1/8000rpm、確認資料、建立健康基準。預設LW／q95，kNN另用--openset-method knn，仍透過原factory。換方法需新server/session，不暗改目前模型。

這是獨立導覽入口，沒有取代原python -m web.server／8600；PR #36尚未合併時，不把頁面整合到Albert正在改的index.html/server.py。使用者只需瀏覽器，不需VSCode。

健康-only展示與跨馬達多類研究分開。學會前未知拒絕率、學會後已知接受率與自身配置分類accuracy不同；不提供無真值的損壞百分比、RUL或部署保證。

> 主線整合註記：這份研究摘要來自固定研究提交 `b3d68f145cfa187e208e38cae74bf33f68d7c367`。表中歷史數字不是本輪重新執行；連到研究提交的模組／報告未必已合入 main。本輪只整合獨立導覽，main 的 PolarMap 與實驗頁保留。
