# 分支整合執行紀錄

日期：2026-10-08，Asia/Taipei。工作樹 `D:/schoolshit/專題/src/lineage_integration_20261008`。

## 盤點與備份

- 遠端 main 與新備份 `backup/main-before-integration-20261008-131410` 均為 `64cb71d84663e1745ec54db74abad68def67e8e6`；以 ls-remote 和 GitHub ref API 分別查證。未更新原 checkout 或 source branches。
- 盤點 commit `e8d08f1a6152888b6d475091f0937e271f5a5882` 已 push，遠端 SHA 相同。
- 原環境 Python 3.12.14 缺 loguru，未當作版本驗收。獨立環境 `D:/schoolshit/專題/src/tmp/lineage_integration310` 使用宣告的 Python 3.10.19，依 pyproject 八項依賴安裝；pip check 通過。未修改 pyproject 或原 venv。

## 導覽批次

先寫 `docs/experiments/exp24_experiment_navigation.md`，再從研究固定 SHA 抽取導覽與來源文件。只適配 data 根、exp24 名稱及固定 GitHub 歷史連結，不覆蓋 main 首頁、core、live.py、health 搬家或 AGENT。

實際指令（在工作樹執行，python 為上列環境的 Scripts/python.exe）：

```powershell
python -m tests.integration_evidence --phase baseline --data-root D:/schoolshit/專題/src/Lineage/data
python -m tests.integration_evidence --phase candidate --data-root D:/schoolshit/專題/src/Lineage/data
python -m experiments.navigation_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42
python -m web.guide --data-root D:/schoolshit/專題/src/Lineage/data --port 8611 --rate 10 --seed 42
```

- 基準首次 `output/branch_integration/2026-10-08-13-20-42`：76 項中 64 通過、12 個 WinError 5 暫存權限 errors，保留原始證據。只調整測試行程 tempfile 根到該 run output，不改 production 或降低測試要求。
- 基準重跑 `2026-10-08-13-21-54`：76 passed、0 failed/errors/skipped。CLI 四入口與 pip check 通過。
- candidate `2026-10-08-13-22-14` 因沙箱本機 TCP 權限停滯；沒有完整結果，標記 ABORTED。核對自己啟動的命令與 PID 後停止自己的測試／server，沒有停止使用者行程。
- 正常權限 candidate `2026-10-08-13-24-19`：98 passed、0 failed/errors/skipped。未使用 skip 冒充驗收。
- 真實配對 `output/navigation_regression/2026-10-08-13-22-25/summary.json`：Maha 與 k-NN 各 595 筆，共 1,190 筆，score/verdict/PCA/EWMA/CUSUM/quarantine 等欄位差異 0；source_unchanged=true。兩者 75 筆故障到達後有候選；A/B 警報與原 main 相同。這是同工況工程回歸，不是新模型準確率或獨立資料研究。
- 本機實際資料為 60 檔（T1/T3 × 三 RPM × 十配置）；歷史 90 檔未完整恢復，不宣稱全部九工況驗證。完整檔案 SHA 清冊在 validation.json。
- `tests/integration_evidence.py` 子行程使用 PYTHONIOENCODING=utf-8，避免 Windows CLI 中文被錯誤解碼；首次結果不覆寫，後續另產新 run。
- 瀏覽器 QA 完成：匿名候選／確認、模式、reset、A260/B160播畢、T3新工況、reload同session暫停；詳細結果與截圖在 output/integration_browser/guide_qa.md。負面錯誤情境由 HTTP/WebSocket fixture 覆蓋，沒有冒稱 UI 點擊。已關閉測試頁、flush後只停止自己的8611服務。
- UTF-8 修補後 `2026-10-08-13-30-10` 再跑98 passed、0 failed/errors/skipped，四CLI/pip check通過；此回合仍為工程驗收。

## 待整合串流邊界

重新讀取 #36 全文、評論、reviews、checks；head 仍為 `544d4ed8c6516622e2f46c095351f9483a61635c`，無評論／review／checks。#35 仍 OPEN，health_monitor 用健康 holdout 索引取其他較短配置。本輪不接手其修法；若抽取串流，只帶 exp1/3/4，health stream 不註冊、不改 source branch 或 #35 狀態。
