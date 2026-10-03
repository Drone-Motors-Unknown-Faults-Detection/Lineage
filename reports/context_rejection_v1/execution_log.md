# RPM原型拒絕執行紀錄

2026-10-03，Asia/Taipei。先行手冊commit `4951a3138949c827e0e005c8acafa6a7c6a1ac13`已push／remote一致，才新增core／tests。當時exp17 outer仍執行，沒有讀I成績挑父模型。

20:43左右：兩環境core最初12項測試均通過，Python3.10.19用0.003秒，3.14.6用0.002秒。後續靜態檢查加上距離和overflow拒絕與測試，不更改cal quantile或score定義；在協定前修補，尚無本批formal結果。下一步runner需完整purpose／SHA／來源重建與paired replay，不能把core測試當作已執行324評估。

core／13項測試commit `eb26d9756d69b8ab1a8edc6ded1f152a0a26c502`已push／remote一致。runner沿exp17既有來源、保存、指標與checkpoint流程新增獨立module，不修改sealed I／H／G、沒有monkeypatch。查核發現初稿evaluate/report變數命名替換不完整，兩處改回context，新增空矩陣用途gate回歸；未執行任何formal校準或outer，沒有版本化結果需作廢。

兩環境CLI help及smoke通過，output `fault_type_context_rejection_smoke/2026-10-03-20-46-49`／`20-46-51`；smoke只SYNTHETIC_ENGINEERING_ONLY。source/purpose測試涵蓋actual cal重建、changed train/cal、重封threshold/prototype、node inventory、unknown/test motor污染、cal進parent fit、global selector／假fresh／改q拒絕、相同三scores classifier與OR邏輯。

首次runner兩環境各25項通過（2.042／2.042秒），加policy／固定參數後27項通過（2.053／2.007秒）；完整acceptance於20:49:47／20:49:58執行，兩環境各519通過、0失敗，39命令exit0／pip check／37既有CLI。產物已隨I結果commit `9b5e0e398556dee1bd32befbacb31c6dec11a28d`push／remote一致。沒有用519倒填I fit前492。

再補每筆context_distance／context_ambiguity／calibration_quantiles／rejector state與mode；tamper測試成28項，兩環境通過（1.999／2.037秒），因此再次完整acceptance；最終實際數目待完成後記錄，不沿用519。新formula／manual／protocol尚未封存，本批沒有formal成績。

最終完整acceptance：Python3.10.19於`output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-20-54-40`、Python3.14.6於`...py3_14_6/2026-10-03-20-54-51`，各520通過、0失敗；unittest本體59.038／61.086秒。pip check＋37既有CLI，共39命令全部exit0。新exp18的兩環境CLI help／smoke另外查核，不混算既有37個。常數訊號moment precision warning與故意invalid CLI選項是既有邊界測試輸出，沒有忽略failed testcase。

工程commit `34ee046f2507c031fcdd5829edc67c61c0eee233`已push／remote一致；20:57:37–20:57:58執行手冊lock命令，`output/fault_type_context_rejection_lock/2026-10-03-20-57-37/protocol.json`綁定上述HEAD、I protocol／108模型lock／actual source、J core／runner／manual SHA。固定36方法×3fold×3seeds=324評估，無winner／selection，test曝露未清除。協定提交推送後才能calibrate；此刻尚未讀J outer。

協定commit `98da5c9c09cee9b9c7fb81315dbc6ddfa95fe246`已push／remote一致，之後20:59:06–21:02:36執行calibrate：324個拒絕器完成，引用108個父分類器，新增分類器fit為0。lock checksum `13c1519c1128ea1fd54e2707cd84149506fd57df6c080b7fe30c8b3abd008a71`；9個fold／seed bundle保存在D槽context_rejection_v1，C槽保存compact lock及artifact_location。

21:02:51–21:04:33執行source-verify，從actual known train／cal重新計算距離及固定95%分位數，9個bundle共324節點通過；test numeric reads=0。source checksum `33bedd625b41b323a5905071e0d0a41292a47974248cf84f9e8f14fc088aef9b`，status=VERIFIED_AVAILABLE_NUMERIC_SOURCES。校準與來源重建前後90份formal檔案指紋均為`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。此項只證明可用特徵／用途／計算來源；raw session、視窗及採集獨立性仍UNKNOWN。將本階段提交推送後才執行outer，沒有讀J test成績。
