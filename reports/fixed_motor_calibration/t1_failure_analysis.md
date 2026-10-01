# P4：T1 未知召回率 0% 的封存後診斷

範圍：fixed_methods_motor_calibration_v1、第一組歷史N5、T2 train / T3 calibration / T1 test。3,824個unknown、5,935個known（其中991 healthy）；seed0診斷，封存report已驗證三seeds數值一致。這不是新方法/門檻選擇，不修改本輪模型。

## 已排除的工程疑點（限實際覆蓋範圍）

來源/模型/預測SHA、sample IDs、known/unknown映射、有限值、raw/threshold公式、>1拒絕符號、calibration逐類實際.95 quantile、封存模型重新計算score、保存摘要重算都一致。沒有NaN或反向比較造成0%。程式檢查不等於確認原始採集真值，也不是保證所有程式永遠無bug。

| 固定方法 | T1 AUROC | unknown最高score | known最高score | unknown recall |
|---|---:|---:|---:|---:|
| 105 / Maha-LW | 0.498192 | 0.600991 | 0.925099 | 0% |
| 105 / kNN | 0.522014 | 0.794295 | 0.858256 | 0% |
| 75 / Maha-LW | 0.507380 | 0.595545 | 0.956730 | 0% |
| 75 / kNN | 0.584985 | 0.660435 | 0.694166 | 0% |

所有T1 test score都低於固定1，0%召回符合實際數值；healthy FPR同為0並不代表安全識別成功。單純降低threshold可能多拒絕樣本，但Mahalanobis AUROC接近隨機，不能只靠門檻補回排序。沒有以T1掃任何threshold。

## 原理與證據

1. **校準轉移／接受區域過寬：支持。** Maha75的3screws threshold=202.970892，而同類train自身距離q95=8.873232，比值22.8745。T3各類cal距離相對T2 train大，既定95%分位數把接受區域拉寬；score取所有類`raw / class threshold`的最小值，只要其中一類比例小就接受。T1 unknown 3,764/3,824個最近「正規化reference」是3screws；105 Maha全部3,824如此。注意這不是linear classifier的預測類別。
2. **kNN也有相同接受區域問題，不是Maha專屬實作重複。** 75維4screws threshold=19.955655、train own q95=1.278658，比值15.6067。T1 unknown 3,784/3,824最近reference是4screws；105 kNN全部如此。兩種距離都使用逐類cal門檻和最小比例，可被寬鬆reference主導。
3. **跨馬達分布差異：數值支持，但物理原因不確定。** 在T2 train scaler空間、相同RPM健康特徵median位移（75維平均絕對量）T3/T1分別：6000rpm .263393/.503455、8000rpm .385943/.852199、11000rpm 1.599101/1.457764。同RPM也不同，不能完全歸因於RPM混合。這些是train-scaled數值，不是物理損壞程度；無單位/安裝/負載/同步證據不能確定成因。
4. **特徵／configuration重疊與detector限制：在分數空間得到支持，不能證明物理不可分。** Maha的known/unknown分布高度重疊，75 Maha原始最小distance AUROC=.512917、正規化=.507380；105約.500843/.498192。去除Current/Delta_T可改善整體平均，但沒有恢復T1的未知排序。kNN75正規化AUROC=.584985比原始最小distance .511647高，反證「正規化一定破壞排序」；改善仍有限且固定門檻召回0。

Train距離是**in-sample診斷**：Maha共變異數由這些rows估計，kNN train query含自身鄰居，因此train q95偏樂觀；上述比值不是獨立估計的domain shift倍數，也不支持母體校準保證。原始最小distance也是事後診斷（不同class尺度不同），不能當新方法改善結果。

### 分RPM的重要反證（源自同一批封存結果，未重新fit）

| T1固定方法 | 6000 RPM AUROC | 8000 RPM AUROC | 11000 RPM AUROC |
|---|---:|---:|---:|
| 105 / Maha | .763692 | .511394 | .059424 |
| 75 / Maha | .761686 | .581768 | .047005 |
| 105 / kNN | .747830 | .490624 | .289918 |
| 75 / kNN | .853420 | .579390 | .351554 |

三RPM四方法的unknown recall全部0。整體AUROC接近隨機不代表每工況都隨機；6000rpm有排序訊號，11000rpm部分排序卻反向。這支持工況混合/特徵距離語意不穩定的研究假說，但**不能據此翻轉11000rpm分數方向、挑有利RPM或宣稱RPM分層必然改善**。部分工況的門檻問題較明顯，部分工況還有排序本身的問題，兩者需分開檢驗。

## 無法確定的事項與反證

現有資料只能證明處理後特徵分布與接受行為不同；缺raw/session/時間/清理遮罩，無法區分個體、年齡、安裝、負載、採集及處理流程影響。T1新、T2/T3老與motor身分混雜，不能串成生命週期。Stage2逐通道清理可能也是混雜因素，不能憑現有特徵重建或排除。沒有計算每小時誤報、延遲、RUL或損壞百分比。

## 最多兩個下一輪方案（尚未實作／未驗證）

1. **固定RPM分層模型與校準**：預先鎖定每RPM獨立的train-only scaler/class/reference，仍使用原三motor用途，不依T1選RPM或門檻；對照本輪混合RPM模型，完整報告缺類/樣本不足及全部方向，檢驗接受區域是否受工況混合主導。相同RPM仍有shift，所以不保證改善。
2. **train-only留一已知configuration作proxy-unknown的局部診斷**：只在該fold train馬達內，預先固定所有留一config任務，用剩餘known fit，比較少量事前固定表示法/score規則；真正未知test與calibration不選參。不得合併三折挑global winner，proxy結果不能當新motor驗證，後續test依然exploratory。

兩方案均不是本輪完成項，沒有回寫或重跑T1取得較佳主成績。

## 可重算證據

`output/fault_type_fixed_diagnosis/2026-10-01-19-36-47/diagnosis.json`保存train/cal/test各類及RPM的raw/ratio分布、threshold、nearest class、健康median與IDs digest；四張ECDF顯示已知與未知重疊和拒絕線位置。`source_verification.json`及models SHA確認診斷前後資料與封存模型不變。
