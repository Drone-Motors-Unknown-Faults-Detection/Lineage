# 研究收尾執行紀錄

日期均為 Asia/Taipei。研究分支為 research-improvements-20260920；本回合起點 9aba063e82c4a61228cd4e46c21a927abddc56c0。最新使用者要求有界收尾，取代先前持續搜尋至成功的要求。

## 證據盤點

完整閱讀此 checkout 的 AGENT.md 與各批來源／結果索引。指定寫作文章本回合取得失敗，web 回報不可重試錯誤；不宣稱本次已讀，依 AGENT.md 列出的五項規則撰寫。先行手冊與兩索引 commit 4fb72015d8461846d90f19dd9fac7e25dcd56a8e 已 push，遠端 ref 與本地相符。

22:28:40 的首次盤點完成 12 批。新增 manifest 支持筆數重算及方法 ID 重複拒絕後，22:34:03–22:34:48 重跑唯讀盤點；正式特徵未重新載入、沒有 fit。權威盤點為 output/fault_type_research_closeout/2026-10-05-22-34-03。method_catalog.json.gz 原樣保留 sealed 方法、參數與全部 seeds，包含來源物件，不把歷史限制敘述重新包裝成新結論。未壓縮 93 MB 中間檔留本地，不提交 Git。

Python 3.10.19 與 3.14.6 分別執行 `-m unittest tests.test_fault_type_research_closeout -v`：各 9 項通過、0 失敗。涵蓋 SHA／seal 篡改、缺項、全部 seeds、重複 ID、detector 配對與 A／B 判定。先前 7 項也通過；9 項是新增檢查後的有效驗收。原 618 項科學測試在 2026-10-04 雙環境已通過，本次未重跑。

M 已有 216 completed、2,081,520 records、28,910 unique rows。22:17:39–22:27:41 僅補既有 report：1,134 配對，24 方法全部 FAILED。沒有重訓、重新選模型或調整契約。

22:24:22 及 22:28:54 新增六份 D 槽備份；22:32:32–22:32:36 fixed_delivery 核對 6 ZIP／468 members，whole SHA、member SHA、CRC 均 PASS。原檔與舊備份保留，同機 D 槽不稱異地備份。

既有 282 tracked deletions 均未 stage。正式 105 維資料、Mahalanobis–Ledoit–Wolf 預設、k-NN factory、PolarMap 與五份 sealed M 來源不改。
