# 給老師：2026-10-09 主線交付與剩餘問題

## 本輪已確認

| 項目 | 程式／PR | main 與 issue | 可以支持的結論 |
|---|---|---|---|
| 未擬合防護 | PR #40；core/monitor.py | main `c68b7cdbb5bddf1034a9e713c8e8efd5acc61c87`；#29 completed | 沒有擬合或重擬合失敗時，推論有明確 RuntimeError；成功擬合分數與原版相同 |
| 健康指數封存彙總 | PR #41；experiments/health_index_aggregate.py | main `ae53b92eea7dd68cd7ffefe8d5c24b3f7157428d`；#25 completed | 六 run／54 列可重算；349 欄中 347 吻合、2 精度差異明列 |
| hard600 subset/all-train | 研究分支既有 E02/E04，非本輪新訓練 | #22 於 2026-10-06 關閉；研究程式未整批合入 main | 固定 seed0 的 fault accuracy 下降 3.507／3.655 個百分點；未找到可靠提升 |

主線最後一次 Python 3.10.19：162 passed，0 failed/error/skipped，pip check 與四個 CLI help 成功。guard 另有 11 項與 8 組等價比較；導覽 Mahalanobis/k-NN 各 595 筆、0 mismatch。詳見 [命令、commit 與產物](execution_log.md)。工程修補沒有重新 fit，也沒有準確率增加。

## 仍未通過或無法確認

- **FAILED**：hard600 沒有可靠提升；不能把最佳化收斂當分類改善。其 [固定研究證據](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/e7ee971d2ed41d5ce80e3a56f912eb4dc1c038dc/reports/issue_delivery_20261005/hard600_closeout.md) 與負面結果保留。
- **DIFFERENT**：兩個健康指數方法差值欄為舊 0.018513、新 0.018512；容差 0.0000005。先四捨五入可解釋舊值，原生成程式缺失，歷史操作 **UNKNOWN**。#25 要求回報差異，不要求零差異，因此可關工程 issue。
- **UNKNOWN／INCOMPLETE**：raw/session/run、原始視窗／刪點／同步證據、獨立新採集與 fresh final 仍不足。T1/T2/T3 是三顆馬達，不能拼成一顆退化生命週期。#9 不關閉。
- #19 尚未核實全部原文引用；#30 追蹤已發布 [#43–#49 與去重補充](audit_followups.md)，各缺陷仍 open；#26 依賴政策、#27 CI 尚未完成。#13–16 須另核完整協定與驗收。
- #24/#28/#35/#37 原首頁入口與 Albert PR #36 有同檔重疊，本輪未修改 health_monitor.py、server.py、index.html、experiments.js，未合併 PR #36。

七問背景與示範操作在 [exp24 導覽](../navigation/exp24_README.md)；[實驗八完整重算說明](../experiments/exp8_health_index_aggregate_delivery.md) 保存手冊、SHA、舊值／新值與限制。本輪證據僅支持工程交付與現有資料比較，不支持部署可靠度、RUL 或 fresh final。

## 文件驗證入口

`python -m tests.project_closeout_evidence` 只檢查本輪選定文件的相對檔案目標及來源 SHA，輸出到 `logs/project_closeout_evidence/`、`output/project_closeout_evidence/`；不載入正式資料，不驗證所有歷史錨點或遠端論文全文。完整回歸使用 `python -m tests.integration_evidence --phase candidate --data-root <既有唯讀資料根>`。
