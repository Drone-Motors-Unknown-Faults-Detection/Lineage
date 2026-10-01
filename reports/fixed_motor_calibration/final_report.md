# 固定方法與專用馬達校準：2026-10-01 現有資料研究交付

工程與本輪探索性比较已完成：取消共同模型選擇、專用calibration motor、36配對評估、完整預測驗證及T1失敗分析。**模型可靠性尚未通過；沒有fresh final test，所有研究切分仍INCOMPLETE。** 不要求不存在的硬體/新採集才能執行本輪工作。

## 1. 新協定與資料用途

`fixed_methods_motor_calibration_v1`，checksum `3b6cde9f5c19e627c0694f7488660b783228ae2354e96b8fa25b9dd1085edf1e`，先commit/push才執行真實fit。

| fold | train | 專用 calibration | test | train rows | cal rows | test known / unknown |
|---|---|---|---|---:|---:|---:|
| 0 | T1 | T2 | T3 | 5935 | 6007 | 5604 / 3690 |
| 1 | T2 | T3 | T1 | 6007 | 5604 | 5935 / 3824 |
| 2 | T3 | T1 | T2 | 5604 | 5935 | 6007 / 3850 |

validation=[]、selection_sample_ids=[]、selection_policy=none、shared_validation_calibration=false。Unknown只在test揭露，其餘兩motor unknown明列unused。訓練馬達healthy+known fit scaler/classifier/reference/covariance/neighbors；另一馬達healthy+同known只供既定.95距離quantile。方法不由cal、test或跨折validation平均選出。

healthy=8screws；5known faulty=1screws、2screws、3screws、3_14screws、4screws；4unknown=4_146screws、5screws、6screws、7screws，直接綁第一組歷史N5 manifest。標籤仍是同一鬆動機制的數量/位置configuration，非9個已確認獨立物理故障原因。

固定105/75維 × Maha-LW/kNN × 3motor folds × seeds0/1/2＝36 detector evaluations，共享18classifier fits。沿用C=1、balanced LogisticRegression/lbfgs、max_iter1000、tol1e-4、train-only RobustScaler、k5、confidence.95、score>1未知，完整resolved params存protocol。沒有PCA或路徑/T-code/標籤特徵。全部方法用相同test IDs及正式data fingerprint。

方法清單源自歷史研究，所以「此次執行前鎖定」不等於未看過資料。三seeds不變motor角色，決定性lbfgs/LW/kNN得到相同預測；所有seed SD0，不代表未知母體變異0。

## 2. 實際執行與結果（不是沿用舊數字假裝重跑）

真實資料fit 19:31:08–38，evaluate 19:32:25–19:33:43，36/36完成、0失敗。Reporter 19:34:14–51重新核對所有36 gzip SHA、346920 rows、IDs/真值/方向/metrics/RPM與12歷史配對。Unique samples=28910，每row12次方法/seed預測，不是346920個獨立樣本。

以下是**等motor權重描述性平均**，包含healthy的known accuracy不等於純fault accuracy。兩detector共用classifier，因此known分數相同是預期行為。

| 方法 | known accuracy | balanced accuracy | macro-F1 | 5known faults accuracy | unknown AUROC | unknown recall | healthy FPR |
|---|---:|---:|---:|---:|---:|---:|---:|
| 105/Maha | 29.63% | 29.74% | .2620 | 25.27% | .531118 | 15.07% | 0% |
| 105/kNN | 29.63% | 29.74% | .2620 | 25.27% | .504657 | 4.49% | .282% |
| 75/Maha | 34.15% | 34.50% | .3028 | 26.61% | .574588 | 18.44% | 0% |
| 75/kNN | 34.15% | 34.50% | .3028 | 26.61% | .571053 | 5.45% | .741% |

75相對105：known accuracy +4.5226百分點；純5fault accuracy只+1.3423百分點；Maha AUROC+.043469、recall+3.3666百分點；kNN AUROC+.066396、recall+.9588百分點，但healthy FPR+.4586百分點。**這些是固定表示法之間的差異，不是取消selector帶來的新提升。**

與歷史同方法、同N5、同motor fit/cal相比，12配對classifier/reject差異筆數0、score最大絕對差0、accuracy/recall差0。刪除共同選擇與共享選參用途沒有修改原fit/cal數學，分數不變正確。舊global-selected結論仍有17546個外折known test參與共同選擇依賴；新流程不產生winner，不能把相同分數重新宣稱無偏或fresh。

其他完整平均：75/Maha AP=.439675、precision=.278537、unknown F1=.211959、FPR95=.864022、known rejection=12.821%、accepted-correct known rate=29.036%、合併unknown最終open-set accuracy=24.846%；75/kNN相應AP=.434208、precision=.180775、F1=.082427、FPR95=.847773、known rejection=5.253%、accepted-correct known rate=33.796%、最終open-set accuracy=22.642%。完整逐類precision/recall/F1、confusion matrices、unknown各label、prevalence與RPM metrics均在JSON，不以拒絕效果混入同名closed-set known accuracy。

### 逐motor：seed0，seeds1/2完全相同

| test motor | test rows | known accuracy105→75 | Maha AUROC105→75 | Maha recall105→75 | kNN AUROC105→75 | kNN recall105→75 |
|---|---:|---:|---:|---:|---:|---:|
| T1 | 9759 | 37.46→45.48% | .498192→.507380 | 0→0% | .522014→.584985 | 0→0% |
| T2 | 9857 | 23.21→25.22% | .615003→.614031 | 44.21→46.91% | .541871→.526181 | 12.83→15.87% |
| T3 | 9294 | 28.23→31.76% | .480161→.602353 | 1.00→8.40% | .450085→.601992 | .65→.49% |

只有3個documented motors；不得把3seeds、9motor/RPM、重複windows或126舊combination當更多獨立受試。沒有逐窗IID CI或部署級motor母體信賴保證。

### 9個已觀測motor/RPM組合（全部10configuration有資料）

各列方法用相同test rows；不是每折各9個獨立工況。未知prevalence列於最後一欄。所有Maha healthy FPR=0；kNN 105/75只有T2 11000rpm為3.162%/8.300%，其餘八列為0。

| motor/RPM | rows | known acc105→75 | Maha recall105→75 | kNN recall105→75 | unknown prevalence |
|---|---:|---:|---:|---:|---:|
| T1/6000 | 3358 | 15.66→37.30% | 0→0% | 0→0% | 39.16% |
| T1/8000 | 3049 | 49.37→49.21% | 0→0% | 0→0% | 40.01% |
| T1/11000 | 3352 | 48.47→50.27% | 0→0% | 0→0% | 38.45% |
| T2/6000 | 3189 | 19.54→18.07% | 0→0% | 0→0% | 38.23% |
| T2/8000 | 3250 | 3.60→8.70% | 52.18→54.15% | 2.65→10.78% | 35.97% |
| T2/11000 | 3418 | 47.75→50.00% | 74.69→80.23% | 31.67→33.17% | 42.77% |
| T3/6000 | 2941 | 12.64→17.94% | 0→0% | 0→0% | 38.39% |
| T3/8000 | 3225 | 39.95→34.41% | 0→0% | 0→0% | 41.24% |
| T3/11000 | 3128 | 31.42→42.33% | 3.01→25.18% | 1.95→1.46% | 39.35% |

本輪資料格子無缺類/缺RPM，36全部完成。未測其他負載/安裝/新session格子，這些非「0%」而是UNKNOWN/NA；未擴大六種方向或挑有利motor。

## 3. T1失敗分析

4方法3824 unknown最高score依序.600991/.794295/.595545/.660435，全部低於固定1；非NaN、truth/符號或保存摘要錯誤。Maha總AUROC約.50，known與unknown重疊；kNN75 .584985仍弱。T2-fit/T3-cal造成較寬某些類別接受區域，min(normalized distance)常被3screws（Maha）/4screws（kNN）主導。與classifier預測必須分開解讀。

T1分RPM75/Maha AUROC .761686/.581768/.047005；75/kNN .853420/.579390/.351554：6000有排序訊號，11000部分排序反向，不能只說所有features都無訊號，也不依此反轉分數或調threshold。相同RPM健康feature median仍有motor間差異，支持domain shift／calibration transfer的數值解釋；個體/年齡/安裝/清理/不同stage特徵物理意義無法分離。

詳細證據/反證/in-sample train距離限制及最多兩個**尚未實作驗證**的下輪方案見`t1_failure_analysis.md`。診斷只讀，未用test掃threshold/k/subset/quantile，未重fit或取最好seed，沒計RUL、逐小時誤報與警報延遲。

## 4. 驗收層級與「切分不完整」的不同意思

| 層級 | 狀態 | 判斷 |
|---|---|---|
| 同折用途與unknown排除 | VERIFIED | train/cal/test ID與motor分離；只train fit/reference、known cal門檻 |
| 本輪共同selector依賴 | VERIFIED已取消 | selection空、validation N/A；固定角色CV輪換合法，不建立global winner |
| validation/calibration共用 | VERIFIED已消除此角色共用 | 不選參，cal专用；沒有造第四motor或宣稱無偏轉移校準 |
| 本輪N5/3RPM coverage、36保存結果 | VERIFIED | SHA/IDs/公式/重算/配對；全部格子有資料 |
| 模型識別能力 | FAILED/不足 | T1未知0%、平均known fault accuracy26.61%、unknown召回仍低 |
| 獨立final資格 | INCOMPLETE | 每fold一test motor/class，舊至少2 groups不放寬，all28910已曝光 |
| 原始來源/視窗/清理採集獨立性 | UNKNOWN | 缺session、raw boundaries、時間/stride、刪點遮罩等，不由無副本推PASS |
| 真正退化生命週期/部署泛化/5%誤報保證 | 未驗證 | 不能由三不同motor、0%healthy FPR或名目.95推出 |

T1/T2/T3是文件支持的不同馬達，T1新、T2/T3老；沒有序號不代表完全沒有身分證據。但使用時數、實際老化、session/run及環境不明，不能三顆接成同一生命週期。歷史整檔IQR可能利用test分布，本輪不能沒有raw就還原或聲稱已消除此影響。

## 5. 老師兩項建議對照

| 建議 | 完成度 | 本輪完成證據與限制 |
|---|---|---|
| healthy+5known faulty / 4unknown | 實驗完成、可靠性未完成 | 固定歷史第一組三motor/兩repr/兩detector/3seeds36新評估；fault為configuration，並非9種物理fault cause |
| 隨機healthy+N faulty驗證 | 舊研究已執行，本輪未重跑 | 舊N=5全126組756runs、N sweep/closed-set/Protocol B合計2490是基線；新CLI可接N/class manifests不等於本輪重跑全部 |
| 切分有依據、說明不完整 | 部分完成 | documented leave-one-motor-out，新用途校驗與no-selector完成；raw/session證據不足及一motor/test不足無法靠洗牌修復 |
| 可信fault type與未知預測 | 未通過 | 分開保存known及unknown指標，T1仍0%；不能以能執行模型當可靠證明 |

可以支持「這三顆馬達現有處理後特徵的跨馬達探索性比較」。不支持廣泛部署、新資料盲測、完整採集獨立性、退化百分比、RUL或固定5%誤報。

## 6. 驗證、Git與artifact位置

P0起始97a4434；P0 08aa1d5，P1 c24584b（協定先push），P2 414c30f（241tests雙runtime），fit checkpoint b1eec1b，P3 4044600，P4 341e763（244tests雙runtime），P5 1b803a5（246tests雙runtime及完整ZIP校驗）均非force push、remote SHA核對相符。最後紀錄提交只補記交付SHA，不改程式或研究結果；獨立final研究驗證仍INCOMPLETE。

最後完整驗收：`.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_acceptance`（3.10.19，19:41:26），`.\venv\Scripts\python.exe -m experiments.fault_type_fixed_acceptance`（3.14.6，19:41:37），**每環境246 tests PASS、0失敗，pip check與9 CLI help PASS**。共新增29tests；2個member-SHA tests驗證valid-CRC篡改也會拒絕。完整指令、Python套件版本、stdout/stderr、test count在各timestamp environment.json與command_1.txt；不宣稱其他runtime/OS或cross-runtime joblib相容。

repo：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。
branch：`research-improvements-20260920`，remote：`https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage.git`。
備份：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-01\fixed_motor_calibration`，新ZIP/wholeSHA/CRC/memberSHA索引。单D卷備份，不是異地灾備；舊data_independence三ZIP不覆盖，額外SHA核驗。

機器索引`reports/fixed_motor_calibration/result_index.json`记錄全部绝對路径。formal90CSV與历史manifests/locks/predictions未覆盖；282他人tracked deletions未stage；没有raw/source ZIP/secrets入Git。默認105/linear/Maha-LW、PolarMap、binary pipeline不變，kNN仍通過原factory切換。没有替issue9新增未经授權留言。

重现和恢復入口见`reproduction.md`。全部已曝光，不把換seed或新路径當fresh；现有资料范围以外事實保留UNKNOWN，不要求用户补不存在硬体来完成本轮。
