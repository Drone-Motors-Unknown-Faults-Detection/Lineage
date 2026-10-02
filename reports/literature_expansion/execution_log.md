# 文獻擴展研究執行紀錄

2026-10-02 Asia/Taipei；接續 eb324595d76774556662d1d6d5ea810e0bb1392c，research-improvements-20260920。完整閱讀 AGENT.md，核對先前198次實測與備份索引，不重跑2490次歷史研究。正式90CSV/28910row指紋預期 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。保留282個既有tracked deletions與無關未追蹤產物。

## 文獻／協定與工程測試

查核28項原始文獻／作者來源，sources.md記採用、改編與未實測理由；另查官方sklearn1.7 NCA/OAS/GMM/LOF文件。部分出版頁抓取403或失敗，明列替代預印本與未完整取得內容，沒有宣稱完整逐篇通讀或將外部benchmark成績移植到本資料。

固定24 pipelines×2正式detectors＋22額外score variants，3fold×3seed，共630 logical evaluations；方法固定且無selector。不保證分數改善、無界「所有方法」未宣稱完成。所有方法同一healthy＋5known／4unknown與3motor角色。閾值僅known cal，不用test搜尋。改編在本輪test前固定，但參考已曝光歷史結果，仍exploratory。

首次23項小測試21通過、2失敗：NCA subset的numpy int64不支援JSON封存。已改為Python int；沒有任何正式fit/test受影響。準備階段也發現factory參數名應為knn_neighbors而非n_neighbors，已修正後才測。保留初版registry 2026-10-02-01-19-40日誌作工程痕跡，不能當作最終source SHA契約。

正式預設105維／linear／Ledoit–Wolf Maha與PolarMap、kNN切換均未改。歷史sealed code、models、manifests、報告不覆寫。新模組／報告／output獨立版本；大型bundle/predictions循D槽archive慣例，Git保留compact report、locks及SHA索引。

增加保存預測來源／SHA／truth／score方向／曝光及summary tamper測試，共31項新測試通過。首次synthetic01-21-41在執行期間程式修正後被source SHA guard拒絕，保留該工程輸出，不拿部分結果做研究。未更改候選方法；重新以穩定程式完成01-23-17 synthetic630/630、0失敗、226800筆保存預測與sealed重推論完全一致。修正synthetic每類12row時C24不必要的min15要求：最低5，只有knn15 classifier要求15；正式資料沒有因此缺格或調分。

Python3.10.19與3.14.6初轮各295項完整測試通過、pip check與16個舊CLI help通過；增加8項tamper測試後再次全套驗收，最终實數另列。3.14讀3.10舊synthetic protocol被runtime參數契約正確拒絕，改用已存在3.14自己的fixture/index重fit，未解除guard、未cross-load joblib。

最終準備protocol：output/fault_type_literature_registry/2026-10-02-01-26-16/protocol.json，bf98e897a1d984a8e72e521cb184636f3d1e2df6cd377b071ee2a1d99670f4ba。候選、公式、係數、seeds與sources SHA都在正式fit/test前封存；先提交推送工程／protocol，再做正式fit；封存fit後再提交推送lock，才執行test。

P0文獻／界線文件commit25f05965b9d7e7ba68d01bfd6f4f198f7de5fa5c，push成功，local=remote。最新完整驗收：3.10.19在2026-10-02-11-57-44、3.14.6在11-59-05各303 passed/0failed，pip check与16 legacy CLI PASS。31項新單元測試覆蓋七種表示法、全部分類器、signed score、參數固定、未知/fit用途、防tamper。3.14使用自己的既有fixture，在11-57-36完成630synthetic、0失敗、226800保存預測／sealed重推論；與3.10的01-23-17相同工程矩陣，兩者不是研究成績。另新增literature_acceptance收錄4新CLI help與完整驗收。

## P2：正式模型鎖定，尚未評估test

工程／事前協定commit94487305f9ba648705e195cfb69bfa70d08b880b，push成功且remote=local；正式fit於12:01:19開始、12:04:42完成，exit0。只讀known train/cal，validation與selection IDs空、未評估test。9個fold/seed bundles；234次分類器node fit、81次表示法fit、180次官方factory reference fit、174個額外score物件建立／校準（其中MSP/entropy等不是額外獨立訓練的模型）。fit前後90CSV指紋相同。

鎖定檔：output/fault_type_literature_fit/2026-10-02-12-01-19/locked_study.json；lock checksum48ba96ab8c3eb8b2a4a25e8a17a95b5083e2e6f6318aba6bdd6e08b1b9be44da。R17 predicted-class calibration在fold0與fold2各三seeds缺少至少一個預測類別校準群組，六格INCOMPLETE，不fallback、不借test或真值補校準；其餘方法可評估。630為計画格數，不預稱630成功。

最新完整驗收：output/fault_type_literature_acceptance_py3_10_19/2026-10-02-12-00-09與py3_14_6/2026-10-02-12-01-27，各303 passed/0failed，pip check PASS，20個CLI help PASS（16舊＋4新）。3.10.19進行正式科學比較；3.14只做自己的工程相容性fixture，不跨版本載入joblib。

大型正式fit已備份至D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-02/literature_expansion/fault_type_2026-10-02-12-01-19.zip，628817824 bytes、11個來源檔，archive index位於output/fault_type_archive/2026-10-02-12-07-35/archive_index.json。兩份synthetic630也保存到同目錄不同名稱，未覆寫舊研究備份；封存CRC通過，最終交付將再次逐member驗SHA。

補充Cox、Shannon、MacQueen與官方scaler來源列入sources_addendum.md；不修改已封存sources.md，不改protocol或係數；追加書目本身不構成新實驗。此階段提交並push模型lock與工程驗收後，才開始正式test推論。
