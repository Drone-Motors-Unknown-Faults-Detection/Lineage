# #30：整合後17項稽核差異

舊發現源於44d98da／80bdf54；2026-10-06的正式重驗以64cb71d為基線，交付固定[83846b main_reaudit](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/83846b2967bb1f925e457db8093cfdb2d430c1bc/reports/issue_delivery_20261005/main_reaudit.md)。[原證據JSON](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/83846b2967bb1f925e457db8093cfdb2d430c1bc/output/fault_type_issue_triage/2026-10-06-18-37-13/main_review.json)、[R1–R10原稿](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/83846b2967bb1f925e457db8093cfdb2d430c1bc/reports/issue_delivery_20261005/roadmap_issue_drafts.md)、[待插入段落](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/83846b2967bb1f925e457db8093cfdb2d430c1bc/reports/issue_delivery_20261005/health_and_reports_section22_patch.md)、[原分工](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/83846b2967bb1f925e457db8093cfdb2d430c1bc/reports/issue_delivery_20261005/remaining_issue_triage.md)皆保留，不恢復舊reports。

本輪main4f783c6。對不受PR38/39影響的程式以Git blob及AST行號核對，沿用舊反例且明記未重跑；只對新增串流測試與文件索引重新驗收。機器證據由 `python -m tests.issue_delivery_evidence --data-root D:/schoolshit/專題/src/Lineage/data` 保存於output/issue_delivery_evidence。SHA不是新行為測試，PERF未profiling，SEC-003未做root外寫入。

| ID | 舊64cb結論／證據 | 本輪4f783c6結論／檔案行號 | 限制／追蹤 |
|---|---|---|---|
| EXP-002 | summary缺CSV/log仍完整 | 仍成立；exp6_matrix.py:77 `_is_complete`，blob未變 | 原fixture未重跑；R1草案 |
| DATA-001 | healthy-only且任意105欄被載入 | 仍成立；core/data.py:54、68，blob未變 | 欄語意／exact labels仍未檢；R2 |
| DATA-002 | min(widths)截短且未記原寬度 | 仍成立；core/formal_data.py:314 `_convert_condition`，未變 | 不推論raw同步；R3 |
| DATA-003 | 無manifest同size/mtime不同bytes同指紋 | 仍成立；formal_benchmark.py:68，未變 | 原反例，不宣稱本輪正式資料遭竄改；R4 |
| DATA-004 | manifest保存absolute path | 仍成立；core/formal_data.py:433，未變 | portable／private分離未實作；R4 |
| SEC-002 | client取得exc repr | 仍成立且SSE也傳exc；web/server.py:177、241、279、324 | 本輪唯讀核新增SSE路徑，無外部攻擊；#28/R6 |
| SEC-003 | '..'接受，離開RPM目錄 | 仍成立，root escape未驗證；formal_data.py:314，未變 | 舊stub未越root，不寫完全安全或已證root escape；R3 |
| REPRO-001 | exp1–3未統一指紋與環境 | 仍成立；exp1:146、exp2:283、exp3:172 | exp1/3行移動，新增iter_run未統一metadata；R4 |
| REPRO-002 | formal結果缺packages/hardware | 仍成立；formal_benchmark.py:147，未變 | integration驗收記packages不等於所有研究runner補齊；R4 |
| ARCH-001 | parser與schema並行、無canonical config | 仍成立；runner.py:18、formal_benchmark.py:300，未變 | 維護議題，不推數值失效；R7 |
| ARCH-002 | 多責任大函數 | 結構仍成立；formal_benchmark.py:147、matrix.py:110、web/live.py:197，未變 | 未重構、未profiling；R10 |
| TEST-002 | catalog已測、WS/loader/輸出不足 | 部分再改善；test_navigation_guide.py、test_stream_integration.py、test_integration_navigation.py | 新增匿名/狀態/同算/中斷釋鎖測試；主WS Origin、正式loader仍缺專項，非全修；#27/R5 |
| AGG-001 | tampered manifest fingerprint被發布 | 仍成立；aggregate_exp6.py:56、103，未變 | 原fixture未重跑；R1，不和health彙總#25混同 |
| PERF-001 | CSV load無指紋cache | 結構未變；data.py:68、runner.py:51 | 未profiling，不能稱主要瓶頸；R8 |
| PERF-002 | 逐類kneighbors | 結構未變；openset.py:108、149 | 不沿用舊秒數當本輪量測；R8 |
| DOC-001 | index已修但歷史內部連結限制 | 現行選定索引目標重新驗證；docs/README.md:1及本輪新增文件 | 相對檔案存在不保證所有歷史錨點或遠端網址；R9 |
| DX-001 | 主流程POSIX，局部PS | 部分改善但仍成立；build_uv.sh:1、run_web.sh:1；exp24有PS入口 | 獨立3.10.19 Windows驗收不是所有install路徑；#26/R9 |

上表省略路徑前綴時，expN／matrix／aggregate均在experiments/；所有行號固定4f783c6。來源工具保存每檔SHA與完整函數跨度。原62（2026-10-03）、80等數字保留日期脈絡，不改寫成新測試數。歷史重驗工具24項與現行main suite是不同範圍。

## R1–R10去重及可發布草稿

所有草稿尚未發布、未指派。#30第二checkbox涉及新issue發布，目前仍待授權；文件整合只在本PR，不先勾main已更新。

| 分組 | 處理方式 | 最小重現／驗收 |
|---|---|---|
| R1 EXP-002/AGG-001 | 一份新草案，不重開#25 | 只有合法summary但缺CSV/log，及manifest指紋不符；完整性拒絕、合法數值不變、舊output不覆寫 |
| R2 DATA-001 | 新草案 | healthy-only/任意105欄fixture；先定exact schema/labels/finite/nonempty與compatibility，不重清資料 |
| R3 DATA-002/SEC-003 | 一份新草案 | 通道2/3窗、config '..'；明確通道截斷政策與resolved containment，drive/UNC/absolute測試只寫temp，root escape目前未驗證 |
| R4 DATA-003/004/REPRO | 一份metadata草案，引用#26 | 同size/mtime異bytes需異SHA；portable摘要/private sidecar、commit/packages/OS版本，排除raw寫入 |
| R5 TEST-002 | 補既有#27，不重建CI issue | loader/主WS/exp1–3契約；先保留新增導覽與SSE測試，不重寫 |
| R6 SEC-002 | 補既有#28，與PR36同server檔保留 | client不回path/trace，server有correlation；本輪不修 |
| R7 ARCH-001 | 新草案 | flags到canonical config到schema一致；fitted guard由#29處理 |
| R8 PERF | 一份量測草案 | 固定資料/seed量load walltime/memory及classes/batch/reference；先量再決定cache/vectorization |
| R9 DOC/DX | 文件入口本輪補，環境部分引用#26 | clean Windows與POSIX smoke、歷史鏈；不刪venv、不把局部驗收當全平台 |
| R10 ARCH-002 | 新草案 | 先fixture契約，再逐helper；metrics/event順序不變，排除Albert重疊檔案 |

## 其他issue分工證據

#24涉及health_monitor CLI、#28涉及server，公開PR36有實際同檔重疊，留後續協調；#35及health串流本輪不碰。#25/#26/#27未見公開新PR且沒有assignee，標待確認接手，不能說都屬Albert；#27依賴#26環境政策。#13–16須先對固定研究分支既有AE、遷移、Ancestor對照與視覺化成果判讀，main缺檔不等全專案未做；本輪不訓練。#9的raw/session/fresh資格仍UNKNOWN/INCOMPLETE。未知未推送工作與作者意圖不推斷。
