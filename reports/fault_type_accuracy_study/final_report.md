# 現有資料有界準確率研究（2026-10-02，Asia/Taipei）

## 結論與驗證範圍

新增198／198邏輯評估完成、0失敗，1,908,060筆保存預測逐筆核對PASS，28,910 unique test IDs。另重用18個A0基線結果，不重新fit。72個共用reference檢查與225個配對差值通過；沒有global winner、validation或selector。

**有局部提升，沒有全面可靠升級。** A7 shrinkage LDA的三motor等權純fault配置accuracy由A0的26.61%升至30.91%（+4.30百分點），balanced accuracy由26.78%升至31.21%，macro-F1由.2404升至.2866。但healthy+known accuracy由34.15%降至32.17%，T1純fault accuracy由34.67%降至25.10%；改善主要來自T2/T3。A7的detector沿用A1，不能把分類器提升說成新的unknown分數改善。

B1/B2/B3在A1固定底座下可改變T1排序與操作點，並得到非零unknown recall，仍有漏檢、RPM失敗及非常弱的已知分類。A4/kNN對T1有較高unknown recall，代價是63.87%健康FPR，不是可部署勝利。正式105維／linear／Maha-LW、PolarMap與binary路徑保持不變；kNN仍可切換。

全部數字是**EXPLORATORY_HISTORICAL_TEST_EXPOSED**；fresh final test=false，獨立驗證INCOMPLETE、原始採集UNKNOWN。方法來自歷史問題後的固定消融，執行前封存不是全新盲測。

## 協定、資料與實際成本

`fault_type_accuracy_study_v2_json_contract`只修復v1參數JSON tuple/list還原；方法、參數、198預算沒有更動。registry 8418b7539670a3b4fd952e4a087b83bc18cb1870fbc4ef5eb4f44530b9523e5a在真實fit前push。train=T1/cal=T2/test=T3；train=T2/cal=T3/test=T1；train=T3/cal=T1/test=T2。每RPM只使用同RPM train擬合與另一馬達known cal校準，未知開發rows明列unused。seeds0/1/2只改演算法隨機性。

healthy為8screws；known faulty為1screws/2screws/3screws/3_14screws/4screws；unknown為4_146screws/5screws/6screws/7screws。fault指鬆動配置，不是九種獨立物理原因。

90CSV／28,910rows／105維的bytes與fingerprint前後不變：c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。

實際198 classifier fits、180 factory reference fits、27 pooled covariance fits、90 representations、162新score calibrations，81實體bundle／225 node audits。fit 00:35:14–00:40:13（約299秒，bundle work合計287.66秒）；evaluate含lock/audit核對 00:43:18–00:51:11（約473秒）；獨立reporter 00:51:38–00:56:52（約314秒）。這些是批次wall時間，包含I/O／驗證／共用work，不是串流延遲；未做峰值記憶體profile，不報每小時誤報、警報延遲或RUL。不得將每run重複計入的shared seconds直接相加。

### 九個可證實工況：motor × RPM

| Motor | 6000rpm samples / unknown prevalence | 8000rpm | 11000rpm | 全motor test數 |
|---|---:|---:|---:|---:|
| T1 | 3358 / 39.16% | 3049 / 40.01% | 3352 / 38.45% | 9759 |
| T2 | 3189 / 38.23% | 3250 / 35.97% | 3418 / 42.77% | 9857 |
| T3 | 2941 / 38.39% | 3225 / 41.24% | 3128 / 39.35% | 9294 |

全motor known/unknown為T1 5935/3824、T2 6007/3850、T3 5604/3690。全部known train/cal每RPM六類齊全，無缺格借資料。三motor與九工況不是九顆独立motor。

## 全部分類器／表示法結果

下表先在同motor對三seeds取平均，再三motor等權；不是把所有windows池化，也不是選最好seed。Maha/kNN原始分類預測共用相同classifier，因此closed-set結果相同是正確行為。

| Arm | 改動 | 純fault acc | 純fault BA | 純fault macro-F1 | healthy+known acc |
|---|---|---:|---:|---:|---:|
| A0 | 75 mixed RPM，原linear，基線重用 | 26.61% | 26.78% | .2404 | 34.15% |
| A1 | 75，RPM獨立linear | 17.92% | 17.82% | .1497 | 18.53% |
| A2 | 66，mixed RPM linear | 26.66% | 26.81% | .2351 | 33.95% |
| A3 | 66，RPM獨立linear | 19.58% | 19.47% | .1716 | 20.21% |
| A4 | signed-log66，RPM linear | 23.01% | 22.70% | .1971 | 23.86% |
| A5 | 75，RPM ExtraTrees | 27.45% | 27.34% | .2589 | 33.21% |
| A6 | 75，RPM HGB | 23.63% | 23.58% | .2027 | 28.06% |
| A7 | 75，RPM shrinkage LDA | 30.91% | 31.21% | .2866 | 32.17% |
| A8 | 75，RPM RBF SVM | 14.06% | 13.66% | .1004 | 17.47% |

分類改動相對A1：A5 pure accuracy +9.53pp、A6 +5.71pp、A7 +12.99pp、A8 -3.86pp；相對原A0：A5 +0.83pp、A7 +4.30pp，其餘除A2微小+0.05pp皆下降。A2去除公式冗餘不代表提升所有指標：macro-F1仍下降；非線性平方項可能原本提供linear可用的表達，不能僅用「冗餘」推論必然改善。

### 各motor純fault accuracy（全部候選）

| Arm | T1 | T2 | T3 |
|---|---:|---:|---:|
| A0 | 34.67% | 22.07% | 23.10% |
| A1 | 10.92% | 18.93% | 23.91% |
| A2 | 34.71% | 21.49% | 23.78% |
| A3 | 11.39% | 20.33% | 27.02% |
| A4 | 9.67% | 25.23% | 34.12% |
| A5 | 17.85% | 25.18% | 39.31% |
| A6 | 19.24% | 24.83% | 26.81% |
| A7 | 25.10% | 36.74% | 30.88% |
| A8 | 9.71% | 18.49% | 13.97% |

A5的T1每個seed不同，這裡17.85%是三seed均值，不使用較佳seed取代。LR/LDA/SVM與detector為確定性，三seed相同並不代表三次新採集。每seed實值／SD、全部RPM、每類support/recall與confusion matrix見machine-readable summary及完整verified report。仍有零召回配置，例如A7 seed0 T1的2screws、T3的2screws與3_14screws；沒有任何方法證明所有配置可辨識。

## 全部開集結果與代價

M=Maha-LW、K=kNN。AUROC/AP為unknown-positive；AP必須和前述prevalence一起看。recall/FPR/known rejection用已固定校準操作點，未從test選門檻。final acc包含known接受且正確與unknown拒絕。

| 方法 | AUROC | AP | unknown recall | healthy FPR | known reject | final acc |
|---|---:|---:|---:|---:|---:|---:|
| A0/M | .5746 | .4397 | 18.44% | 0.00% | 12.82% | 24.85% |
| A0/K | .5711 | .4342 | 5.45% | 0.74% | 5.25% | 22.64% |
| A1/M | .5388 | .4197 | 21.07% | 8.99% | 18.73% | 16.14% |
| A1/K | .5348 | .4485 | 16.90% | 30.68% | 19.78% | 15.66% |
| A2/M | .5864 | .4442 | 15.66% | 0.00% | 11.52% | 24.26% |
| A2/K | .5728 | .4351 | 5.00% | 0.42% | 4.79% | 22.26% |
| A3/M | .5316 | .4081 | 15.72% | 10.26% | 18.35% | 14.36% |
| A3/K | .5328 | .4462 | 25.46% | 35.08% | 22.14% | 19.62% |
| A4/M | .5528 | .4665 | 14.68% | 10.90% | 5.02% | 18.80% |
| A4/K | .5542 | .4555 | 26.82% | 21.29% | 21.27% | 22.83% |
| A5/M | .5388 | .4197 | 21.07% | 8.99% | 18.73% | 25.28% |
| A5/K | .5348 | .4485 | 16.90% | 30.68% | 19.78% | 21.61% |
| A6/M | .5388 | .4197 | 21.07% | 8.99% | 18.73% | 21.61% |
| A6/K | .5348 | .4485 | 16.90% | 30.68% | 19.78% | 18.96% |
| A7/M | .5388 | .4197 | 21.07% | 8.99% | 18.73% | 24.04% |
| A7/K | .5348 | .4485 | 16.90% | 30.68% | 19.78% | 22.21% |
| A8/M | .5388 | .4197 | 21.07% | 8.99% | 18.73% | 17.41% |
| A8/K | .5348 | .4485 | 16.90% | 30.68% | 19.78% | 16.16% |
| B1 class-LW/global | .5706 | .4399 | 24.69% | 0.14% | 18.80% | 18.69% |
| B2 pooled-LW/class | .5596 | .4315 | 23.86% | 0.00% | 17.46% | 19.17% |
| B3 pooled-LW/global | .5550 | .4227 | 24.87% | 0.00% | 20.62% | 19.40% |
| B4 kNN/global | .5357 | .4424 | 24.94% | 25.52% | 24.18% | 17.95% |
| B5 class-M/conformal | .4761 | .3941 | 20.90% | 8.64% | 18.53% | 16.10% |
| B6 class-K/conformal | .5100 | .4064 | 16.43% | 29.29% | 19.47% | 15.49% |

A5–A8的unknown分數與A1逐筆相同（72檢查PASS）；分類器提升沒有創造新的detector提升。B1/B2/B3相對A1/M有較低healthy FPR及較高recall，但它們的分類器依然是A1，不把它們和A7臨時組合報成已驗證方法。B5/B6沒有「Conformal必然更好」；排序與FPR沒有取得廣泛改善，跨motor不保證可交換性。

### 接受後accuracy不能取代coverage

| 方法 | selective accuracy（所有接受樣本，接受unknown算錯） | coverage |
|---|---:|---:|
| A0/M | 20.13% | 85.00% |
| A1/M | 10.91% | 80.35% |
| A5/M | 21.99% | 80.35% |
| A7/M | 21.47% | 80.35% |
| A4/K | 13.50% | 76.56% |
| B3 | 14.33% | 77.72% |

完整24方法的selective／known acceptance／unknown precision/F1／FPR@95TPR等保存在summary，不只輸出以上示例。FPR@95TPR是事後ROC描述值，不部署該test門檻。

Pareto只用「pure-fault balanced accuracy ↑／unknown recall ↑／healthy FPR ↓」三軸：A0/M、A2/M、A4/K、A7/M、B3為描述性non-dominated points。這不代表其他指標、其他motor或部署成本也勝出，更不是global selected winner。A2比A0的BA僅微小改善，未提供統計顯著性保證。

## T1：排序、操作點與失敗

T1有3824 unknown與991 healthy。以下都是seed0；detector三seed相同已核對。A5–A8相同detector只依A1對照，不重複列。

| T1方法 | AUROC | unknown recall | healthy FPR | 6000/8000/11000 RPM AUROC |
|---|---:|---:|---:|---|
| A0/M（歷史） | .5074 | 0% | 0% | .7617/.5818/.0470 |
| A1/M | .5634 | 0% | 0% | .7554/.6285/.2908 |
| A1/K | .6248 | 21.89% | 50.76% | .7614/.7635/.5128 |
| A2/M | .5304 | 0% | 0% | .8520/.6667/.1678 |
| A2/K | .6038 | 0% | 0% | .8567/.5845/.3889 |
| A3/M | .5486 | 0.13% | 0.10% | .6896/.6447/.2836 |
| A3/K | .6160 | 52.59% | 63.87% | .7605/.7714/.4941 |
| A4/M | .6306 | 14.33% | 32.69% | .6901/.5805/.6512 |
| A4/K | .6799 | 75.60% | 63.87% | .7793/.7073/.7617 |
| B1 | .5786 | 9.28% | 0% | .6667/.7170/.4655 |
| B2 | .5978 | 5.36% | 0% | .7602/.7138/.5815 |
| B3 | .5643 | 3.40% | 0% | .7295/.6332/.4978 |
| B4 | .5682 | 25.84% | 31.58% | .7474/.7120/.4652 |
| B5 | .4225 | 0% | 0% | .5000/.5094/.2678 |
| B6 | .6400 | 20.63% | 46.92% | .7335/.7635/.4268 |

T1 6000/8000已有部分可用排序但可能被cal門檻全部接受；11000很多方法排序仍反向／近機率。A4改善部分排序，不只是降門檻，但高healthy FPR與classification退步仍否定全面可靠。B2的11000 AUROC .5815且recall15.90%，比A1/M的.2908/0%改善，不表示所有RPM已解決（6000/8000 recall仍0%）。B1主要T1拒絕在11000（27.54%），6000/8000仍0%。没有test threshold掃描、刪類、cap或分數翻號。

未知nearest-reference在RPM分層後不再只被同一寬類主導：A1/M為1screws1220、3_14screws643、3screws1039、4screws922。A2/K仍3824/3824都選4screws；A2/M的3screws2338/3824。B1/B2/B3的nearest定義是各自raw／ratio，不將不同定義的counts混當一個距離。完整train/cal/test每類raw與score/p分布、healthy同RPM位移及calibration thresholds見diagnosis／模型audit／保存預測。

T1 A1/M unknown最高normalized score在6000/8000/11000為.7911/.9799/.7208，全低於固定reject>1，所以0%召回符合實際分數，非truth／NaN／比較符號錯誤。以T2 train的RobustScaler單位描述healthy各feature中位數平均絕對位移：T3 calibration為.6811/.5108/2.3522，T1 test為1.2952/1.2179/2.1521；支持跨motor表徵分布不同，但不是物理shift倍數或感測器／老化原因的證明。

**得到支持：**分類器與detector因素分離；RPM特徵分布／reference與跨motor校準的互動；部分表徵能改变排序；寬接受區與分數聚合可造成漏檢。**不是已確定因果：**感測器方向／單位／安装／負載／實際老化與歷史IQR對test分布的影響，均無完整來源證據。train距離是in-sample描述，不拿它的倍數推論motor母體shift。

## 狀態、交付與下一輪

VERIFIED：固定方法／參數／三motor角色，known-only train/cal、空selection、SHA／IDs／公式／配對重算、正式來源未修改、原default regression、實際198組完整保存與備份。

FAILED／INCOMPLETE：沒有得到跨三motor/RPM全面提高且安全的方案；仍有零類別召回、T1弱與部分高healthy FPR。fresh final validation、每類獨立test groups要求未滿足；不能因高分換成PASS。

UNKNOWN：原始recording/session/run/window、刪點mask、真時間、sample rate/units/mount/load／跨階段物理一致性；不補造。

完整老師對照見limitations.md；方法來源與「本輪／歷史／僅文獻候選」見methods_sources.md；重現命令見reproduction.md；所有絕對路徑與SHA／備份見result_index.json。原始與formal data未提交，大型model/predictions/verified JSON以新D槽ZIP保存，Git保存lossless compressed summary与索引，不覆蓋舊ZIP。單一D槽不是異地備援。

後續最多兩項具體候選，**尚未實作／驗證**：①同RPM train-only harmonic band-max shape ratios加保留總幅度，和未正規化幅度對照，檢驗scale與shape而非「能量」；②classifier-conditioned rejection，以cal的predicted class（不是test真值）分組，檢查min-over-classes寬接受區與誤分類代價。它們需另封存protocol，保留mixed-RPM A0對照，不採本輪test最好seed／label挑組合。沒有自動擴展10組N5或126×全部arms，也沒有實作P6大模型／target adaptation。
