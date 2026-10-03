# 平滑L1研究接續紀錄

2026-10-03，Asia/Taipei。exp16尚未使用，先完成手冊及兩份索引，再新增core與12項測試。沒有改exp15或其他sealed依賴。來源與公式圖片核對見exp16手冊及exp15 sources_addendum。

`.venv310/Scripts/python.exe -m unittest tests.test_fault_type_smooth_l1 -q`：12通過、0失敗，0.023秒。
`venv/Scripts/python.exe -m unittest tests.test_fault_type_smooth_l1 -q`：12通過、0失敗，0.020秒。
包含Q／S零值與極端值、distance對原型導數、相對損失含anchor有限差分、mean初始化匹配、收斂／未收斂、tampering、序列化與同seed重現。沒有正式fit或outer score；runner與來源驗證仍待實作。

這部分只提交core／測試／先行手冊及索引。實驗15的外層評估／verify繼續使用其封存SHA；新增測試數不回填之前452項驗收產物。之後完整回歸須報新的實際數字。

## runner與來源驗證，2026-10-03

核心先行提交`85a35f96dd893ba83e1aa69bb4bd47ba9db5ffc6`已推送。新增runner共用exp15 parent來源重建、原manifest／factory／metrics；fit與cal實際來源分開，未知不擬合。新增8項來源測試，兩環境各20項通過：cal不能初始化原型、重封SHA仍錯的原型／loss子集、錯誤Q/S與parent inventory／selector／test讀取均拒絕。

最初Python3.10 CLI遇到Python3.11才支援的下標星號展開，改為tuple concatenation；沒有正式資料結果被生成。修正後兩環境`--help`及`smoke`通過，合成smoke為`15-44-27`／`15-44-29`，只作工程測試。保留最初3.14的`15-43-49`smoke與失敗紀錄，不冒稱首次兩環境都通過。

完整命令：兩環境各執行`-m experiments.fault_type_continuous_acceptance`。`output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-15-48-08/environment.json`及`...py3_14_6/2026-10-03-15-48-19/environment.json`實際各472項通過、0失敗，status=PASS；pip check與既有37個CLI皆exit0。exp16 help/smoke另行執行，不灌入37的計數。

此時僅完成工程驗收，108格尚未fit/evaluate。先提交runner與手冊，再生成新protocol並提交推送，之後才正式擬合。正式105／LW／k-NN factory／PolarMap及282筆既有tracked deletions均未改。

runner與472項驗收提交`45411e2c46aa78bbeb26e35036fd4e17b307a2d4`，push成功且remote SHA一致。15:54再次唯讀核對main AGENT blob為`8f35a6bf14fa4747d63add1d6bc852b65bcb4784`，與前次已完整讀取版本相同。沒有建立issue／PR或向其他對話傳訊息。

事前lock命令見手冊，實際輸出`output/fault_type_smooth_l1_lock/2026-10-03-15-53-46/protocol.json`；鎖定程式HEAD為45411e2。方法固定12、fold3、seed0/1/2，共108格；selection空、歷史曝光不清除。協定推送後才開始fit，沒有先看本批test成績。

## 正式擬合與actual-source重建

協定commit `7ace8972194ff75f8f1cda5d990f177d705eb342`已push且remote一致，semantic protocol seal=`71b1618d165ef1dd2e309bac9a5ec8e8b8adcd2e8a01084d3939235268437a8b`。seal是canonical payload checksum，與完整file SHA不同，後續索引分開列。

`fit --protocol output/fault_type_smooth_l1_lock/2026-10-03-15-53-46/protocol.json --data-root data/formal_local`：15:54:51–16:00:10，9bundles／108models，108成功、0未收斂、最高550iterations；資料SHA前後相同。D主產物為`D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/smooth_l1_v1/workspace/output/fault_type_smooth_l1_fit/2026-10-03-15-54-51/`，C compact lock同名路徑；locked seal=`aa6373bcff8a24e356142977555e76e7ae5f62aa520e520017c692bdfe61985b`。

`source-verify --protocol ...15-53-46/protocol.json --lock output/fault_type_smooth_l1_fit/2026-10-03-15-54-51/locked_study.json --data-root data/formal_local`：20:13:55–20:17:19，actual known train/cal重建全部108models與train predictions完全一致，test_numeric_reads=0，來源前後不變。不是只比fit IDs或檔名。這段尚未outer評估；來源驗證檔為`output/fault_type_smooth_l1_source_verify/2026-10-03-20-13-55/source_verified.json`。中間時段不宣稱持續背景研究。

## outer結果、重推與備份

來源commit `36605fd37106872f620daabe7cb2fa834bf98b9e`已push／remote一致後，執行同module `evaluate --protocol ...15-53-46/protocol.json --lock ...15-54-51/locked_study.json --source-verification ...20-13-55/source_verified.json --data-root data/formal_local`，20:19:06–20:21:01，108／108格、0INCOMPLETE、1,040,760records／28,910unique，action計算102.892秒。D output `fault_type_smooth_l1_evaluate/2026-10-03-20-19-06`；before/after SHA相同。

`verify`相同arguments加`--evaluation D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/smooth_l1_v1/workspace/output/fault_type_smooth_l1_evaluate/2026-10-03-20-19-06/evaluation.json`，20:21:11–20:23:12，108逐筆reinfer及truth mutation／saved metrics全匹配，輸出D `fault_type_smooth_l1_verify/2026-10-03-20-21-11`。未改參數，未重訓新增「獨立」資料。

`report`使用本批p/e/v與`--baseline output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json --previous output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json --euclidean D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/discriminative_prototypes_v1/workspace/output/fault_type_discriminative_prototypes_evaluate/2026-10-03-15-33-56/evaluation.json`：20:23:56–20:25:03，重算controls／12候選、756配對，12全部FAILED，無global winner。Human report未改sealed summary。

`backup`一次指定本批D fit/evaluate/verify三roots，產物`output/fault_type_smooth_l1_backup/2026-10-03-20-24-08/archive_index.json`。另`-m experiments.fault_type_archive --output-root`三次指本批C protocol/source/report，`--destination D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/smooth_l1_v1/archives`，index `output/fault_type_archive/2026-10-03-20-27-31/archive_index.json`。每批單次多root，時間戳未撞名。

`-m experiments.fault_type_fixed_delivery --index`上述兩index，20:28:18，6ZIP／252members整檔SHA、CRC、member SHA PASS；未extract/delete，不是離機備份。三compact GZIP總約599KB，個別explicit force-add以繞過既有*.gz忽略，未改.gitignore、未stage模型／data／282無關刪除。

exp17 core-only後完整兩環境各483通過：20-20-32／20-20-43；exp17 runner及來源用途20測試後完整各492通過：20-26-06／20-26-17。全部各39命令exit0含pip check與37既有CLI。最初H事前驗收472項不回填成492；20:24:15／16的exp17 smoke是synthetic ENGINEERING_ONLY。
