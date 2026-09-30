# 完整 artifacts 路徑與校验

本機工作根目錄：
`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`

## 資料與切分契約（Git保存compact文件）

- 資料稽核：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\data_audit.md`
- 機器可讀稽核：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\data_audit.json`
- Full126 A registry：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\manifests\class_roles_v1_40cb4312c2e92342.json`
- Balanced30 B registry：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\manifests\class_roles_v1_6bdff74614f1d781.json`
- Group split example：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\manifests\campaign_example\campaign_split_summary.json`
- Manifest validation example：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_manifest\2026-09-30-18-43-30\validation_index.json`
- 正式唯讀feature root（不在Git／ZIP）：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\data\formal_local`

## 三個完整research matrices

- A N=5：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-05-42`
- A remaining sweep：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-37-27`
- B N=5：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-37-39`

每個目錄：`run_plan.json`、`run_status.json`、`environment.json`、
`matrix_index.json`、`aggregate_<protocol>_n<N>_<method>.json`、
`paired_comparison.json`是compact版控證據；`manifests/`保存完整checksum-bound
sample manifests；`runs/<run_id>/`包含predictions.jsonl.gz、fit_audit.json.gz與
summary.json，涵蓋逐樣本機率、test IDs、scores、全部confusion matrices／metrics。
完整內容可從下列D槽ZIP恢復，不依賴Temp是永久存在的假設。

## 合併表、圖與深入分析

- 全部輸出：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34`
- 表格mean/SD/nominal CI/pooled：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\results_table.csv`
- 趨勢圖：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\known_fault_sweep.png`
- 每protocol/N配對：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\paired_by_protocol_and_N.json`
- 每unknown配置：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\per_unknown_configuration.json`
- 每known配置：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\per_known_configuration.json`
- Unknown吸引方向：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\unknown_attraction_counts.json`
- RPM/campaign分析：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\primary_condition_analysis.csv`
- 最難配置：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_report\2026-09-30-23-49-34\hardest_configurations.json`
- 最終13項回報：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\final_findings.md`
- 執行／失敗／commit/push紀錄：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\execution_log.md`
- 詳細重現：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\reports\fault_type_openset\reproduction.md`

## D槽完整ZIP64（均CRC PASS，原始工作檔未刪除）

| Artifact | Bytes | Files | SHA-256 |
|---|---:|---:|---|
| A N=5 | 3712231384 | 2654 | 25fc12c6982143f72fdf8c5534837dcd4767ba98ab106af39bdbb10eacb3d540 |
| A remaining sweep | 4691045317 | 3570 | 64ad06dac8625e838a6df251b247d7bc295837f602a3a7f9c2d98ceeea36377b |
| B N=5 | 3375246908 | 2527 | 24ec1e80346dcbc2d8244dfaa9c0cc2188788ae8eed0530d2fde3671b1e38f8f |
| Combined report | 2176346 | 10 | 414532b03e8dbc3a7e13b22daef2934c5771bdfbddcdcfb35f4cae80108df047 |

- A N=5：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-19-05-42.zip`
- A remaining sweep：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-19-37-27.zip`
- B N=5：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-19-37-39.zip`
- Combined report：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-23-49-34.zip`

ZIP均含BUNDLE_INDEX.json：每file原始relative path、bytes、SHA。解壓到新的
目錄，不覆蓋既有工作檔；內部summary仍記原C槽路径，以bundle index定位
portable copy，不把metadata路徑重寫成新的immutable manifest。
不包含raw/formal source data或credentials。Archive indices（Git保存）完整路徑：

- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_archive\2026-09-30-19-32-44\archive_index.json`
- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_archive\2026-09-30-23-49-43\archive_index.json`
- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_archive\2026-09-30-20-05-02\archive_index.json`
- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_archive\2026-09-30-23-53-04\archive_index.json`
