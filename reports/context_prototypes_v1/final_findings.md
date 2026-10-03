# RPM工況原型：封存實測結果

2026-10-03，Asia/Taipei。完成108格／0執行失敗、108模型全部收斂並由known來源重建；12方法全數FAILED，R2／R3未達成。所有正式資料已曝光，本批是探索性配對；沒有global winner或正式替換。

## 方法與來源

兩幾何×degree1/2×static／GLVQ／aux共12分類器，分別I01–I06 identity、I07–I12 hard600；每個degree依序static/glvq/aux。三fold train/cal/test=T1/T2/T3、T2/T3/T1、T3/T1/T2，seeds0/1/2。RPM是文件化工況代碼，非fault label，無T-code或路徑輸入；不能推論實測轉速一致。

原機制取自Graeber／Vetter／Saralajew／Unterreiner／Schramm（2021），*AGLVQ - Making Generalized Learning Vector Quantization Aware of Context*，ESANN557–562，[原文](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)，DOI10.14428/esann/2021.ES2021-40。本站改成單截距、RPM低階多項式、全部known train最小平方初始化、平方距離／平均sigmoid(4mu)／L-BFGS-B、固定aux=.01；完整改編與作者MIT code SHA見sources.md及exp17手冊。二次static精確對應各RPM每類平均中心，是條件化控制。不是原作者TF模型完整重現。

C02/M factory拒絕器完全不變，未知召回預期不變；cal不fit分類器，selection/validation空。所有scaler、metric、prototype fit由train繼承或重建，audit實際IDs／RPM／SHA可追溯。固定協定checksum f2c3d40bddc99066e2a94fa0bc9b240b35cfd1c8e62a1ce8297c99ac4addef25，事前commit b2896；來源重建commit0462e4b後才outer。

## 全方法成績

除特別標示，均是motor-macro；fault accuracy／F1只含true known faulty，但混淆矩陣保留healthy／unknown輸出欄。完整final F1另用所有truth及final decisions，不能互換分母。static identity各seed相同；metric static仍受父metric seed影響。三seeds不是三次新採集。

|方法|known accuracy%（seed0）|fault accuracy%（seed0/1/2）|fault F1（seed0）|healthy total alarm%（seed0）|完整final fault F1（seed0 pooled）|
|---|---|---|---|---|---|
|C02|34.153|26.613/26.613/26.613 |0.240401|26.870|0.166613|
|C17|39.286|30.431/30.431/30.431 |0.285191|14.126|0.223283|
|C24|32.168|30.909/30.909/30.909 |0.286643|63.407|0.194219|
|D01|39.286|30.431/30.431/30.431 |0.285191|14.126|0.220229|
|G01|34.600|30.366/30.366/30.366 |0.260646|42.635|0.235106|
|G03|33.785|27.492/30.761/29.040 |0.233048|32.822|0.207804|
|G13|34.743|25.504/31.312/37.111 |0.190424|17.272|0.181196|
|G15|37.031|26.637/20.148/25.680 |0.207072|8.924|0.203432|
|I01|29.338|28.212/28.212/28.212 |0.264046|63.850|0.192655|
|I02|25.957|21.392/22.726/23.600 |0.194960|49.077|0.134176|
|I03|25.682|21.335/23.138/23.734 |0.193770|50.519|0.132283|
|I04|26.311|24.968/24.968/24.968 |0.234438|66.066|0.175951|
|I05|27.130|25.864/25.590/23.818 |0.228225|65.570|0.182408|
|I06|27.159|25.905/25.638/23.845 |0.228636|65.605|0.182714|
|I07|35.693|28.871/29.892/28.879 |0.232175|28.947|0.184083|
|I08|36.008|27.395/29.337/26.935 |0.261441|19.513|0.179329|
|I09|36.014|27.402/29.309/26.865 |0.261521|19.513|0.179367|
|I10|37.119|29.997/31.196/28.881 |0.273905|25.841|0.202522|
|I11|38.901|31.214/30.370/27.347 |0.287168|21.310|0.211943|
|I12|38.889|31.214/30.383/27.341 |0.287115|21.377|0.211908|

所有I未知motor-macro召回18.4367%，與C02/M相同；T1=0%、T3=8.4011%、T2=46.9091%。完整AUPR、AUROC、FPR@95TPR、prevalence、confusion及每motor/RPM/class/seeds含support存於summary。108格合計1,040,760筆預測，唯一樣本28,910，不當成新增百萬獨立樣本。

## 馬達分層（seed0）

|方法|test motor|fault accuracy%|healthy total alarm%|unknown recall%|2screws recall%|
|---|---|---|---|---|---|
|I01|T3|13.925|28.781|8.401|8.325|
|I01|T1|45.287|97.477|0.000|0.000|
|I01|T2|25.425|65.291|46.909|32.647|
|I02|T3|16.935|16.479|8.401|0.102|
|I02|T1|31.614|98.688|0.000|0.000|
|I02|T2|15.626|32.063|46.909|27.451|
|I03|T3|17.041|18.059|8.401|0.203|
|I03|T1|31.614|98.789|0.000|0.000|
|I03|T2|15.350|34.709|46.909|27.451|
|I04|T3|27.999|33.860|8.401|30.863|
|I04|T1|24.049|100.000|0.000|6.429|
|I04|T2|22.857|64.339|46.909|38.725|
|I05|T3|25.583|33.747|8.401|17.259|
|I05|T1|28.560|100.000|0.000|15.204|
|I05|T2|23.449|62.963|46.909|61.961|
|I06|T3|25.646|33.747|8.401|17.259|
|I06|T1|28.540|100.000|0.000|14.898|
|I06|T2|23.528|63.069|46.909|61.961|
|I07|T3|35.481|32.619|8.401|36.751|
|I07|T1|24.009|20.888|0.000|0.000|
|I07|T2|27.124|33.333|46.909|32.647|
|I08|T3|35.735|31.151|8.401|36.244|
|I08|T1|21.440|0.404|0.000|0.000|
|I08|T2|25.010|26.984|46.909|32.647|
|I09|T3|35.757|31.151|8.401|36.345|
|I09|T1|21.440|0.404|0.000|0.000|
|I09|T2|25.010|26.984|46.909|32.647|
|I10|T3|32.153|31.377|8.401|36.751|
|I10|T1|29.490|19.374|0.000|0.000|
|I10|T2|28.348|26.772|46.909|48.529|
|I11|T3|31.412|30.700|8.401|36.345|
|I11|T1|28.883|6.458|0.000|0.000|
|I11|T2|33.347|26.772|46.909|63.039|
|I12|T3|31.412|30.700|8.401|36.345|
|I12|T1|28.883|6.660|0.000|0.000|
|I12|T2|33.347|26.772|46.909|63.039|

27個motor/RPM/seed格子的完整安全結果在machine summary與evaluation中。每方法最弱motor-class recall均0，worst RPM healthy總alarm全部達100%；平均不能掩蓋這些格子。健康alarm包含錯報成known fault與拒絕為unknown兩個互斥事件。

## 失敗分析與配對

I11 seed0 fault accuracy31.214%，比C24的30.909%只多0.305pp，沒有跨seeds的至少2pp提升；seed1/2降至30.370%／27.347%。I11對同degree static I10的差為+1.217／−0.826／−1.534pp，不支持判別學習穩定改善。其F1 seed0=.287168接近C17=.285191，但不及+0.02要求，且多motor有class collapse。

I04（二次identity static）讓T1 healthy全部判為fault：total alarm100%；已知配置局部召回增加不能作安全改善。I07/I08/I09的T3 2screws召回約36%，但T1仍0，說明RPM條件化沒有消除motor差異。這支持「工況代碼本身不足以修復跨motor轉移」的有限結論；缺raw／安裝／負載證據，不能確定domain shift的物理原因。T1/T2/T3是不同個體，不能串成退化生命週期。

720個逐fold/seed配對涵蓋C02/C17/C24/D01、同幾何pooled G controls、degree／variant／geometry差異；每一對test IDs、truth與source SHA一致。不因看過結果改degree、aux、seed或門檻。下一批exp18先行手冊在I評估未結束時固定全部12父分類器，另測距離／歧義／OR，不挑I11。

## VERIFIED、FAILED／INCOMPLETE、UNKNOWN

VERIFIED：formal fingerprint未變；108已封存模型來源重建／108完整逐筆reinfer及truth mutation；用途隔離／known-only；6ZIP、252members SHA／CRC；兩環境I20小測試與492完整回歸（執行於fit前，不能以新J測試數倒填）。正式105／linear／Maha-LW／k-NN factory與PolarMap未改。

FAILED：12方法皆未過原CONTRACT，不部署；T1 unknown0%、worst class0、最壞RPM健康alarm100%。INCOMPLETE：僅一組known subset，未完成B多subset／stress，fresh final guard每類至少2獨立test groups仍不足；不能改metadata取得PASS。UNKNOWN：session、raw windows／overlap、file-level IQR遮罩、真實安裝／units／load，沒有補造。

老師問題1：主healthy＋5known／4unknown已完成本批實跑，其他N／126組沿用歷史成果，本批未重跑；已知標籤是螺絲配置，不能稱9種獨立物理原因，可信fault-type分類仍未達成。問題2：用途、群組切分與曝露已說明和驗證；採集獨立性及final test組數缺口未修復。本輪不要求不存在的實體馬達；繼續做現有資料可支持的工程與有限探索。

## 重現、測試與交付

命令及所有phase commits見execution_log.md；機器索引result_index.json列完整路徑／semantic seals／檔案SHA。Python3.10.19/sklearn1.7.2負責科學擬合與重推；Python3.14.6僅相容性測試，不跨版本load模型。artifact archive在D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/context_prototypes_v1/archives，單一磁碟備份，不冒稱offsite。
