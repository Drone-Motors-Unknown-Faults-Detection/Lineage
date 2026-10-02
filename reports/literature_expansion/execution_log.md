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

P2 lock commit acf8c7e771546f658f72b5b4d8463c06dc3f2eca，push成功，local=remote；protocol+lock與234個fit audits額外驗證PASS後，於12:09:14啟動正式evaluate。封存模型和方法程式未更改。

新增非封存方法範圍的只讀診斷模組fault_type_literature_diagnosis，固定比較C01/C02/C17、R01–04/R18–20的train／cal／test分數分布，不fit、不掃閾值、不新增方法評估。新增四項工程測試檢查signed/zero門檻、真值僅報表分組與非有限值。首次import路徑誤写experiments而非core導致1個loader error，修正後4/4通過；正式evaluate不引用此模組，未影響研究程式／protocol SHA。完整相容性验收加入第五個新CLI後重跑，最終測試實數以新environment.json為準。

新診斷工程驗收：3.10.19於12:11:25、3.14.6於12:13:16各307 passed/0failed，pip check及21 CLI help PASS。診斷metadata再加入data_scope／自身source SHA，四項相關單元測試再次通過，12:15:03 synthetic診斷CLI成功，351個分布集合（13固定方法×9bundles×train/cal/test），models_refit=false、thresholds_modified=false。不是351次新研究評估。8MB診斷JSON留外部archive，Git留索引output/fault_type_archive/2026-10-02-12-15-21/archive_index.json；不把synthetic分數當馬達研究成績。診斷初版12:12:53仍保留、不覆寫，交付引用data_scope明確的新版本。

診斷程式commit994505391a0c201a010a5624223fcb1333bd8f34，push成功local=remote。追加metadata後全套驗收12:16:09（3.10）及12:19:45（3.14）仍各307 PASS。

## P3：正式評估與逐筆重推論驗證

evaluate於12:09:14–12:16:07完成624/630，六格缺失均有封存R17 fit理由；6,013,647筆預測，unique test仍28,910。evaluation checksum294a41c2a6c870c89e77c957402ce3764ddc96a1a126d24eeeeb1067f10cf0cb。來源90CSV前後SHA／指紋相同；無selector或test調參。output/fault_type_literature_evaluate/2026-10-02-12-09-14/evaluation.json，39MB完整逐run來源索引與625檔保存預測於D槽新ZIP：554478066 bytes，CRC PASS，索引output/fault_type_archive/2026-10-02-12-16-43/archive_index.json。verify於12:16:33開始，用封存模型重推論所有保存樣本，不僅重算summary；完成狀態後續追加。

核對歷史控制範圍：C02/A0為同混合RPM完整pipeline。C24/A7分類器／表示法／train相同；但歷史A7只按RPM分classifier，共用mixed-RPM A1 detector reference；本輪事前寫定的C24也按RPM分detector reference與cal。不能期待所有開集指標一致，也不能用該差異宣稱純分類器效果。報告新增classification_matches與expected_entire_method_match，把實際差異全部保留；此為報告解讀修正，不改方法或重跑挑分。新增三項報告範圍測試全部通過（完整測試應為310，依最新驗收实數確認）。sources.md與protocol保持封存原文，新增说明不冒充事前資訊。

報告解讀修正後最终完整驗收：3.10.19（12:21:11）、3.14.6（12:22:05）各310 passed/0failed，pip check与21 CLI help PASS。新科學方法／協定程式已封存且未變；310比原272多38項工程測試。本階段提交報告檢查程式與測試、完整驗收、已完成evaluate日誌及D槽索引；不stage39MB evaluation或625份大型預測，全部可由archive index恢復驗SHA。

### 解讀勘誤（以上A1 mixed-RPM敘述已撤回）

71787fe394ef8a77e034a56357298815ddea7ac8已push且remote相同，但該commit報告注釋誤把歷史A1說成mixed。12:25完整控制report實際四組matches全部true，引發進一步來源核對：experiments/fault_type_accuracy_registry.py:25明列A1 rpm_strategy=separate；:31 A7 reference_arm=A1。舊summary的A1/A7 Maha AUROC同為.538823773312093，與本輪C24完全相同。結論：C02/A0與C24/A7均是完整pipeline控制；共享A1不等於混合RPM。前述差異推測不成立，已向使用者更正，不再當成已確認問題。

更正報告說明及三項範圍測試，保持310項總數；不改sealed study code、protocol、模型、分數或門檻，因此無受影響研究runs需要重跑。output/fault_type_literature_report/2026-10-02-12-24-31保留為SUPERSEDED_INTERPRETATION_ONLY，數值沒變但注釋錯誤；以新timestamp report交付。來源／數字的實際核對優先於對話線索與代理的先前印象。

正式verify於12:24:15完成624 available結果、6,013,647逐筆預測與sealed模型重新推論完全一致，source前後不變。verified.json.gz checksum索引與新report／只讀diagnosis後續列交付索引；沒有fresh test或獨立來源資格提升。

## P4／P5：更正後結果、診斷與交付核對

更正後report於12:26:09執行，summary checksum be1ae2f68ace1e9420b69e2d8269be6d1821d881ff8654aea4c175367db06f49；C02/A0與C24/A7四組全部18項指標matches=true。verified report seal efb92da2c9fa1007829c83c9c3aedb41b390046bfa3ef65b5366f8d7c97928be。只讀正式diagnosis於12:24:42–12:25:59成功，351分布集合，data_scope=EXPLORATORY_HISTORICAL_TEST_EXPOSED，diagnosis seal a02a8068515e8057ac0129bd4c16381c6d640c5b178f4a69b8fe6e5c2efcb5da，無refit／threshold改動。報告與診斷D槽archive index為output/fault_type_archive/2026-10-02-12-27-10；verified archive index為12-24-52。

最终程式（含RPM解讀勘誤）完整驗收：Python3.10.19與3.14.6均12:26:34啟動，分别12:27:56／12:28:02完成，各310 passed／0failed、pip check及21CLI help PASS。保留早期307／310的工程日誌，不以舊驗收冒充更正後結果。研究sealed implementations及defaults均未改。

12:27:43執行fault_type_fixed_delivery，8archives／1935member的whole SHA、CRC與所有來源member SHA PASS，沒有刪除來源。member_verification.json保存output/fault_type_fixed_delivery/2026-10-02-12-27-43。新ZIP全部位於D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-02/literature_expansion，不覆寫舊ZIP，不將同機D槽副本說成異地備份。

數值結論：C17 healthy+known accuracy39.2863% vs C02 34.1532%（+5.1331pp）、fault-only30.4315% vs26.6126%（+3.8189pp），未超過歷史C24/A7 fault-only30.9091%。R09 AUROC .604251最高但T1 recall0、T2/11000健康拒絕100%；R18 recall22.6793%／healthy unknown-FPR9.4941%，不能只報召回改善。C17/M健康unknown-FPR0不包含healthy被classifier誤分known fault（T1該錯誤31.5843%）。所有弱結果與失敗均保留，正式default不替換。
