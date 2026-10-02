# 執行紀錄

2026-10-02 Asia/Taipei。P0：完整讀 AGENT、附件、literature五份說明/結果索引、accuracy及fixed-calibration索引，閱讀實際representation/classifier/score/fit/cal/verify/feature讀取與metric程式。起點791ee5b，17 artifact SHA、9 model SHA、234 audit與formal SHA scan PASS。847原dirty entries/282 deletions保留。psutil不可用，使用stdlib作業系統記憶體介面；無新增系統安裝。未重訓或改指標舊檔。

原科學限制維持：全部舊資料曝光、三顆不同motor、age與individual混雜、raw/session未知、test群組不足。各阶段commit與push實際核對後追加，不預寫成功。

P0 commit af380efe78ef3b51bc1d0c6dbda4f505c8b1ac2c 已 push，remote ref 與 local 一致。
P1：13 個 metric v2 cases PASS。624 組 / 6,013,647 records / 28,910 unique 的舊預測重算 exit 0；未訓練/重推模型。2026-10-02-12-51-52 的 metric seal 19c1dd6b5a27d5de6c3ec8898f24123cbb68252f2e774a19141586fabf6ae59b。舊 healthy unknown-FPR 與新互斥項相符，新增完整健康誤報揭露 C17 T1/8000 =100%。無門檻調整。保留 R17 六格不足與舊報告。

P1 commit def53146e3881eb284a52c1f650e7886108a6f07 已 push，remote exact。

P2 commit 93b98075170f16cb64c94d1a71db10607a8f91a4 已 push，remote exact；16相關測試PASS（13 metrics+3 diagnosis）。
P3 actual web 原文搜尋/方法查閱，17候選、7篇methods/settings深讀，其餘閱讀限制明列；既有31筆full-cover均未取得完整閱讀證明，不補造。原RDA掃描/官方存本抓取限制及Vaze全文timeout如實記錄。採用3機制，其餘延後/缺資料/越界分開。

P3 commit b55a5b913d831dcbded263328d4771672c10764e 已 push，remote exact。
P4/5/6工程：新增9arms train-only數值類、來源綁定registry、分離fit/cal/infer、逐格SHA checkpoint與reinfer。直接相關34新cases（13 metric+3 diagnosis+18 mechanisms），預算81。合成smoke兩runtime PASS，不算研究。protocol seal 4db05bc722e49ecb6421beaa072f21216ab795d8b180c3fcb441d0d7fe230743，未執行新outertest。完整acceptance實際測試數另依產物記錄。

完整acceptance：Python3.10.19與3.14.6各344 tests PASS、pip check PASS、27 CLI help PASS。產物2026-10-02-13-09-31/13-09-43；synthetic13-09-54/13-09-56兩native runtime PASS。未跨sklearn載joblib。

P4初次提交被auto-review額度限制拒絕，指令未執行；使用者繼續後正常重試，d2548fa811b69f5b64329bc2bfbe938f6043f542已push/remote exact。
17:46-17:47完成pre-evaluation9 fit bundles、27新P classifier/9 geometry、0 warnings，peak process 1,987,735,552 bytes（含大型parent）；lock 88a15375583b25512d11f7fc715a2c420dfa2f4a3cad5a4e4ada7b4cf6b67ffc。尚未評估outertest。
發現resume aggregate會重寫sealed總索引（checkpoint本身正常），新增save_immutable＋重現測試；舊protocol/lock完整保留，不覆寫。需要新source SHA協定後重新fit，不算新增arm，不新增test評估；正式81格仍尚未執行。

修補驗證：science相關35 PASS、3.14 mechanisms19 PASS、report3 PASS。新protocol17:49:29/ff6ddc29ca101f73c8a3ca6f818147dc4f6cd81032581966757b5f72087e1b91已生成，未看新outertest。新版report以within-fold AUROC/AP作sample-weighted平均，不混跨模型raw score排名。

修補/新protocol commit 8bcbb53405105d313bebcbfd291935430b53e81e 已push/remote exact。
正式新fit 17:50:41–17:52:29，9 bundles、27 P classifier fits/9 geometry、0 failed/0 warnings；lock c1d47ead2bbeeb8d82fb63fa5040272cd732a504ccaac0a182a1b8ed083278e1。fit source前後SHA一致，峰值1,988,251,648 bytes含parent，非單arm增量。全套348 tests各runtime PASS，CLI仍在執行時未宣稱最後完成。外部大型models/audits稍後獨立備份，不入Git。

P5 lock commit a724dbc693cd87280593ee64dacb31259486d99a 已push/remote exact。
P6 17:53:06–17:54:37，81/81新evaluations、0 failed/INCOMPLETE、780,570 records/28,910 unique，data前後不變；evaluation seal 2ff6fdca458d449254cbcc83259719d8d91562db82105712c07f64f99b809076。
17:55:10–17:56:37 verifier全部81/780,570重新inference exact，controlled truth mutation invariant；seal 1ff5c7fdb4df8b8cc64810858b58fd0067fa618b9f85c2d87103068192d17a9e。
fit replay17:54:16與eval replay17:55:59 PASS，原sealed總檔SHA不變、不計新增研究runs。全套348/348兩runtime、pip各PASS、28 CLI各PASS（30 commands含pip/test）。
初配對report17:56:50 16方法/243paired條件 PASS，D系列逐筆classifier/score與父控制exact；補充post-rejection/precision/F1與未測runtime=null後輸出新report，不覆蓋初報、不改模型/門檻。

P6 commit b3df4063ce810d801fd27288412ee0fe81939227 已push，remote與local exact。
P7 authoritative report17:58:59，seal 69e4b6d126dc1129ed2bceb0c1ff6621a946a263496bc72c1f859bbe9a6f40a8；16方法、243 paired comparisons，沒有global winner。全部27個arm/fold的3seed逐筆pred/score/threshold/reject完全相同，無seed敏感度，非新增獨立motor。
最新版全套：Python3.10.19及3.14.6各349 tests PASS、pip check PASS、28 CLI help PASS，各30 commands/0 nonzero。產物18:00:37/18:00:48；不跨sklearn版本載入模型。349=既有310+本輪39；native synthetic只作工程測試。
P8：18:03:58/18:04:29 archive indices保存14新ZIP，共301 source members/480,240,398 bytes；18:04:44全包whole SHA、CRC與逐member SHA PASS。D槽新mechanism_research_v2目錄，無刪除源檔，未覆蓋舊8個literature_expansion備份，另核對舊8 SHA全部不變。單D磁碟非offsite。
原正式core/geometry.py、monitor.py、data.py、openset.py、mahalanobis.py相對起點無diff；formal fingerprint不變。282 tracked deletions仍保留，不stage。大型模型、逐樣本prediction及full summary只外部封存，小型摘要/索引/執行日誌入Git。
P2 只讀診斷 exit0；3 個 seed0 parent models，formal source 前後一致，無 fit/threshold 修改。兩圖檢視，2screws train=100%/test=0%；R17 真實 cal 各類足量但 predicted routes 空。形成 H-D/H-P/H-G，未知採集事實不補造。
