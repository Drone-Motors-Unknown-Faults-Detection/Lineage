# 驗收、來源與 Git 交付

2026-10-02，Asia/Taipei。研究工作樹：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`；分支 `research-improvements-20260920`；remote `https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage.git`。

## 驗收判定

- VERIFIED：九個完整方法／81正式評估，0執行失敗／0缺格；780,570逐樣本紀錄全部重新推論、指標重算與來源SHA核對。仍只有28,910個unique samples，不是780,570個獨立樣本。
- VERIFIED：unknown不fit/cal；train/cal/test不同motor；selection IDs空；方法、參數與校準規則評估前鎖定。checkpoint重播保持sealed lock/evaluation原檔SHA。
- FAILED：九方法各有至少一個motor×RPM的健康完整誤報超過暫定研究10%條件；最差健康誤報100%，T1 unknown recall仍0%。不取test最佳閾值，不替換正式預設。
- INCOMPLETE：全部現有資料已歷史曝光，每折只有一test motor；未滿每類至少兩test groups。新seed、新檔名和新protocol不構成fresh final test。
- UNKNOWN：recording/session、raw-window區間／重疊、刪點遮罩、實際單位／取樣／安裝／負載。文件支持T1/T2/T3三顆不同motor；沒有序號不抹除文件證據，也不能分離個體與老化。

## 測試與效能

Python3.10.19（science，sklearn1.7.2）與Python3.14.6（compatibility）各349 tests PASS、0 failed；pip check與28 CLI help各PASS。命令：`.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_acceptance`；`venv/Scripts/python.exe -m experiments.fault_type_mechanism_acceptance`。

科學數字僅使用3.10的模型；3.14使用native synthetic smoke，不跨sklearn載joblib。合成數據只驗證工程，不列研究分數。三seeds=0/1/2逐筆數值完全相同，無估計獨立採集變異。

正式fit27個P分類器／9個block geometry；初版test前修補後另保留27／9舊fit，不暗刪嘗試。本輪新評估仍81格。fit process peak 1,988,251,648 bytes，含載入父模型，不是單方法增量；evaluation記錄79.2942297秒，含必要計算／輸出但不含所有preflight牆鐘時間。九方法共用bundle inference約7.08738秒，不能拆成九份獨立時間比較；旧控制耗時不可得，報null。

## 備份與恢復

新備份目錄：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-02\mechanism_research_v2`。14 ZIP，共480,240,398 bytes、301來源檔。whole SHA／CRC／逐member SHA均PASS。source_files_removed=false；舊literature_expansion八包SHA不變。單D磁碟不是offsite備份；formal data與source raw ZIP不重包。

兩份archive_index：`output/fault_type_archive/2026-10-02-18-03-58/archive_index.json`、`output/fault_type_archive/2026-10-02-18-04-29/archive_index.json`；完整驗證：`output/fault_type_fixed_delivery/2026-10-02-18-04-44/member_verification.json`。result_index列絕對路徑／SHA；壓縮包的manifest記錄原始source paths與member SHA，恢復到新目錄後需按manifest對照，不直接覆寫舊結果。

## 階段提交（均已核對remote exact）

| 階段 | commit |
|---|---|
| P0 inventory | af380efe78ef3b51bc1d0c6dbda4f505c8b1ac2c |
| P1 metrics | def53146e3881eb284a52c1f650e7886108a6f07 |
| P2 diagnosis | 93b98075170f16cb64c94d1a71db10607a8f91a4 |
| P3 literature | b55a5b913d831dcbded263328d4771672c10764e |
| P4 protocol/implementation | d2548fa811b69f5b64329bc2bfbe938f6043f542 |
| Pre-evaluation resume fix/reseal | 8bcbb53405105d313bebcbfd291935430b53e81e |
| P5 train/cal lock | a724dbc693cd87280593ee64dacb31259486d99a |
| P6 evaluate/verify | b3df4063ce810d801fd27288412ee0fe81939227 |
| P7 report/349 tests | cec005b91c539df762704f39ade85c5ae45bda2f |

P8本檔／sealed結果索引／備份索引為最後交付提交；提交自身SHA不能寫入自身，最終回覆以git rev-parse與git ls-remote實際值核對。不force push，不新PR或跨聊天室傳訊。

正式105維／linear／Mahalanobis-LW預設、core.openset factory、binary detection與PolarMap未改；原282 tracked deletions與無關dirty files保留，未提交。完整老師建議對照、逐motor/RPM/class及負面結果見final_findings；本輪不聲稱重跑歷史2490格或所有N配置。
