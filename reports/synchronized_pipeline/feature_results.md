# 特徵表示研究：固定N5／已曝光資料，2026-10-01

## 結論

預登錄known validation選出vibration75，不是看test挑選。探索性test的分類與Mahalanobis
ranking／recall有改善，但依然不足以稱可靠模型。正式105CSV、linear/LW預設不更換。
本輪只變表示，固定原balanced LogisticRegression與factory設定，沒有重新跑2490。
真正historical-vs-aligned raw對照沒有執行：仍無可驗證原DAQ時間。

## 預先固定選擇

原first N5 role，healthy+1/2/3/3_14/4screws；4_146/5/6/7為unknown。
全3 documented motor folds，seed42/123/2026只是fold標識。RobustScaler/PCA/prototypes/reference只fit train；
known calibration設.95 threshold，kNN k5、Mahalanobis LW。Validation/calibration共用的相依仍在。
每候選一個固定classifier，PCA20/full SVD；選equal-fold macro-F1、再BA、最後預定tie rank。
Registry 568c99e先push；fit18classifier/36detectors完成後lock8866c35先push，再test。

| 表示 | Validation macro-F1 | Validation BA |
|---|---:|---:|
|105 baseline|0.188776|22.5878%|
|三軸振動75（選定）|0.216750|26.3888%|
|電流15|0.087356|14.2381%|
|溫差15|0.112292|16.2422%|
|振動＋電流90|0.213395|26.3801%|
|train PCA20|0.155761|21.1128%|

選定者validation F1＋0.027974、BA＋3.8011百分點；未換成ExtraTrees。

## 鎖定後全候選結果

36/36完成、0失敗；36逐樣本gz全部重算metrics/SHA/IDs核對。同seed全12runs使用相同test。
共346920prediction records是28910舊samples被六表示／兩detectors重用，不是346920次獨立採集。

| 表示 | Test accuracy | Test BA | Test macro-F1 | Maha AUROC | Maha unknown recall |
|---|---:|---:|---:|---:|---:|
|105 baseline|29.6306%|29.7372%|0.262007|0.531118|15.0702%|
|振動75|34.1532%|34.5029%|0.302791|0.574588|18.4367%|
|電流15|18.2860%|18.4497%|0.130768|0.485142|0.5200%|
|溫差15|19.8646%|20.0478%|0.133809|0.528219|1.0547%|
|振動＋電流90|31.6848%|31.8386%|0.288183|0.526727|17.0351%|
|PCA20|26.5896%|26.7488%|0.219175|0.580716|4.0059%|

振動75 vs同範圍baseline：accuracy＋4.5226百分點、BA＋4.7656百分點、F1＋0.040784。
不與全部126組25.744%做直接差值，不選test AUROC最高的PCA取代預先選定者。

| 振動75／equal-fold | Mahalanobis LW | kNN |
|---|---:|---:|
|AUROC|0.574588|0.571053|
|AUPR|0.439675|0.434208|
|Unknown recall|18.4367%|5.4526%|
|Unknown precision|27.8537%|18.0775%|
|Unknown F1|0.211959|0.082427|
|FPR@95TPR|86.4022%|84.7773%|
|Healthy FPR|0%|0.7407%|
|Healthy acceptance|100%|99.2593%|

Maha AUROC＋0.043469、recall＋3.3666百分點；kNN AUROC＋0.066396、recall＋0.9588百分點，
但kNN healthyFPR由0.2822%升至0.7407%。不能只報ranking改善或0healthyFPR便稱安全。

| Motor test／seed | baseline accuracy→振動75 | baseline F1→振動75 | 振動75 Maha recall |
|---|---:|---:|---:|
|T3／42|28.2298%→31.7630%|0.253514→0.259415|8.4011%|
|T1／123|37.4558%→45.4760%|0.316536→0.397559|**0%**|
|T2／2026|23.2063%→25.2206%|0.215970→0.251398|46.9091%|

只有三顆motor，個體與老化混雜。列fold/range描述，不用windows／重複表示算窄母體CI。
per-class recall/confusion、motor/RPM/configuration分層與18detector pairs差值均保存在verified JSON。
其中一motor unknown recall=0，unknown-score separation仍不足。

## 原理解讀（推論，不是因果證明）

- 振動較貼近鬆動引起的動態反應；電流／溫差可能混入工況、個體與溫升等nuisance，加入105空間不必然提升跨motor分類。
- 冗餘與無關維度會改變距離幾何、協方差估计及鄰近關係；刪除部分維度能改善表示，但不證明current/temp永遠無用。
- PCA保留train高變異方向，不保證保留故障判別方向。PCA此輪AUROC較高卻分類／固定threshold recall较差，ranking與操作點是不同指標。
- 現有來源的刪點／通道時間錯位、按檔清理與physical未知仍在；不能歸因單一原因，也不能由本輪子集研究稱已修復同步。

## 精確產物（工作root內相對位置）

Root=`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`

- registry `output/fault_type_representations/2026-10-01-08-37-53/candidate_registry.json`
- selection/lock/18joblibs/audit `output/fault_type_representations/2026-10-01-08-38-17/`
- lock checksum `bdf471c8e6f86223d61e8fb2c5f134156c01cc24de8148e84c59bcacc9b271c3`
- 36runs/predictions `output/fault_type_representations/2026-10-01-08-38-59/`
- 重算驗證 `output/fault_type_representation_report/2026-10-01-08-41-08/verified_comparison.json`

```powershell
$p='.\.venv310\Scripts\python.exe'
& $p -m experiments.fault_type_representations prepare --matrix output/fault_type_matrix/2026-09-30-19-05-42 --data-root data/formal_local
# commit實際新registry後，fit使用該registry；不要重新選組合
& $p -m experiments.fault_type_representations fit --matrix output/fault_type_matrix/2026-09-30-19-05-42 --data-root data/formal_local --registry output/fault_type_representations/2026-10-01-08-37-53/candidate_registry.json
# 先commit實際新locked fit；下列是既有保存產物的可核對評估入口
& $p -m experiments.fault_type_representations evaluate --matrix output/fault_type_matrix/2026-09-30-19-05-42 --data-root data/formal_local --registry output/fault_type_representations/2026-10-01-08-37-53/candidate_registry.json --locked output/fault_type_representations/2026-10-01-08-38-17/locked_config.json
& $p -m experiments.fault_type_representation_report --evaluation output/fault_type_representations/2026-10-01-08-38-59/evaluation_report.json --locked output/fault_type_representations/2026-10-01-08-38-17/locked_config.json
```
