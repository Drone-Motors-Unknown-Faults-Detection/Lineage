# 三軸排列核執行紀錄

2026-10-03，Asia/Taipei。先讀AGENT.md及寫作規則；exp18正執行324評估。本批原始TI paper已讀32頁；exp19手冊及兩索引先寫，尚無新core／runner／formal fit。下一步手冊commit／push後實作公式與合成測試，再建立source／purpose runner。原正式預設與282筆無關tracked deletions保留。

尚未執行81 detector評估，不宣稱新方法提高分數。方法依歷史失敗與文獻事前固定；所有28,910資料已曝光，無fresh或可靠性PASS。

先行手冊commit `c307712f86453da39d86c86809f315c3e3474705`已push／remote一致，才新增core／tests。2026-10-04接續實作，兩native環境各23項formula／source小測試通過，Python3.10.19本體0.080秒、Python3.14.6本體0.105秒。涵蓋共享尺度交換、六項等於36項平均、對稱／PSD、核對角非1、SVC確定性／nonconvergence拒絕、actual train重fit重建與重封coeff拒絕、private coeff tamper、centroid手算／q0／NaN／overflow。此階段尚無runner／formal fit；全套回歸待runner實作後執行。

core階段commit `9f11645d0f0f16aabf3f2148e2359426640c8f24`已push／remote一致。runner共用G的已驗證來源、保存、逐筆metrics／replay流程，不修改sealed G／H／I／J。初稿report仍有G的prototype variant配對欄位，靜態審查於formal lock前修正為固定alpha0消融，新增42配對組合測試；沒有任何formal結果需作廢。

兩native CLI help與smoke通過，output `fault_type_axis_kernel_smoke/2026-10-04-16-33-02`／`16-33-12`，只SYNTHETIC_ENGINEERING_ONLY。新runner／用途／actual source加10測試，兩環境各33小測試通過（本體2.458／2.655秒）。涵蓋重封cal threshold、變動known cal／factory reference拒絕、unknown／test motor進development拒絕、三拒絕器classifier共享、nonconvergence INCOMPLETE、global winner／假fresh拒絕。

J完整結果交付commit `e471393f0e77054c98e18f8853244a4466affef4`已push／remote一致。2026-10-04 16:41:57／16:41:58開始本批完整acceptance，結果待完成後記錄。新kernel／runner未formal lock／fit，沒有用J外部成績挑alpha或門檻。

完整acceptance完成：Python3.10.19於16:43:56、Python3.14.6於16:44:07，各553 tests通過、0失敗，unittest本體63.772／64.776秒。各39命令exit0，包含pip check、unittest及37既有CLI；新exp19 help／smoke另外核對。工程驗收產物`output/fault_type_continuous_acceptance_py3_10_19/2026-10-04-16-41-57`及`...py3_14_6/2026-10-04-16-41-58`。先提交推送runner／回歸證據，再lock協定；此時formal K fit／outer均0。

工程commit `72c7d61b4b248043e2de83469f6b30e631f1cfe9`已push／remote一致。16:46:00–16:46:22執行手冊lock，protocol `output/fault_type_axis_kernel_lock/2026-10-04-16-46-00/protocol.json`；semantic checksum `2dab6753530bc6736b88881b57e61d9488253ceb9a459276b3fcd0d8b0f00abf`。固定81評估／27分類器、alpha0／0.5／1、gamma1/66、完整SVC／shared scaler參數、三motor角色／seeds及原CONTRACT；各implementation SHA封存，不修改sealed程式或手冊。協定commit／push後才formal fit。

協定commit `060fe0e3807132c77151bb6fb0b5c62c9f5fc1ca`已push／remote一致，才於16:47:14開始formal fit，16:52:33完成27／27分類器、0失敗。模型與逐fold／seed fit audits存D槽`lineage_fault_type_artifacts/2026-10-04/axis_invariant_kernel_v1/workspace/output/fault_type_axis_kernel_fit/2026-10-04-16-47-14`。C槽compact lock與D槽SHA均`f8d112cd6001370e57f786f3c87b339f8ae96eb3ac146f3b6de3cdead6392315`；locked checksum `21f30fb76c1bdcffcdb25a956afe7c8a46fe26497a0f2bab99b0d2f601636f49`。

16:52:44–16:59:50完成9個fold／seed bundle的actual known來源重建，27 classifier全通過。source proof `output/fault_type_axis_kernel_source_verify/2026-10-04-16-52-44/source_verified.json`，semantic checksum `8e19b4cebac79443fe60f6345424fcc2f655af4bf8c9c39ed1b9282bb32324ee`，test_numeric_reads=0，90CSV fingerprint前後皆`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。原始session／window獨立性仍UNKNOWN，fresh final guard仍INCOMPLETE。先提交推送本段來源證據，再開始81配對outer；此紀錄尚無K test成績。

第一次合併stage／commit請求遭安全檢查拒絕，理由為可能一併提交無關刪除；唯讀檢查證實staged_count=0，282刪除全未stage。改為先只stage7份K來源檔案、逐項核對index，再申請提交與push；未unstage、恢復或stage他人刪除，安全檢查通過。來源commit `c5b1f88e0e2dbbe5adee8a1ad00344ab540972a5`已push／remote一致，才於17:04:00開始outer。17:08:46完成81／81、0失敗，780,570筆prediction records，unique samples仍28,910；272.429秒。evaluation seal `1d87b45bc16b64ca41580120fcf10354526bcbd962b69e51ea58817ad5e07d92`。17:09:01開始從封存模型逐筆重推，驗證完成前不宣稱交付或可靠性通過。

17:09:01–17:17:12逐筆重推完成，476.732秒，verification seal `0653d9bcfe97268048a3e9f6c9cbb9ae1d46435c8eea89144d45c028ac62b408`；所有81預測、metrics、工況及truth mutation核對通過。21:32:27–21:34:01產生13方法表（9K＋4controls）、378配對，report seal `4ae0663e984090036e8318849d4f584fb0662ff02b13591ed3d5d454a2a70c87`。9K的CONTRACT全部FAILED、最差類別recall均0、最差RPM健康總誤報均100%；K09 T1 unknown46.600%但健康總誤報83.451%，不能採用。三seed預測／指標一致，非新增採集。

21:33:45 D槽三primary root封存，21:36:20 C槽protocol／source／report三root封存；21:36:37–21:36:38 fixed_delivery確認6ZIP／198members全SHA／CRC PASS，保留原始outputs，D槽單volume非offsite。正式預設與他人282刪除沒有動。報告含全方法／三seeds／motor／RPM、來源改編、失敗解釋、老師建議與完整SHA索引。eval／verify／summary的compact gz只精確force-add這三檔，不stage大模型／逐筆predictions或正式data。最後push結果commit與remote SHA核對另記後續接續log。
