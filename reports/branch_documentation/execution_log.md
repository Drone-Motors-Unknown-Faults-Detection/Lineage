# Docs #11 與 main TODO 交付紀錄

2026-10-02，Asia/Taipei。研究 checkout：
`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`，
branch `research-improvements-20260920`；起點 HEAD `e35abd12c4f257da8173f1a750dedb10d99b0ab7`。

## GitHub 規定與目前工作

- 完整讀 main/AGENT.md，blob `f3b92347582bceff98ede6513f06458cdefdeac5`；同步到研究分支。新增實驗或改方法／切分／指標先寫 docs/experiments 對應手冊，兩份 docs 索引列入；記錄方法、文獻、預期反駁判準與程式範圍。
- 指定李思萱文章的 web.open 失敗；正常公開 HTTP 可取得，已讀完整 articleBody。沒有保存／轉載文章全文，也沒有繞過付費牆。
- #11 指派給 05zhi，原 checklist 兩項：分支 md 與 README/docs README。新增分支總覽、schema 說明與9份模組手冊、兩份索引並更新 root README。既有程式的手冊明示補寫日期，不冒稱早於實作。
- main 已有大寫 TODO.md，未另建 todo.md。保留 #9/#11/#13–#16 原清單，新增當前研究工作。先更新 TODO（commit `5627ee6b6c14be808a210c47ce6dc4122b1167a3`），再建立指派給05zhi的 #22；回連 TODO（commit `82cccac6958b255a7e6ce18c6e458c189139aa58`）。
- GitHub MCP update_file/create_issue 回傳403（integration 權限不足）。已授權本機 gh CLI 的正常 API/issue create 成功；沒有變更 remote／登入／安全設定。遠端 TODO 更新用原 blob SHA 比對，避免覆蓋並行變更。

## 檢查與測試

- 新增12份 docs（2說明＋9手冊＋1索引），45個本機 Markdown links，missing=0。
- Python3.10.19及3.14.6各執行 `python -m unittest discover -s tests -p 'test_synchronized*.py' -q`：17 tests PASS；`test_fault_type_continuous_report_v2.py`：2 tests PASS。每環境合計19；没有重新跑全套，先前376不當成本輪全測數。
- 每環境核對9個所寫模組的 --help，全部 exit0。實際 CLI 接口與手冊相符；fresh實體資料範例不聲稱已存在。
- 起初誤用 pytest，兩環境均回 No module named pytest；改用 repo 既有 unittest，沒有安裝依賴。近常數 synthetic signal 的 scipy precision-loss warning 保留，測試為 PASS，不當成真實信號品質判定。
- 修改前後 formal105／LW／k-NN／PolarMap 沒有程式或資料變更。v2 report 已有的空白行格式修正留在未stage研究改動；282 unrelated tracked deletions完全不stage。
- diff --check 無 whitespace errors（只有 Windows LF/CRLF提示）。只 stage 本項確認文件與research_state，不 stage raw、models、predictions或其他人修改。

## 研究 checkpoint

Q evaluation `output/fault_type_continuous_evaluate/2026-10-02-18-47-45/evaluation.json` 存在，seal `b4ef4ce09bc85969f90d81158acb4bcfd0c5c2f1492feb6530e0386558abf2de`；72 planned、60 completed、12 INCOMPLETE；576144 records、28910 unique，95.618秒。這是讀 aggregate 的核對，尚未獨立 verify/report，未宣稱完整性能驗收。

原持續研究 goal 顯示 usageLimited；本次先完成新授權的 Docs/TODO/issue 工作，未啟動新訓練批次。下一步命令保存於 continuous_research/research_state.json 與 study 手冊，不標可靠性完成。

## Git 交付

首次 staged diff --check 找到 smoke/acceptance CLI 行尾空白，提交程序 exit2，尚未commit/push；已刪除兩處空白再檢查。文件commit／push及issue完成狀態在下一筆同步紀錄追加，以實際回傳 SHA 為準。#11 只在研究分支文件push核對完成後關閉；main只更新TODO，不合併整個研究分支。

- 文件提交 `2f15c797d2adb43b0103629783c7dd4baba03138`：17個確認檔案，staged diff --check PASS。正常push成功，local/remote同SHA；GitHub contents API讀固定commit的分支總覽確認文件存在。
- #11原兩項checklist皆勾選；交付comment `https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/11#issuecomment-5955386278`；state=CLOSED，2026-10-02T15:12:17Z，reason completed。沒有關閉#9或把研究驗收寫成完成。
- main/TODO完成標記commit `b623d35a7185740653e882ad5ce24e185e8c207f`，blob `858f9dfe27b385573ec7a638545a8d57596efa66`。#22仍open，只勾選已交付的文件／手冊，verify/report/備份／下批研究仍待辦。
