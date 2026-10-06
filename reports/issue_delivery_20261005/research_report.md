# 單顆馬達訓練與跨馬達校準的開放集故障辨識研究

專案 Lineage｜整理與實作代理 Codex｜讀者 指導老師與專題成員

研究期間 2026 年 10 月 2 日至 4 日；2026 年 10 月 5 日補結果判讀與交付。時間採 Asia/Taipei。版本 20261005 收尾版。較早的 10 月 1 日固定方法研究與 2,490 格研究列為背景；文件日期不當作新模型訓練日期。

## 摘要

本研究使用一顆馬達的健康與五種已知螺絲配置，從頭訓練分類器與 train-only 表示法；另一顆馬達的同組已知資料只設定未知判定門檻；第三顆馬達用於已知配置分類及四種保留配置的未知識別。三顆馬達依固定方向輪替。所有正式資料仍是 90 份 CSV、28,910 筆 105 維特徵。

近期研究涵蓋線性與樹分類器、距離與密度分數、幅值／形狀表示、度量學習、局部 Fisher、原型與工況條件原型、排列不變核、風險外推與有限表格自挑戰。控制方法 D01 的已知分類高於 C02，但 T1 未知召回仍為零，且部分工況的健康總誤報達 100%。最後 M 批的 24 方法、216 評估都完成工程驗證，沒有方法通過事前可靠性契約。本次補做的工作為 M 報告與 1,134 配對核對，沒有重訓。

研究階段採 B 路徑收尾。保留程式、模型、來源重建、逐筆預測、摘要與備份；Group DRO 保留為已規劃未實作。此結論只限定目前資料、固定方法及專案有限適配，不能推論所有開集研究無效。現有 rows 都有歷史 test 曝露，採集 session／原始視窗邊界未知，獨立 final test 仍不完整，不能宣稱部署可靠。

## 一 研究問題與老師建議

老師提出兩個問題：資料含健康與九種 faulty 配置，為何仍無法訓練可信的 fault type；train、calibration 與 test 切分有何依據。本研究先將 healthy-only 冷啟動與 healthy＋known faults 分開。此報告主題是後者：已知配置可分類，保留四種配置作 unknown。

九個 faulty labels 多為同一螺絲鬆動機制的數量／位置配置，不能等同九個已確認的獨立物理故障原因。螺絲名稱可作監督標籤；它不能提供真實損壞程度、使用時數、RUL 或健康退化百分比。不同馬達的量測差異也不等同時間演進。

同機 random split 容易讓相近視窗進入不同用途；本研究改用文件支持的馬達 T-code 作群組。固定方法避免跨折平均 validation 挑共同 winner，也取消 validation／calibration 共用。不過 raw 視窗依賴與 test 馬達數不足仍存在。修正程式用途分工不會自動產生新的採集證據。

## 二 資料與可追溯範圍

T1、T2、T3 是文件支持的三顆不同馬達；T1 描述為新機，T2、T3 為老機。固定文件為 Experiments_Guide.md 的 afcfcc419dab3103a86a8f95601d3af85890eb38 版本，第 218 與 230–231 行。文件能支持 documented leave-one-motor-out 的識別基礎；目前缺實體序號、使用時數與老化真值，個體差異和老化混雜，不能分離其效果。

正式指紋為 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。來源核驗保存 90 CSV 的 SHA、manifest IDs 與 fit 來源；沒有把正式 105 維重寫成其他格式。完全相同檔案／數值副本未發現，不代表獨立錄製已證明。三階段既有特徵的語意限制，沿 reports/fault_type_openset/provenance_followup.md 與同步 raw 工作記錄；本期不重建或補造未知的 raw-window mapping。

每配置的 session／run 次數、連續錄製邊界、時間欄位、真正採樣率、stride／overlap、刪點遮罩、原始對齊、感測器單位／安裝／負載都保留 UNKNOWN。程式寫 10,000 Hz 不能證明每次採集一致。同步原始訊號 schema 是後續 ingest 契約，不等於這 90 CSV 已具備同步 raw 真值。

工況為 T1／T2／T3 × 6000／8000／11000 rpm 共九格；每格含十個標籤。RPM 是文件化工況代碼，實際每次轉速穩定度沒有獨立採集證據。九工況、九 faulty labels、三 seeds 是三個不同概念。

## 三 固定資料分工與訓練定義

known 為健康 8screws，加 faulty 1screws、2screws、3_14screws、3screws、4screws。unknown 為 4_146screws、5screws、6screws、7screws。每折只使用 train 馬達的 known 做 scaler、representation、classifier、prototype、covariance 或 neighbor reference 的擬合；cal 馬達 known 只定門檻；test 包含 known 與四 unknown。另兩顆開發馬達的 unknown 不使用。

|fold|train motor／筆|cal motor／筆|test motor／筆|test known|test unknown|
|---|---|---|---|---|---|
|0|T1/5935|T2/6007|T3/9294|5604|3690|
|1|T2/6007|T3/5604|T1/9759|5935|3824|
|2|T3/5604|T1/5935|T2/9857|6007|3850|

這些筆數由 records_for 與既有 manifest 重算，不讀 test 特徵、不擬合。fold_support.json 保存逐類／RPM 支持及排序 sample IDs 的 SHA。完整 sample IDs、來源檔 SHA、fit audits 在原 manifests、locks 和各批 source proof，並由 checkpoint_inventory 串接。

|test motor|配置|支持筆數|
|---|---|---|
|T3|1screws|949|
|T3|2screws|985|
|T3|3_14screws|940|
|T3|3screws|994|
|T3|4_146screws|923|
|T3|4screws|850|
|T3|5screws|932|
|T3|6screws|940|
|T3|7screws|895|
|T3|8screws|886|
|T1|1screws|1034|
|T1|2screws|980|
|T1|3_14screws|1027|
|T1|3screws|905|
|T1|4_146screws|1028|
|T1|4screws|998|
|T1|5screws|874|
|T1|6screws|944|
|T1|7screws|978|
|T1|8screws|991|
|T2|1screws|1003|
|T2|2screws|1020|
|T2|3_14screws|1054|
|T2|3screws|1030|
|T2|4_146screws|1010|
|T2|4screws|955|
|T2|5screws|1084|
|T2|6screws|992|
|T2|7screws|764|
|T2|8screws|945|

所有研究 seeds 固定 0、1、2。三次循環只涵蓋 T1/T2/T3、T2/T3/T1、T3/T1/T2 三個 ordered assignments；沒有宣稱完成六種方向全排列。確定性模型的 seeds 可能同值，照實保存，不畫虛假的誤差條。

validation_sample_ids 與 selection_sample_ids 都為空、selection_policy=none。參數來自事前 registry／protocol，不藉 cal／test 選表示、閾值策略或 seed。本研究名單受先前歷史結果影響，因此本次執行前鎖定仍屬探索性，不能稱盲測。現有 28,910 rows 都有歷史 test 曝露；在此折未 fit 的 test motor 並非整段研究從未看過。

從頭訓練指每 fold 只從該 motor known 估計必要權重。M 的 ERM warm start 同樣從零用該 fold known 擬合，再進入固定步數遮蔽訓練；沒有外部預訓練權重。復用封存 C02 reference 是共用已知資料的控制，不算新分類器訓練或外部遷移。

## 四 指標分母與可靠性契約

known accuracy 的分母為 healthy＋五 known faulty，使用原始分類器 labels，不含 reject。fault accuracy、balanced accuracy、conditional fault macro-F1 只在真值為五 known faulty 的 rows 計算，錯判 healthy 仍保留。全分母 final fault F1 使用所有 test 真值與最終決策，包含 healthy／unknown 被誤判 known fault 的 false positives；四 unknown 合併為 unknown 輸出，五 fault 為計算 F1 的目標類別。不能將條件 F1 和全分母 F1 混用。

健康總誤報以最終互斥決策計算：healthy→UNKNOWN 加 healthy→accepted known fault，分母是所有 true healthy。被 reject 的 raw fault 誤判只算一次。unknown recall／precision／F1 以保留的四配置為 positive，AUROC／AUPR 用越高越未知的分數，AUPR 須和該 motor 的 unknown prevalence 一起閱讀。coverage 為接受數／全部 test；accepted accuracy 只在接受者內。沒有 positives 或零分母採原 verifier 的缺失規則，不能補成完美值。

描述主表採 seed0 三 motor 等權平均，附錄保存各 seed 的實值；全分母 final fault F1 主表另標 pooled 28,910 rows。不同 motor 的分數尺度不同，不把 pooled raw scores 的 AUROC 當泛化證據。各 motor、RPM、類別和全部 seeds 的完整值，以封存 summary／evaluation 為準。

原 continuous_reliability_v1 要求各 seed 的 fault accuracy 相對 C24 至少 +0.02、fault macro-F1 相對 C17 至少 +0.02；每 motor×RPM 健康總誤報 ≤0.10；每 motor×known-fault recall ≥0.10；每 motor unknown recall ≥0.10。另要求 motor F1 不劣超過 0.01、各 RPM unknown recall 相對 C02 不劣超過 0.02、reject 後正確率相對 D01 不劣超過 0.01、coverage 相對 D01 不劣超過 0.10。全文沿 core/fault_type_reliability.py:CONTRACT，不放寬失敗條件。

主篩通過後還要多 known subsets、匹配消融與壓力測試才可能支持 B 級證據；獨立 fresh final 和每類至少兩個 test groups 才能支援 C 級。近期各批只做一組固定 N=5 初篩，不能以三 seeds 充當更多馬達。

## 五 主控制與解耦設計

C02 是 base75＋balanced logistic＋factory Mahalanobis–LW；C17 為 harmonic69＋uniform shrinkage LDA＋該表示的 factory Mahalanobis；C24 為 base75 per-RPM LDA＋對應 factory Mahalanobis 控制。D01 保留 C17 分類器，搭原 C02/M reference。C17 與 D01 的分類成績相同，拒絕成績可能不同。控制綁定見 experiments/fault_type_continuous_report.py 第 20–21 行。每個配對要求相同 test IDs；不把同一分類器換 detector 當新的分類進步。

|方法|known %|fault %|條件 F1|健康總誤報 %|unknown recall %|
|---|---|---|---|---|---|
|C02|34.15|26.61|0.2404|26.87|18.44|
|C17|39.29|30.43|0.2852|14.13|8.44|
|C24|32.17|30.91|0.2866|63.41|21.07|
|D01|39.29|30.43|0.2852|14.13|18.44|

|方法|全分母 final fault F1|unknown AUROC|unknown AUPR|coverage %|known拒絕後正確 %|
|---|---|---|---|---|---|
|C02|0.1666|0.5746|0.4397|85.00|29.04|
|C17|0.2233|0.5756|0.4498|93.69|39.26|
|C24|0.1942|0.5388|0.4197|80.35|25.98|
|D01|0.2202|0.5746|0.4397|85.00|36.79|

D01 相對 C02：known accuracy +5.13 個百分點，fault accuracy +3.82 個百分點，健康總誤報下降 12.74 個百分點；unknown recall 不變。相對 C17，unknown recall 提高 10.00 個百分點，但 known rejection 從 4.94% 增至 12.82%，known 拒絕後正確率從 39.26% 降至 36.79%。D01 仍有零召回與高誤報工況，不是可靠 winner。

## 六 實際方法與有限改編

### 表示法與一般分類器

正式資料維持 105 維；formal105、vibration base75、刪除重複項 dedup66、頻率形狀 harmonic69、RMS gain63／66／69 都是研究中的 train-only views，不改 CSV。幅值比值與 gain normalization 為本站操作約定；Tseng 等的旋轉頻率幅值研究提供動機 [B28]，沒有把 RMS 比值冒稱原論文公式。

linear／logistic／softmax [B04]、收縮 LDA [B01,B02]、ExtraTrees [B05]、RandomForest [B06]、histogram boosting [B07]、RBF SVM [B08]、距離加權 kNN [B03]、Gaussian NB [B09]、PCA [B10]、NCA [B11]、RDA [B12] 皆有實際舊控制。來源閱讀深度逐篇列於文後，未宣稱所有全文精讀。樹／SVM 是固定參數對照；NCA 有固定 train 子集與迭代預算，缺項保留 INCOMPLETE。原文其他模型與資料的高分不能移植成本站成績 [B38–B40]。

LDA 使用 lsqr、uniform priors 與指定 shrinkage，C02 logistic 的 C=1、balanced、lbfgs、max_iter=1000。樹控制固定 200 棵、max_depth=12、min_samples_leaf=5；histogram boosting 為 200 steps、learning_rate=.05、l2=1、early_stopping=false。SVM C=1、gamma=scale；kNN k=5／15、distance、brute；PCA full SVD 不 whitening。逐 arm 的實際 sklearn 參數保存在 catalog 的 protocol.classifier_parameters，包含 seeds，不能把文中的簡述當完整 runtime 配置。

### 馬式距離與其他拒絕分數

Ledoit–Wolf [B02] 收縮 empirical covariance 的不穩定小特徵值，讓逆矩陣與距離較穩定。這不能保證 unknown 在幾何上遠離 known，也不能保證另一馬達的 cal 分布適合 test 馬達。逐類距離公式如下；Σc、μc 僅由 known train 建立。

EQUATION: d_c²(x) = (x − μ_c)ᵀ Σ_c⁻¹ (x − μ_c)

factory 使用逐類 known calibration 分位數，正規化距離分數 >1 拒絕；k-NN reference 同樣只用 train、k=5、confidence=.95，沿 core.openset factory。分類器和拒絕器可解耦；cal 不能流入 reference。其他已實測分數包括 pooled Mahalanobis [B13]、背景相減 RMD [B14]、OAS [B15]、diagonal／local／centroid／多中心、Isolation Forest [B16]、novelty LOF [B17]、One-Class SVM [B18]、diagonal GMM 的 EM [B19]、MSP [B20]、熵 [B21]、energy [B22]、ViM [B23] 與 KMeans 多原型 [B24]。它們是表格資料的有限適配，不是深層 OOD 論文完整復現。

RMD 保留背景距離相減後可能為負的 raw score，不能統一用除門檻歸一化。MSP 使用 1−max probability，known cal pooled 的 linear q95，strict raw>q 拒絕。不能把 signed score、MSP、factory 的規則混成同一個大於 1。歷史 conformal [B25]／RPM／predicted-class routing 只按實際產物列入背景控制，跨馬達 exchangeability 未證明，沒有固定 5% 誤報保證。

EQUATION: s_MSP(x) = 1 − max_c p(c | x)    q = Quantile₀.₉₅(s_MSP(X_cal,known))

### 度量學習與局部 Fisher

LMNN-inspired [B26] 採非負 diagonal weights，等 pull／push=.5、target k=3、identity ridge=.01、固定每類 RPM20 筆，沒有學完整 PSD 矩陣。Q 的 150 iteration 部分 fit 不收斂；train-only 27 次 solver 診斷比較 hard150、smooth150、hard600。smooth loss 只借 Rennie／Srebro 的 scalar logistic 思路 [B27]，沒有實作推薦系統 MMMF。E 使用已封存 hard600 度量，比較近鄰、target-neighbor energy 與一／三中心；unknown 不進 triplets、參考庫或校準。

LFDA [B29] 用類內第七鄰居 self-tuning affinity 與 pairwise scatter，固定 ridge=trace(Sw)/d×1e−6，取 10／20 正方向並以特徵值平方根加權。每類 RPM20 筆子集，PCA10／20 配對使用同子集。正方向不足應 INCOMPLETE，不補方向。兩分類器 LDA／5NN 及 factory score 對照分開，識別表示效果與 detector 效果。

### 判別原型與工況拒絕

GLVQ [B30] 使用 train 真值找最近同／異類原型 d+、d−，相對差 μ 經 sigmoid 損失。本站固定 beta=4、epsilon=1e−12、mean loss、L-BFGS-B、anchor 0／.01、每類一／三個中心；不重現原文隨時間變窄的 sigmoid 或影像架構。平方距離與 smooth-L1 [B31] 準範數／範數兩版配對，alpha=20；改動詳見 exp15／16，解析梯度有有限差分測試。

EQUATION: μ = (d₊ − d₋) / (d₊ + d₋ + ε)    J = mean sigmoid(4μ) + λ mean((W − W₀)²)

AGLVQ [B32] 啟發本站 RPM-conditioned prototype：context=(RPM−8000)/3000，degree1／2、static／GLVQ／aux=.01，兩種幾何、同 train 最小平方初始化。此支線明確使用文件化 RPM 作 context；不使用 T-code、路徑或 test fault truth。與一般不含 RPM 的分類器分開報告。沒有執行原作者舊 TF／Keras 程式。

prototype rejection [B33] 比較距離、相對模糊度和 OR fusion。原文 threshold search 未移植；本站只用 pooled known cal q95，OR 用 signed normalized excess 的最大值，threshold=0。高 unknown recall 若伴隨健康總誤報 99% 不能判成功。

### 軸排列不變核

Haasdonk／Burkhardt [B34] 的群平均核啟發本站三軸 S3 六排列，固定共享 scaler、Gaussian gamma=1/66、alpha=0/.5/1；SVM C=1、balanced、precomputed。自建 RKHS 類中心距離拒絕沿 known cal q95。這只處理座標排列，不代表任何旋轉、感測器重安裝或單位問題都消除；方向變動沒有採集真值可確認。

### RPM 風險外推與有限表格自挑戰

REx [B35] 的原則是減少開發環境間風險差異。本站 L 使用三 RPM 等權、各 RPM 六 known 類等權 cross entropy，beta=0／1／10、population variance、W ridge=.001，兩表示 ×三係數 ×三detectors。全部 54 fits 收斂，只證明固定目標已求解，不證明跨 motor 泛化。本文公式是本站有限適配。

EQUATION: J = mean_r R_r + β Var_r(R_r) + 0.001 ‖W‖²

RSC [B36] 原文使用影像特徵與網路訓練。本站 M 不新增 CNN，使用 base75／harmonic69 線性 softmax；由同 fold known train ERM warm 開始，固定 200 full-batch steps，最後 iterate。四版為 unmasked、random、signed_gradient（W_y，不取絕對值）、contribution（z×W_y）。每樣本遮蔽 ceil(D/3) features，再選 probability-drop 最大 ceil(n/3) rows；stable ties、stop-gradient、負貢獻保留。eta=1/(.5×weighted_augmented_train_trace+.001)，train-only 決定；bias 不處罰，ridge 只套 W。推論不使用真值、不遮蔽，不用 cal／test 早停。

EQUATION: η = 1 / (0.5 weighted_augmented_train_trace + 0.001)

原文 RSC 的 CNN、Adam、curriculum、影像 headline accuracy 未在本站復現。M 的遮蔽／固定預算為有限改編，對照 unmasked／random 可反駁「單靠遮蔽更可靠」的假說。72 fine fits 與 18 warm fits 分開；200 steps 為 FIXED_HORIZON_COMPLETE，不標 optimizer convergence。Group DRO [B37] 只有 exp22 手冊與來源卡，完全未 fit、未測；不列性能榜。

## 七 研究過程與完整執行範圍

|批次|planned評估|completed|INCOMPLETE|預測records|可靠性|
|---|---|---|---|---|---|
|文獻 C|630|624|6|6013647|無同版主篩；保留探索結果|
|機制 D/P|81|81|0|780570|無同版主篩；保留探索結果|
|Q|72|60|12|576144|FAILED:6／INCOMPLETE:2|
|E|108|108|0|1040760|FAILED:12|
|F|144|144|0|1387680|FAILED:16|
|G|216|216|0|2081520|FAILED:24|
|H|108|108|0|1040760|FAILED:12|
|I|108|108|0|1040760|FAILED:12|
|J|324|324|0|3122280|FAILED:36|
|K|81|81|0|780570|FAILED:9|
|L|162|162|0|1561140|FAILED:18|
|M|216|216|0|2081520|FAILED:24|

各批以 batch／arm／fold／seed 身分去重，表內 prediction records 是重複推論，不新增獨立資料。表中 reliability FAILED 和 runner error 分開；INCOMPLETE 留原缺項，不能補做容易格後報全部完成。本回合只讀歷史產物與補 M report，不重跑歷史 2,490 格。

Q 的數值失敗由封存末 weights、optimizer message 與固定預算記錄；使用額度中斷不能算演算法失敗。solver27 只有 train-only 診斷，沒有追加 outer prediction。hard600 九 fit 收斂於 ftol，不能隱藏 projected-gradient 尚高於 gtol 的情況。該結果支持預算／停止規則的重要性，不支持 test 成績提升。

K 的不變核全部九方法、L 的風險外推十八方法，以及 M 的自挑戰二十四方法未通過原契約。L 增大 beta 可降低 train RPM 風險差異，但跨 motor 最差類仍為零，反駁「train 工況更一致即可得到可靠 cross-motor」這個充分條件。

## 八 成績 消融與最差工況

|方法|known %|fault %|條件 F1|健康總誤報 %|unknown recall %|
|---|---|---|---|---|---|
|Q07|39.82|33.92|0.3041|29.14|8.71|
|F02|41.01|33.42|0.2985|18.95|18.44|
|G16|37.03|26.64|0.2071|8.92|20.22|
|J03|29.34|28.21|0.2640|68.25|24.60|
|K09|28.47|24.39|0.1999|69.62|22.69|
|L10|37.29|31.25|0.2666|30.46|18.44|
|L16|37.32|31.28|0.2668|30.46|18.44|
|M13|37.29|31.25|0.2666|30.46|18.44|
|M22|36.44|30.08|0.2379|29.75|18.44|

這些是解釋失敗的代表，沒有指定 global winner 或部署替換。所有新 arms 的主數值在附錄列出；全部 fold／seed／RPM／class 的原指標與混淆矩陣在 method_catalog、各批 summary 和 evaluation，一併引用來源與 SHA。

|M方法／seed|fault %|條件 F1|健康總誤報 %|unknown recall %|
|---|---|---|---|---|
|M01/0|26.00|0.2406|40.91|18.44|
|M01/1|26.00|0.2406|40.91|18.44|
|M01/2|26.00|0.2406|40.91|18.44|
|M02/0|26.00|0.2406|40.99|5.45|
|M02/1|26.00|0.2406|40.99|5.45|
|M02/2|26.00|0.2406|40.99|5.45|
|M03/0|26.00|0.2406|44.74|4.60|
|M03/1|26.00|0.2406|44.74|4.60|
|M03/2|26.00|0.2406|44.74|4.60|
|M04/0|24.83|0.2183|56.11|18.44|
|M04/1|24.88|0.2188|56.29|18.44|
|M04/2|24.83|0.2182|56.15|18.44|
|M05/0|24.83|0.2183|56.18|5.45|
|M05/1|24.88|0.2188|56.36|5.45|
|M05/2|24.83|0.2182|56.22|5.45|
|M06/0|24.83|0.2183|61.31|3.89|
|M06/1|24.88|0.2188|61.38|3.87|
|M06/2|24.83|0.2182|61.34|3.88|
|M07/0|26.22|0.2033|83.31|18.44|
|M07/1|26.22|0.2033|83.31|18.44|
|M07/2|26.22|0.2033|83.31|18.44|
|M08/0|26.22|0.2033|83.31|5.45|
|M08/1|26.22|0.2033|83.31|5.45|
|M08/2|26.22|0.2033|83.31|5.45|
|M09/0|26.22|0.2033|83.60|1.68|
|M09/1|26.22|0.2033|83.60|1.68|
|M09/2|26.22|0.2033|83.60|1.68|
|M10/0|26.99|0.2175|82.82|18.44|
|M10/1|26.99|0.2175|82.82|18.44|
|M10/2|26.99|0.2175|82.82|18.44|
|M11/0|26.99|0.2175|82.82|5.45|
|M11/1|26.99|0.2175|82.82|5.45|
|M11/2|26.99|0.2175|82.82|5.45|
|M12/0|26.99|0.2175|84.28|1.21|
|M12/1|26.99|0.2175|84.28|1.21|
|M12/2|26.99|0.2175|84.28|1.21|
|M13/0|31.25|0.2666|30.46|18.44|
|M13/1|31.25|0.2666|30.46|18.44|
|M13/2|31.25|0.2666|30.46|18.44|
|M14/0|31.25|0.2666|30.46|5.45|
|M14/1|31.25|0.2666|30.46|5.45|
|M14/2|31.25|0.2666|30.46|5.45|
|M15/0|31.25|0.2666|30.67|5.30|
|M15/1|31.25|0.2666|30.67|5.30|
|M15/2|31.25|0.2666|30.67|5.30|
|M16/0|29.53|0.2489|30.60|18.44|
|M16/1|29.52|0.2489|30.60|18.44|
|M16/2|29.51|0.2488|30.60|18.44|
|M17/0|29.53|0.2489|30.60|5.45|
|M17/1|29.52|0.2489|30.60|5.45|
|M17/2|29.51|0.2488|30.60|5.45|
|M18/0|29.53|0.2489|31.13|6.36|
|M18/1|29.52|0.2489|31.17|6.42|
|M18/2|29.51|0.2488|31.20|6.45|
|M19/0|30.54|0.2519|39.47|18.44|
|M19/1|30.54|0.2519|39.47|18.44|
|M19/2|30.54|0.2519|39.47|18.44|
|M20/0|30.54|0.2519|39.47|5.45|
|M20/1|30.54|0.2519|39.47|5.45|
|M20/2|30.54|0.2519|39.47|5.45|
|M21/0|30.54|0.2519|39.96|2.51|
|M21/1|30.54|0.2519|39.96|2.51|
|M21/2|30.54|0.2519|39.96|2.51|
|M22/0|30.08|0.2379|29.75|18.44|
|M22/1|30.08|0.2379|29.75|18.44|
|M22/2|30.08|0.2379|29.75|18.44|
|M23/0|30.08|0.2379|29.79|5.45|
|M23/1|30.08|0.2379|29.79|5.45|
|M23/2|30.08|0.2379|29.79|5.45|
|M24/0|30.08|0.2379|30.21|3.50|
|M24/1|30.08|0.2379|30.21|3.50|
|M24/2|30.08|0.2379|30.21|3.50|

M13 相對 C17 的 fault accuracy 提高 0.82 個百分點，條件 F1 變動 -0.0186，健康總誤報增加 16.34 個百分點。這個局部分類增加不符合 F1 和安全保護。M13 相對 C24 的 fault accuracy 只增加 0.34 個百分點，未達 +2 個百分點。

|M13 test motor|known %|fault %|條件 F1|健康總誤報 %|unknown recall %|
|---|---|---|---|---|---|
|T3|34.46|22.15|0.2161|0.00|8.40|
|T1|37.00|37.18|0.2919|63.87|0.00|
|T2|40.42|34.43|0.2916|27.51|46.91|

|M13 motor／RPM|健康筆數|健康→未知 %|健康→已知fault %|健康總誤報 %|unknown recall %|
|---|---|---|---|---|---|
|T3/6000rpm|314|0.00|0.00|0.00|0.00|
|T3/8000rpm|272|0.00|0.00|0.00|0.00|
|T3/11000rpm|300|0.00|0.00|0.00|25.18|
|T1/6000rpm|320|0.00|100.00|100.00|0.00|
|T1/8000rpm|313|0.00|100.00|100.00|0.00|
|T1/11000rpm|358|0.00|0.00|0.00|0.00|
|T2/6000rpm|324|0.00|0.00|0.00|0.00|
|T2/8000rpm|368|0.00|1.90|1.90|54.15|
|T2/11000rpm|253|0.00|100.00|100.00|80.23|

|M13 motor|配置|支持筆數|classifier recall %|reject rate %|
|---|---|---|---|---|
|T3|8screws|886|100.00|0.00|
|T3|1screws|949|25.61|19.39|
|T3|2screws|985|0.91|0.00|
|T3|3_14screws|940|27.77|0.00|
|T3|3screws|994|53.52|30.68|
|T3|4screws|850|0.00|33.29|
|T3|4_146screws|923|NA|33.59|
|T3|5screws|932|NA|0.00|
|T3|6screws|940|NA|0.00|
|T3|7screws|895|NA|0.00|
|T1|8screws|991|36.13|0.00|
|T1|1screws|1034|33.75|0.00|
|T1|2screws|980|0.00|0.00|
|T1|3_14screws|1027|58.13|0.00|
|T1|3screws|905|98.56|0.00|
|T1|4screws|998|0.00|0.00|
|T1|4_146screws|1028|NA|0.00|
|T1|5screws|874|NA|0.00|
|T1|6screws|944|NA|0.00|
|T1|7screws|978|NA|0.00|
|T2|8screws|945|72.49|0.00|
|T2|1screws|1003|100.00|38.58|
|T2|2screws|1020|31.57|68.73|
|T2|3_14screws|1054|15.46|1.04|
|T2|3screws|1030|0.00|37.28|
|T2|4screws|955|26.70|0.00|
|T2|4_146screws|1010|NA|37.92|
|T2|5screws|1084|NA|64.94|
|T2|6screws|992|NA|60.69|
|T2|7screws|764|NA|15.31|

M13 的 seeds 0／1／2 結果完全相同；random 版有微小變動，其他版相同時亦原樣保留。不能把三 seeds 的低 SD 當馬達母體信賴區間。三顆 motor 沒有足夠採集群組支援逐窗 IID bootstrap 的精準泛化保證。

|M方法|主篩|最差類召回 %|最差工況健康誤報 %|最差motor未知召回 %|
|---|---|---|---|---|
|M01|FAILED|0.00|96.44|0.00|
|M02|FAILED|0.00|97.23|0.00|
|M03|FAILED|0.00|98.53|0.00|
|M04|FAILED|0.00|96.20|0.00|
|M05|FAILED|0.00|96.84|0.00|
|M06|FAILED|0.00|96.84|0.83|
|M07|FAILED|0.00|100.00|0.00|
|M08|FAILED|0.00|100.00|0.00|
|M09|FAILED|0.00|100.00|0.44|
|M10|FAILED|0.00|100.00|0.00|
|M11|FAILED|0.00|100.00|0.00|
|M12|FAILED|0.00|100.00|0.00|
|M13|FAILED|0.00|100.00|0.00|
|M14|FAILED|0.00|100.00|0.00|
|M15|FAILED|0.00|100.00|3.22|
|M16|FAILED|0.00|100.00|0.00|
|M17|FAILED|0.00|100.00|0.00|
|M18|FAILED|0.00|100.00|1.52|
|M19|FAILED|0.00|100.00|0.00|
|M20|FAILED|0.00|100.00|0.00|
|M21|FAILED|0.00|100.00|0.44|
|M22|FAILED|0.00|100.00|0.00|
|M23|FAILED|0.00|100.00|0.00|
|M24|FAILED|0.00|100.00|0.26|

所有 M 方法逐 seed 最差 known fault recall 為零，健康 motor-macro 三seed實值範圍約 29.75%–84.28%。逐方法原始 reasons 包含 motor／RPM／seed，見 decision_record.full_contract_gates；附錄保留原因計數及完整索引，沒有只留下表現較好 seed。

## 九 失敗分析與可反駁假說

已排除的工程疑點包括 test IDs／SHA 不匹配、來源副本別名繞過、cal 混入 fit、test truth 改變推論、NaN／分數方向／reject 符號與報表分母錯配。來源 proof 從 known train／cal 重建模型與 threshold，test_numeric_reads=0；outer verifier 再逐筆重推及重算。工程 VERIFIED 的範圍是保存的 formal 計算鏈，沒有由此推導 raw 採集獨立性。

配置重疊有模型行為證據：D01 三 motor 的 2screws recall 都為零，多支線仍有零類別。它支持「現有表示與已知分類邊界不足」的診斷，不能直接證明原始物理訊號不可分。T1 的 factory 未知召回為零；相同 reference 下更換分類器仍為零是控制預期，不能只改 classifier 就稱 OOD 已改善。

motor domain shift 與 calibration transfer 有跨 motor／RPM 的分層差異支持。T1 可在某些替代 detector 得到較高 unknown recall，但會伴隨健康大幅誤報；J03 與 K09 是明確例子。局部召回提高不足以通過安全保護。AUROC 接近有限排序能力也說明只調 threshold 未必解決分布重疊，本輪沒有用 T1 test 掃最有利閾值。

形狀與幅值、軸對應、RPM context 等改編有合理機制，卻沒有通過全面契約。L 的 train 風險差異降低、M 的遮蔽訓練完成都沒有消除最差類與健康誤報。這些失敗反駁有限適配的充分條件，不否定原論文。感測器安裝、實際負載、個體老化是否造成偏移，目前缺證據，只列可能解釋。

未取得時間順序與 raw session，不能計算每小時誤報／警報延遲；未取得退化真值，不能計算 RUL 或損壞百分比。失敗後未回寫本輪 test 規則，保留全部不利格。

## 十 可信度狀態與老師問題回覆

|項目|狀態|支持範圍|
|---|---|---|
|正式計算鏈／逐筆預測|VERIFIED|來源 SHA／IDs、known-only fit、216逐筆驗證與1,134配對|
|M可靠提升|FAILED|24方法未達原契約；沒有部署替換|
|多known subsets穩健改善|INCOMPLETE|近期初篩只用一組N=5；歷史Nsweep不替代新方法驗收|
|獨立fresh／每類≥2 test groups|INCOMPLETE|所有rows歷史曝露，每折一顆test motor|
|raw sessions／overlap／清理遮罩|UNKNOWN|formal副本檢查不能證明採集獨立|
|N Group DRO|未實作|只有手冊與來源卡；不是演算法FAILED|
|Word逐頁排版|見content_qa.json|內容與ZIP檢查不等於PNG視覺驗收|

老師問題一為部分完成：健康＋五 known／四 unknown 的主要配置有完整實測；歷史 N=5 的全部 126 組、N=1–8 與 N=9 closed-set／Protocol B 已執行，歷史合計 2,490 格，但本輪未重跑全部 N 或組合。近期只在一個固定 known subset 做方法初篩，未找到可信 fault configuration 模型，不能把可執行 runner 當可靠 fault type 已解決。

老師問題二為部分完成：已清楚定義 motor 群組用途、取消共同跨折選模型與 validation／cal 共用，單折 IDs 分離與 known-only fit 可驗證。「切分不完整」仍包含每類 test motor group 不足、raw session／overlap／清理遮罩未知、歷史曝露及未具 fresh final。這些缺口不能用洗牌、新 seed、改名或 metadata 更正文句消除。

## 十一 本階段結論與保留資產

沒有候選同時達主要改善與最差組保護，採 B 路徑封存。可靠提升仍 false，production replacement=false。正式 105 維／linear／Mahalanobis–Ledoit–Wolf 預設與 PolarMap 不改；factory k-NN 仍可切換。階段結案不關閉整個專案、不刪分支、不影響其他使用者工作。

M 真正中斷在 report／配對、過期 state 與交付；evaluate 和 verification 早已完成。本次只補報告、驗收、備份與狀態修正。六份 ZIP 共 468 source members 通過 whole／member SHA／CRC，保留原模型／預測及舊 ZIP。同機 D 槽是可恢復副本，不是異地備援。M restore 還依賴父批的 reference／protocol，不能把六包冒稱全部歷史依賴已自含。

## 十二 後續方向與停止條件

本輪交付後不開新批。若使用者另行授權，可先重新定義研究問題為配置識別而非九個物理故障原因，預先固定少量比較並沿現有安全契約；仍須標探索性，不能取得 fresh 身份。另一方向是對來源可驗證的新資料使用同步 ingest／raw feature contract；目前沒有實體馬達，不要求重新採集作此輪前置。現有 ingest 只提供入口，不宣稱已採集。

Group DRO 的 proposed group reweighting／regularization 與 exp22 手冊保留，狀態為已規劃未實作。若再啟用，需新的事前授權與固定成功條件；目前結果沒有足夠訊號支持本回合自動啟動。

## 十三 工具 重現與交付驗收

科學執行環境 Python3.10.19、NumPy2.2.6、SciPy1.15.3、sklearn1.7.2；相容工程環境 Python3.14.6、NumPy2.5.3、SciPy1.18.1、sklearn1.9.1，不跨版本載入正式 joblib。運算沿既有 CPU runner；未安裝 metric-learn／sklearn-lvq 或作者影像 TF 框架，不宣稱 GPU 訓練。工具為現有 logger、factory、FeatureStore、source verifier、outer verifier 與 archive／delivery。

原 618 項完整科學測試已在 10 月 4 日兩環境通過，pip check 與 37 CLI helps 等共 39 commands 全部 exit0；本次沒有再跑618。新增盤點與格式化共11項 toy tests 在兩環境均 PASS；9項是前一盤點 checkpoint。Word 使用 loader 的 bundled Python 與 python-docx，與科學環境分開，不升級原實驗依賴。

研究根目錄：C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree。備份根目錄：D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-04/feature_self_challenging_v1/archives。

唯讀盤點：`.venv310/Scripts/python.exe -m experiments.fault_type_research_closeout --m-report output/fault_type_self_challenging_report/2026-10-05-22-17-39/summary.json.gz`。

M 既有 report 重算：`.venv310/Scripts/python.exe -m experiments.fault_type_self_challenging report --protocol output/fault_type_self_challenging_lock/2026-10-04-22-01-49/protocol.json --evaluation output/fault_type_self_challenging_evaluate/2026-10-04-22-16-34/evaluation.json.gz --verification output/fault_type_self_challenging_verify/2026-10-04-22-18-59/verified.json.gz --baseline output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json --previous output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json`。

備份核對：`.venv310/Scripts/python.exe -m experiments.fault_type_fixed_delivery --index output/fault_type_self_challenging_backup/2026-10-05-22-24-22/archive_index.json --index output/fault_type_archive/2026-10-05-22-28-54/archive_index.json`。僅核對，不解包覆寫。

恢復時先依各批 artifact_location.json 尋找 primary_artifact；核對 ZIP whole SHA／member SHA／CRC，再在新的空目錄還原。沿各批 result_index 的 parent_protocol／parent_lock 復原父 reference；不得用 compact 摘要冒充完整模型或逐樣本 CSV。

內容與 JSON 對照、引用、Word editable elements、ZIP 及 SHA 分開驗收。頁面 PNG 渲染必須使用 bundled renderer；目前 Windows bundled runtime 無 LibreOffice，不能改用使用者 desktop 安裝。若正式 renderer 無法啟動，另以 content_qa.json 記錄 LAYOUT_UNVERIFIED，內容檢查不冒充逐頁視覺檢查。

## 十四 參考文獻與閱讀範圍

以下書目與正文 B 編號對應；原論文方法、官方 API 與本站操作約定分開。來源卡證明的全文閱讀與僅核對摘要的項目分開，本回合沒有重新讀完全部40篇。公式差異與程式碼以先行手冊和 method_catalog.protocol 為準。

[B01] Fisher, R. A. (1936). The use of multiple measurements in taxonomic problems. Annals of Eugenics 7, 179–188. [原始來源](https://doi.org/10.1111/j.1469-1809.1936.tb02137.x)

閱讀範圍：書目與方法對應；全文閱讀未獲證明。本站用途：LDA 的歷史來源；本站使用多類 Gaussian 判別及收縮。

[B02] Ledoit, O. & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. Journal of Multivariate Analysis 88, 365–411. [原始來源](https://www.ledoit.net/Well-conditioned2004.pdf)

閱讀範圍：方法與官方 API 核對；部分回合全文取得受限。本站用途：逐類與 pooled 共變異數的不同適配。

[B03] Cover, T. M. & Hart, P. E. (1967). Nearest Neighbor Pattern Classification. IEEE Transactions on Information Theory 13, 21–27. [原始來源](https://isl.stanford.edu/~cover/papers/transIT/0021cove.pdf)

閱讀範圍：書目與方法查閱；全文閱讀未獲證明。本站用途：近鄰分類的基礎；本站距離加權 k-NN 與拒絕分數不同。

[B04] Cox, D. R. (1958). The Regression Analysis of Binary Sequences. Journal of the Royal Statistical Society B 20, 215–232. [原始來源](https://doi.org/10.1111/j.2517-6161.1958.tb00292.x)

閱讀範圍：書目查核。本站用途：logistic 基礎來源；六類 L2／lbfgs 依既有 sklearn 契約。

[B05] Geurts, P., Ernst, D. & Wehenkel, L. (2006). Extremely randomized trees. Machine Learning 63, 3–42. [原始來源](https://orbi.uliege.be/handle/2268/9357)

閱讀範圍：書目與方法查閱；全文閱讀未獲證明。本站用途：ExtraTrees 固定參數對照。

[B06] Breiman, L. (2001). Random Forests. Machine Learning 45, 5–32. [原始來源](https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf)

閱讀範圍：書目與方法查閱；全文閱讀未獲證明。本站用途：RandomForest 固定參數對照。

[B07] Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. Annals of Statistics 29, 1189–1232. [原始來源](https://doi.org/10.1214/aos/1013203451)

閱讀範圍：書目與方法查閱。本站用途：sklearn histogram boosting 的思想來源，非原演算法逐步重現。

[B08] Cortes, C. & Vapnik, V. (1995). Support-vector networks. Machine Learning 20, 273–297. [原始來源](https://doi.org/10.1007/BF00994018)

閱讀範圍：出版資訊與摘要；未宣稱取得訂閱全文。本站用途：RBF 與 precomputed invariant kernel SVC。

[B09] John, G. H. & Langley, P. (1995). Estimating Continuous Distributions in Bayesian Classifiers. UAI, 338–345. [原始來源](https://arxiv.org/abs/1302.4964)

閱讀範圍：書目與方法查閱。本站用途：採 Gaussian 對照，不是該文提出的 kernel density 版本。

[B10] Pearson, K. (1901). On lines and planes of closest fit to systems of points in space. Philosophical Magazine 2, 559–572. [原始來源](https://doi.org/10.1080/14786440109462720)

閱讀範圍：書目核對；出版全文取得受限。本站用途：train-only PCA，不 whitening。

[B11] Goldberger, J., Roweis, S., Hinton, G. & Salakhutdinov, R. (2004). Neighbourhood Components Analysis. NIPS 17. [原始來源](https://papers.nips.cc/paper/2566-neighbourhood-components-analysis.pdf)

閱讀範圍：方法查閱；未宣稱全文逐頁閱讀。本站用途：NCA10，固定 train 子集與迭代預算；不同於 LMNN。

[B12] Friedman, J. H. (1989). Regularized Discriminant Analysis. JASA 84, 165–175. [原始來源](https://doi.org/10.1080/01621459.1989.10478752)

閱讀範圍：書目與摘要；原掃描公式未完整深讀。本站用途：本站 covariance 凸混合與 RPM pooling 為有限適配。

[B13] Lee, K., Lee, K., Lee, H. & Shin, J. (2018). A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks. NeurIPS 31. [原始來源](https://proceedings.neurips.cc/paper/2018/hash/abdeb6f575ac5c6676b747bca8d09cc2-Abstract.html)

閱讀範圍：方法查閱；全文閱讀未獲證明。本站用途：pooled Mahalanobis 表格適配，無深層特徵或 input perturbation。

[B14] Ren, J., Fort, S., Liu, J., Roy, A. G., Padhy, S. & Lakshminarayanan, B. (2021). A Simple Fix to Mahalanobis Distance for Improving Near-OOD Detection. UDL workshop and arXiv:2106.09022. [原始來源](https://www.gatsby.ucl.ac.uk/~balaji/udl2021/accepted-papers/UDL2021-paper-007.pdf)

閱讀範圍：§2–3、Eq.1–3、設定與特徵方向分析；非全文逐頁。本站用途：RMD 背景距離相減及本站係數／分塊消融。

[B15] Chen, Y., Wiesel, A., Eldar, Y. C. & Hero, A. O. (2010). Shrinkage Algorithms for MMSE Covariance Estimation. IEEE Transactions on Signal Processing 58, 5016–5029. [原始來源](https://arxiv.org/abs/0907.4698)

閱讀範圍：方法與 API 差異核對。本站用途：sklearn OAS 的有限實作差異保留。

[B16] Liu, F. T., Ting, K. M. & Zhou, Z. H. (2008). Isolation Forest. ICDM, 413–422. [原始來源](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)

閱讀範圍：書目與方法查閱。本站用途：all-known train，另一馬達 known-cal q95。

[B17] Breunig, M. M., Kriegel, H. P., Ng, R. T. & Sander, J. (2000). LOF: Identifying Density-Based Local Outliers. SIGMOD, 93–104. [原始來源](https://doi.org/10.1145/342009.335388)

閱讀範圍：書目與官方 novelty API 查閱。本站用途：新樣本 novelty 延伸，不冒稱原 transductive LOF。

[B18] Schölkopf, B., Platt, J., Shawe-Taylor, J., Smola, A. & Williamson, R. (2001). Estimating the support of a high-dimensional distribution. Neural Computation 13, 1443–1471. [原始來源](https://doi.org/10.1162/089976601750264965)

閱讀範圍：書目與方法查閱。本站用途：all-known One-Class SVM，非 healthy-only 多類分類器。

[B19] Dempster, A. P., Laird, N. M. & Rubin, D. B. (1977). Maximum Likelihood from Incomplete Data Via the EM Algorithm. JRSS B 39, 1–38. [原始來源](https://doi.org/10.1111/j.2517-6161.1977.tb01600.x)

閱讀範圍：書目與方法查閱。本站用途：每類 diagonal GMM 的 EM 構件。

[B20] Hendrycks, D. & Gimpel, K. (2017). A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks. ICLR. [原始來源](https://arxiv.org/pdf/1610.02136v3)

閱讀範圍：v3 十二頁全文核對，含附錄與參考文獻。本站用途：MSP 啟發；LDA／softmax 表格版本及 q95 為本站適配。

[B21] Shannon, C. E. (1948). A Mathematical Theory of Communication. Bell System Technical Journal 27, 379–423 and 623–656. [原始來源](https://www.princeton.edu/~wbialek/rome/refs/shannon_48.pdf)

閱讀範圍：書目與熵公式查閱。本站用途：normalized entropy 構件，不是故障 OOD 保證。

[B22] Liu, W., Wang, X., Owens, J. & Li, Y. (2020). Energy-based Out-of-distribution Detection. NeurIPS 33. [原始來源](https://papers.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html)

閱讀範圍：方法公式查閱；未宣稱全文逐頁閱讀。本站用途：actual LDA affine logits 的有限 score 適配。

[B23] Wang, H., Li, Z., Feng, L. & Zhang, W. (2022). ViM: Out-Of-Distribution with Virtual-logit Matching. CVPR, 4921–4930. [原始來源](https://arxiv.org/abs/2203.10807)

閱讀範圍：方法查閱；未宣稱全文逐頁閱讀。本站用途：LDA W、b／rank20／train alpha 的有限表格適配。

[B24] MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. Fifth Berkeley Symposium 1, 281–297. [原始來源](https://digicoll.lib.berkeley.edu/record/113015?v=pdf)

閱讀範圍：機構目錄核對；全文抓取 403。本站用途：sklearn 批次 KMeans 多中心，非原線上更新逐步重現。

[B25] Angelopoulos, A. N. & Bates, S. (2023). A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification. Foundations and Trends in Machine Learning. [原始來源](https://arxiv.org/html/2107.07511v6)

閱讀範圍：方法與假設查閱；非全文逐頁。本站用途：歷史 B5／B6；跨馬達 exchangeability 未證明。

[B26] Weinberger, K. Q. & Saul, L. K. (2009). Distance Metric Learning for Large Margin Nearest Neighbor Classification. JMLR 10, 207–244. [原始來源](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)

閱讀範圍：§3–4、Eq.10–14、Appendix A；非全文三十八頁。本站用途：非負 diagonal／mean／identity ridge／固定子集的 LMNN-inspired 版本。

[B27] Rennie, J. D. M. & Srebro, N. (2005). Fast Maximum Margin Matrix Factorization for Collaborative Prediction. ICML. DOI 10.1145/1102351.1102441. [原始來源](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf)

閱讀範圍：§3.3、Eq.9 shifted generalized logistic。本站用途：只移用 scalar smooth loss 到 triplet，未實作 MMMF。

[B28] Tseng, C. L., Wang, S. Y., Lin, S. C., Chou, J. H. & Chen, K. F. (2014). A Diagnostic System for Speed-Varying Motor Rotary Faults. Mathematical Problems in Engineering 2014, Article 310626. DOI 10.1155/2014/310626. [原始來源](https://onlinelibrary.wiley.com/doi/10.1155/2014/310626)

閱讀範圍：§2 方法文字；本回合由出版商核對五位作者及 2014-05-19 出版日期。本站用途：幅值可能帶故障訊息的動機，RMS 比值不是原文方法。

[B29] Sugiyama, M. (2007). Dimensionality Reduction of Multimodal Labeled Data by Local Fisher Discriminant Analysis. JMLR 8, 1027–1061. [原始來源](https://www.jmlr.org/papers/volume8/sugiyama07b/sugiyama07b.pdf)

閱讀範圍：§3.1–3.3、Eq.9–12 及 §6；非全文逐頁。本站用途：固定 ridge／子集／正方向秩的 LFDA，配 PCA 控制。

[B30] Sato, A. & Yamada, K. (1995 conference, 1996 volume). Generalized Learning Vector Quantization. NIPS 8, 423–429. [原始來源](https://proceedings.neurips.cc/paper_files/paper/1995/file/9c3b1830513cc3b8fc4b76635d32e692-Paper.pdf)

閱讀範圍：七頁全文、Eq.4–10、公式頁渲染核對。本站用途：固定 sigmoid(4mu)、epsilon、L-BFGS-B／anchor 為本站改編。

[B31] Lange, M., Zühlke, D., Holz, O. & Villmann, T. (2014). Applications of lp-Norms and their Smooth Approximations for Gradient Based Learning Vector Quantization. ESANN, 271–276. [原始來源](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-153.pdf)

閱讀範圍：原六頁與 Eq.11–13 方法核對。本站用途：Q／S、alpha20，本站固定幾何與原型訓練適配。

[B32] Graeber, Vetter, Saralajew, Unterreiner & Schramm (2021). AGLVQ - Making Generalized Learning Vector Quantization Aware of Context. ESANN, 557–562. DOI 10.14428/esann/2021.ES2021-40. [原始來源](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)

閱讀範圍：六頁全文與作者固定程式的相關模組。本站用途：單截距 RPM 多項式／平方距離／固定 aux 的有限適配。

[B33] Fischer, L., Hammer, B. & Wersing, H. (2015). Efficient Rejection Strategies for Prototype-based Classification. Neurocomputing 169, 334–342. DOI 10.1016/j.neucom.2014.10.092. [原始來源](https://www.honda-ri.de/pubs/pdf/2814.pdf)

閱讀範圍：作者稿二十五頁、Eq.7–11；Eq.8 渲染查核。本站用途：distance／1−RelSim／固定 q95 OR，不復現原 threshold grid search。

[B34] Haasdonk, B. & Burkhardt, H. (2007). Invariant Kernel Functions for Pattern Analysis and Machine Learning. Machine Learning 68, 35–61. DOI 10.1007/s10994-007-5009-7. [原始來源](https://lmb.informatik.uni-freiburg.de/papers/download/ha_bu_MachineLearning6807.pdf)

閱讀範圍：作者稿三十二頁全文、Eq.2 與 Proposition 11。本站用途：S3 軸排列群平均、共享 scaler 與 RKHS 拒絕器的本站適配。

[B35] Krueger, D., Caballero, E., Jacobsen, J. H., Zhang, A., Binas, J., Zhang, D., Le Priol, R. & Courville, A. (2021). Out-of-Distribution Generalization via Risk Extrapolation. ICML, PMLR 139, 5815–5826. [原始來源](https://proceedings.mlr.press/v139/krueger21a.html)

閱讀範圍：十二頁本文與十八頁補充全文；相關原作者／DomainBed 程式。本站用途：等 RPM／等類 CE、population variance、線性 softmax、ridge 的本站適配。

[B36] Huang, Z., Wang, H., Xing, E. P. & Huang, D. (2020). Self-Challenging Improves Cross-Domain Generalization. ECCV. [原始來源](https://publications.ri.cmu.edu/self-challenging-improves-cross-domain-generalization)

閱讀範圍：arXiv v1 二十頁全文；ECCV 版部分讀取；固定作者程式相關檔案。本站用途：手工特徵、四遮蔽控制、固定 200 steps；無 CNN／Adam／curriculum。

[B37] Sagawa, S., Koh, P. W., Hashimoto, T. B. & Liang, P. (2020). Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization. ICLR. [原始來源](https://arxiv.org/pdf/1911.08731)

閱讀範圍：v2 十九頁全文及固定作者程式相關檔案。本站用途：已規劃未實作，本階段收尾，未進入訓練或測試。

[B38] Gulrajani, I. & Lopez-Paz, D. (2021). In Search of Lost Domain Generalization. ICLR. [原始來源](https://arxiv.org/abs/2007.01434)

閱讀範圍：先前 §3–5；後續只重核摘要與 metadata，非全文逐頁。本站用途：一致模型選擇流程的限制提醒，不移植外部排名。

[B39] Vaze, S., Han, K., Vedaldi, A. & Zisserman, A. (2022). Open-Set Recognition: A Good Closed-Set Classifier Is All You Need? ICLR. [原始來源](https://robots.ox.ac.uk/~vgg/publications/2022/Vaze22/)

閱讀範圍：作者頁與摘要；全文連結取得受限。本站用途：D01 解耦的研究動機，不是本站效果保證。

[B40] Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022). Why do tree-based models still outperform deep learning on typical tabular data? NeurIPS Datasets and Benchmarks. [原始來源](https://proceedings.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html)

閱讀範圍：摘要與設定概述，非全文。本站用途：樹模型比較動機，非跨馬達可靠性證據。

## 附錄一 全方法主數值與配置

下表不作最佳方法排序。方法按 sealed registry ID，保留對照與 INCOMPLETE。主表數值採 motor-macro seed0；全部 seeds、完整 final 分母、每 motor／RPM／class、來源與參數都留在附帶機器索引。部分早期分數的 healthy_safety.false_positive_rate 僅記 unknown alarm，不能冒稱完整健康誤報；早期方法該欄標 NA，完整值沿 metric_definition_v2 重算報告。

### 文獻 C 30 分類配置與分數支線

程式入口 experiments/fault_type_literature_study.py；參數及 sources 沿 C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_literature_report\2026-10-02-12-26-09\summary.json.gz 與 catalog[literature_expansion].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|C01/knn|classifier=lda；parameter=None；representation=base75；rpm_strategy=mixed|
|C01/mahalanobis|classifier=lda；parameter=None；representation=base75；rpm_strategy=mixed|
|C02/knn|classifier=linear；parameter=None；representation=base75；rpm_strategy=mixed|
|C02/mahalanobis|classifier=linear；parameter=None；representation=base75；rpm_strategy=mixed|
|C03/knn|classifier=extra；parameter=None；representation=base75；rpm_strategy=mixed|
|C03/mahalanobis|classifier=extra；parameter=None；representation=base75；rpm_strategy=mixed|
|C04/knn|classifier=forest；parameter=None；representation=base75；rpm_strategy=mixed|
|C04/mahalanobis|classifier=forest；parameter=None；representation=base75；rpm_strategy=mixed|
|C05/knn|classifier=boost；parameter=None；representation=base75；rpm_strategy=mixed|
|C05/mahalanobis|classifier=boost；parameter=None；representation=base75；rpm_strategy=mixed|
|C06/knn|classifier=svm；parameter=None；representation=base75；rpm_strategy=mixed|
|C06/mahalanobis|classifier=svm；parameter=None；representation=base75；rpm_strategy=mixed|
|C07/knn|classifier=knn；parameter=5；representation=base75；rpm_strategy=mixed|
|C07/mahalanobis|classifier=knn；parameter=5；representation=base75；rpm_strategy=mixed|
|C08/knn|classifier=knn；parameter=15；representation=base75；rpm_strategy=mixed|
|C08/mahalanobis|classifier=knn；parameter=15；representation=base75；rpm_strategy=mixed|
|C09/knn|classifier=nb；parameter=None；representation=base75；rpm_strategy=mixed|
|C09/mahalanobis|classifier=nb；parameter=None；representation=base75；rpm_strategy=mixed|
|C10/knn|classifier=rda；parameter=[0.5, 0.1]；representation=base75；rpm_strategy=mixed|
|C10/mahalanobis|classifier=rda；parameter=[0.5, 0.1]；representation=base75；rpm_strategy=mixed|
|C11/knn|classifier=rda；parameter=[0.5, 0.5]；representation=base75；rpm_strategy=mixed|
|C11/mahalanobis|classifier=rda；parameter=[0.5, 0.5]；representation=base75；rpm_strategy=mixed|
|C12/knn|classifier=rda；parameter=[0.0, 0.1]；representation=base75；rpm_strategy=mixed|
|C12/mahalanobis|classifier=rda；parameter=[0.0, 0.1]；representation=base75；rpm_strategy=mixed|
|C13/knn|classifier=lda；parameter=0.1；representation=base75；rpm_strategy=mixed|
|C13/mahalanobis|classifier=lda；parameter=0.1；representation=base75；rpm_strategy=mixed|
|C14/knn|classifier=lda；parameter=0.5；representation=base75；rpm_strategy=mixed|
|C14/mahalanobis|classifier=lda；parameter=0.5；representation=base75；rpm_strategy=mixed|
|C15/knn|classifier=lda；parameter=0.9；representation=base75；rpm_strategy=mixed|
|C15/mahalanobis|classifier=lda；parameter=0.9；representation=base75；rpm_strategy=mixed|
|C16/knn|classifier=lda；parameter=None；representation=signed66；rpm_strategy=mixed|
|C16/mahalanobis|classifier=lda；parameter=None；representation=signed66；rpm_strategy=mixed|
|C17/knn|classifier=lda；parameter=None；representation=harmonic69；rpm_strategy=mixed|
|C17/mahalanobis|classifier=lda；parameter=None；representation=harmonic69；rpm_strategy=mixed|
|C18/knn|classifier=lda；parameter=None；representation=harmonic66；rpm_strategy=mixed|
|C18/mahalanobis|classifier=lda；parameter=None；representation=harmonic66；rpm_strategy=mixed|
|C19/knn|classifier=lda；parameter=None；representation=pca20；rpm_strategy=mixed|
|C19/mahalanobis|classifier=lda；parameter=None；representation=pca20；rpm_strategy=mixed|
|C20/knn|classifier=knn；parameter=5；representation=nca10；rpm_strategy=mixed|
|C20/mahalanobis|classifier=knn；parameter=5；representation=nca10；rpm_strategy=mixed|
|C21/knn|classifier=forest；parameter=None；representation=harmonic69；rpm_strategy=mixed|
|C21/mahalanobis|classifier=forest；parameter=None；representation=harmonic69；rpm_strategy=mixed|
|C22/knn|classifier=svm；parameter=None；representation=harmonic69；rpm_strategy=mixed|
|C22/mahalanobis|classifier=svm；parameter=None；representation=harmonic69；rpm_strategy=mixed|
|C23/knn|classifier=rda；parameter=[1.0, 0.1]；representation=base75；rpm_strategy=mixed|
|C23/mahalanobis|classifier=rda；parameter=[1.0, 0.1]；representation=base75；rpm_strategy=mixed|
|C24/knn|classifier=lda；parameter=None；representation=base75；rpm_strategy=separate|
|C24/mahalanobis|classifier=lda；parameter=None；representation=base75；rpm_strategy=separate|
|R01/R01|kind=pooled；parent_arm=C01|
|R02/R02|kind=relative；parameter=1.0；parent_arm=C01|
|R03/R03|kind=relative；parameter=0.5；parent_arm=C01|
|R04/R04|kind=relative；parameter=2.0；parent_arm=C01|
|R05/R05|kind=oas；parent_arm=C01|
|R06/R06|kind=diagonal；parent_arm=C01|
|R07/R07|kind=knn_factory；parameter=1；parent_arm=C01|
|R08/R08|kind=knn_factory；parameter=15；parent_arm=C01|
|R09/R09|kind=iforest；parent_arm=C01|
|R10/R10|kind=lof；parent_arm=C01|
|R11/R11|kind=ocsvm；parent_arm=C01|
|R12/R12|kind=gmm；parent_arm=C01|
|R13/R13|kind=centers；parent_arm=C01|
|R14/R14|kind=msp；parent_arm=C01|
|R15/R15|kind=entropy；parent_arm=C01|
|R16/R16|kind=margin；parent_arm=C01|
|R17/R17|kind=predicted；parent_arm=C01|
|R18/R18|kind=relative；parameter=1.0；parent_arm=C17|
|R19/R19|kind=energy；parent_arm=C01|
|R20/R20|kind=vim；parent_arm=C01|
|R21/R21|kind=fusion；parameter=0.25；parent_arm=C01|
|R22/R22|kind=fusion；parameter=0.75；parent_arm=C01|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|C01/knn|22.98|16.25|0.1425|NA|5.45|
|C01/mahalanobis|22.98|16.25|0.1425|NA|18.44|
|C02/knn|34.15|26.61|0.2404|NA|5.45|
|C02/mahalanobis|34.15|26.61|0.2404|NA|18.44|
|C03/knn|33.95|23.86|0.2041|NA|5.45|
|C03/mahalanobis|33.95|23.86|0.2041|NA|18.44|
|C04/knn|33.66|26.99|0.2181|NA|5.45|
|C04/mahalanobis|33.66|26.99|0.2181|NA|18.44|
|C05/knn|33.74|26.81|0.2019|NA|5.45|
|C05/mahalanobis|33.74|26.81|0.2019|NA|18.44|
|C06/knn|23.21|16.33|0.1819|NA|5.45|
|C06/mahalanobis|23.21|16.33|0.1819|NA|18.44|
|C07/knn|31.45|23.82|0.2472|NA|5.45|
|C07/mahalanobis|31.45|23.82|0.2472|NA|18.44|
|C08/knn|30.41|22.32|0.2288|NA|5.45|
|C08/mahalanobis|30.41|22.32|0.2288|NA|18.44|
|C09/knn|30.37|25.60|0.2002|NA|5.45|
|C09/mahalanobis|30.37|25.60|0.2002|NA|18.44|
|C10/knn|30.55|23.23|0.1779|NA|5.45|
|C10/mahalanobis|30.55|23.23|0.1779|NA|18.44|
|C11/knn|32.83|26.12|0.2292|NA|5.45|
|C11/mahalanobis|32.83|26.12|0.2292|NA|18.44|
|C12/knn|27.47|20.94|0.1590|NA|5.45|
|C12/mahalanobis|27.47|20.94|0.1590|NA|18.44|
|C13/knn|25.87|15.74|0.1379|NA|5.45|
|C13/mahalanobis|25.87|15.74|0.1379|NA|18.44|
|C14/knn|30.08|23.98|0.2257|NA|5.45|
|C14/mahalanobis|30.08|23.98|0.2257|NA|18.44|
|C15/knn|29.71|27.69|0.2456|NA|5.45|
|C15/mahalanobis|29.71|27.69|0.2456|NA|18.44|
|C16/knn|29.19|19.86|0.1783|NA|5.47|
|C16/mahalanobis|29.19|19.86|0.1783|NA|4.60|
|C17/knn|39.29|30.43|0.2852|NA|7.48|
|C17/mahalanobis|39.29|30.43|0.2852|NA|8.44|
|C18/knn|33.83|25.83|0.2230|NA|7.46|
|C18/mahalanobis|33.83|25.83|0.2230|NA|8.18|
|C19/knn|26.24|17.17|0.1599|NA|3.40|
|C19/mahalanobis|26.24|17.17|0.1599|NA|12.29|
|C20/knn|30.62|21.65|0.2051|NA|3.94|
|C20/mahalanobis|30.62|21.65|0.2051|NA|9.35|
|C21/knn|34.68|24.21|0.1889|NA|7.48|
|C21/mahalanobis|34.68|24.21|0.1889|NA|8.44|
|C22/knn|24.87|16.72|0.1373|NA|7.48|
|C22/mahalanobis|24.87|16.72|0.1373|NA|8.44|
|C23/knn|25.68|15.66|0.1375|NA|5.45|
|C23/mahalanobis|25.68|15.66|0.1375|NA|18.44|
|C24/knn|32.17|30.91|0.2866|NA|16.90|
|C24/mahalanobis|32.17|30.91|0.2866|NA|21.07|
|R01/R01|22.98|16.25|0.1425|NA|11.47|
|R02/R02|22.98|16.25|0.1425|NA|14.51|
|R03/R03|22.98|16.25|0.1425|NA|13.37|
|R04/R04|22.98|16.25|0.1425|NA|8.80|
|R05/R05|22.98|16.25|0.1425|NA|12.93|
|R06/R06|22.98|16.25|0.1425|NA|11.44|
|R07/R07|22.98|16.25|0.1425|NA|4.78|
|R08/R08|22.98|16.25|0.1425|NA|6.01|
|R09/R09|22.98|16.25|0.1425|NA|14.66|
|R10/R10|22.98|16.25|0.1425|NA|10.63|
|R11/R11|22.98|16.25|0.1425|NA|5.86|
|R12/R12|22.98|16.25|0.1425|NA|7.06|
|R13/R13|22.98|16.25|0.1425|NA|11.47|
|R14/R14|22.98|16.25|0.1425|NA|4.49|
|R15/R15|22.98|16.25|0.1425|NA|4.49|
|R16/R16|22.98|16.25|0.1425|NA|4.48|
|R17/R17|NA|NA|NA|NA|NA|
|R18/R18|39.29|30.43|0.2852|NA|22.68|
|R19/R19|22.98|16.25|0.1425|NA|1.95|
|R20/R20|22.98|16.25|0.1425|NA|7.92|
|R21/R21|22.98|16.25|0.1425|NA|4.49|
|R22/R22|22.98|16.25|0.1425|NA|4.49|

### 機制 D/P 解耦、RMD 係數與分塊

程式入口 experiments/fault_type_mechanism_study.py；參數及 sources 沿 C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_mechanism_report\2026-10-02-17-58-59\summary.json.gz 與 catalog[mechanism_research_v2].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|D01|classifier=C17；detector=C02/M；kind=decoupled|
|D02|classifier=C17；detector=C02/K；kind=decoupled|
|D03|classifier=C24；detector=C02/M；kind=decoupled|
|G01|background_weight=0.0；classifier=C17；detector=block geometry；kind=block|
|G02|background_weight=1.0；classifier=C17；detector=block geometry；kind=block|
|G03|background_weight=0.0；classifier=block nearest；detector=block geometry；kind=block|
|P01|beta=0.0；classifier=RPMPartialPooling；detector=C02/M；kind=partial_pool|
|P02|beta=0.5；classifier=RPMPartialPooling；detector=C02/M；kind=partial_pool|
|P03|beta=1.0；classifier=RPMPartialPooling；detector=C02/M；kind=partial_pool|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|D01|39.29|30.43|0.2852|14.13|18.44|
|D02|39.29|30.43|0.2852|14.76|5.45|
|D03|32.17|30.91|0.2866|61.40|18.44|
|G01|39.29|30.43|0.2852|20.10|3.50|
|G02|39.29|30.43|0.2852|30.83|8.15|
|G03|33.71|26.98|0.2472|36.50|3.50|
|P01|32.51|29.71|0.2547|52.48|18.44|
|P02|25.99|18.94|0.1860|37.01|18.44|
|P03|23.85|17.01|0.1500|40.35|18.44|

### Q gain、形狀與對角度量

程式入口 experiments/fault_type_continuous_study.py；參數及 sources 沿 output\fault_type_continuous_report_v2\2026-10-02-23-30-52\summary.json.gz 與 catalog[continuous_research].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|Q01|detector=C02/M；kind=neighbors；metric=False；subset_classifier=True|
|Q03|detector=C02/M；kind=neighbors；metric=False；subset_classifier=False|
|Q05|detector=self/M；dimension=63；kind=gain|
|Q06|detector=self/M；dimension=66；kind=gain|
|Q07|detector=self/M；dimension=69；kind=gain|
|Q08|detector=C02/M；dimension=66；kind=gain|
|Q02|INCOMPLETE；沒有完整 summary，保留 registry 定義：{'detector': 'C02/M', 'id': 'Q02', 'kind': 'neighbors', 'metric': True, 'subset_classifier': True}|
|Q04|INCOMPLETE；沒有完整 summary，保留 registry 定義：{'detector': 'C02/M', 'id': 'Q04', 'kind': 'neighbors', 'metric': True, 'subset_classifier': False}|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|Q01|36.75|28.48|0.2631|19.72|18.44|
|Q03|36.76|28.46|0.2525|19.65|18.44|
|Q05|36.01|32.80|0.2826|46.27|7.57|
|Q06|35.05|30.99|0.2828|43.53|7.92|
|Q07|39.82|33.92|0.3041|29.14|8.71|
|Q08|35.05|30.99|0.2828|43.46|18.44|
|Q02|NA|NA|NA|NA|NA|
|Q04|NA|NA|NA|NA|NA|

### E 度量分類、鄰居 energy、一／三中心

程式入口 experiments/fault_type_metric_classification.py；參數及 sources 沿 output\fault_type_metric_classification_report\2026-10-03-10-12-38\summary.json.gz 與 catalog[metric_classification_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|E01|classifier=identity_subset；detector=C02/M|
|E02|classifier=metric_subset；detector=C02/M|
|E03|classifier=identity_all；detector=C02/M|
|E04|classifier=metric_all；detector=C02/M|
|E05|classifier=identity_mean；detector=C02/M|
|E06|classifier=metric_mean；detector=C02/M|
|E07|classifier=metric_multi；detector=C02/M|
|E08|classifier=metric_energy；detector=C02/M|
|E09|classifier=identity_all；detector=identity/mahalanobis|
|E10|classifier=metric_all；detector=metric/mahalanobis|
|E11|classifier=identity_all；detector=identity/knn|
|E12|classifier=metric_all；detector=metric/knn|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|E01|36.75|28.48|0.2631|19.72|18.44|
|E02|33.63|24.97|0.2024|21.49|18.44|
|E03|36.76|28.46|0.2525|19.65|18.44|
|E04|33.50|24.81|0.1931|21.54|18.44|
|E05|34.60|30.37|0.2606|42.64|18.44|
|E06|34.74|25.50|0.1904|17.27|18.44|
|E07|34.83|26.66|0.2168|22.77|18.44|
|E08|31.11|26.03|0.2357|42.55|18.44|
|E09|36.76|28.46|0.2525|19.65|8.44|
|E10|33.50|24.81|0.1931|21.54|5.65|
|E11|36.76|28.46|0.2525|28.90|7.48|
|E12|33.50|24.81|0.1931|21.54|7.90|

### F PCA／LFDA10／20

程式入口 experiments/fault_type_local_fisher.py；參數及 sources 沿 output\fault_type_local_fisher_report\2026-10-03-15-09-03\summary.json.gz 與 catalog[local_fisher_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|F01|classifier=lda；detector=C02/M；representation=pca10|
|F02|classifier=knn；detector=C02/M；representation=pca10|
|F03|classifier=knn；detector=mahalanobis；representation=pca10|
|F04|classifier=knn；detector=knn；representation=pca10|
|F05|classifier=lda；detector=C02/M；representation=pca20|
|F06|classifier=knn；detector=C02/M；representation=pca20|
|F07|classifier=knn；detector=mahalanobis；representation=pca20|
|F08|classifier=knn；detector=knn；representation=pca20|
|F09|classifier=lda；detector=C02/M；representation=lfda10|
|F10|classifier=knn；detector=C02/M；representation=lfda10|
|F11|classifier=knn；detector=mahalanobis；representation=lfda10|
|F12|classifier=knn；detector=knn；representation=lfda10|
|F13|classifier=lda；detector=C02/M；representation=lfda20|
|F14|classifier=knn；detector=C02/M；representation=lfda20|
|F15|classifier=knn；detector=mahalanobis；representation=lfda20|
|F16|classifier=knn；detector=knn；representation=lfda20|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|F01|34.34|28.44|0.2184|34.27|18.44|
|F02|41.01|33.42|0.2985|18.95|18.44|
|F03|41.01|33.42|0.2985|18.95|6.24|
|F04|41.01|33.42|0.2985|29.46|3.92|
|F05|33.31|26.45|0.2452|30.29|18.44|
|F06|37.13|28.91|0.2559|19.69|18.44|
|F07|37.13|28.91|0.2559|19.69|6.04|
|F08|37.13|28.91|0.2559|24.87|6.15|
|F09|31.50|23.04|0.1568|24.76|18.44|
|F10|35.71|28.29|0.2215|26.09|18.44|
|F11|35.71|28.29|0.2215|26.09|7.15|
|F12|35.71|28.29|0.2215|26.09|6.07|
|F13|32.63|23.85|0.2081|21.43|18.44|
|F14|35.75|28.23|0.2208|25.57|18.44|
|F15|35.75|28.23|0.2208|25.57|6.56|
|F16|35.75|28.23|0.2208|25.57|6.06|

### G 固定／GLVQ／anchor，一／三中心

程式入口 experiments/fault_type_discriminative_prototypes.py；參數及 sources 沿 output\fault_type_discriminative_prototypes_report\2026-10-03-15-39-29\summary.json.gz 與 catalog[discriminative_prototypes_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|G01|detector=C02/M；model=identity_1_static|
|G02|detector=ambiguity；model=identity_1_static|
|G03|detector=C02/M；model=identity_1_glvq|
|G04|detector=ambiguity；model=identity_1_glvq|
|G05|detector=C02/M；model=identity_1_anchored|
|G06|detector=ambiguity；model=identity_1_anchored|
|G07|detector=C02/M；model=identity_3_static|
|G08|detector=ambiguity；model=identity_3_static|
|G09|detector=C02/M；model=identity_3_glvq|
|G10|detector=ambiguity；model=identity_3_glvq|
|G11|detector=C02/M；model=identity_3_anchored|
|G12|detector=ambiguity；model=identity_3_anchored|
|G13|detector=C02/M；model=metric_1_static|
|G14|detector=ambiguity；model=metric_1_static|
|G15|detector=C02/M；model=metric_1_glvq|
|G16|detector=ambiguity；model=metric_1_glvq|
|G17|detector=C02/M；model=metric_1_anchored|
|G18|detector=ambiguity；model=metric_1_anchored|
|G19|detector=C02/M；model=metric_3_static|
|G20|detector=ambiguity；model=metric_3_static|
|G21|detector=C02/M；model=metric_3_glvq|
|G22|detector=ambiguity；model=metric_3_glvq|
|G23|detector=C02/M；model=metric_3_anchored|
|G24|detector=ambiguity；model=metric_3_anchored|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|G01|34.60|30.37|0.2606|42.64|18.44|
|G02|34.60|30.37|0.2606|45.17|8.80|
|G03|33.79|27.49|0.2330|32.82|18.44|
|G04|33.79|27.49|0.2330|33.87|4.03|
|G05|33.83|27.56|0.2345|32.86|18.44|
|G06|33.83|27.56|0.2345|33.87|3.78|
|G07|35.29|26.66|0.2551|19.29|18.44|
|G08|35.29|26.66|0.2551|19.54|6.51|
|G09|36.53|28.06|0.2696|18.84|18.44|
|G10|36.53|28.06|0.2696|19.05|6.38|
|G11|36.52|28.04|0.2694|18.84|18.44|
|G12|36.52|28.04|0.2694|19.09|6.30|
|G13|34.74|25.50|0.1904|17.27|18.44|
|G14|34.74|25.50|0.1904|18.17|14.17|
|G15|37.03|26.64|0.2071|8.92|18.44|
|G16|37.03|26.64|0.2071|8.92|20.22|
|G17|37.06|26.67|0.2074|8.92|18.44|
|G18|37.06|26.67|0.2074|8.92|20.36|
|G19|34.83|26.66|0.2168|22.77|18.44|
|G20|34.83|26.66|0.2168|23.69|9.15|
|G21|33.54|24.86|0.2057|21.52|18.44|
|G22|33.54|24.86|0.2057|23.51|11.15|
|G23|33.54|24.86|0.2057|21.52|18.44|
|G24|33.54|24.86|0.2057|23.51|11.16|

### H smooth-L1 Q／S 幾何

程式入口 experiments/fault_type_smooth_l1.py；參數及 sources 沿 output\fault_type_smooth_l1_report\2026-10-03-20-23-56\summary.json.gz 與 catalog[smooth_l1_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|H01|detector=C02/M；model=identity_quasi_static|
|H02|detector=C02/M；model=identity_quasi_glvq|
|H03|detector=C02/M；model=identity_quasi_anchored|
|H04|detector=C02/M；model=identity_soft_static|
|H05|detector=C02/M；model=identity_soft_glvq|
|H06|detector=C02/M；model=identity_soft_anchored|
|H07|detector=C02/M；model=metric_quasi_static|
|H08|detector=C02/M；model=metric_quasi_glvq|
|H09|detector=C02/M；model=metric_quasi_anchored|
|H10|detector=C02/M；model=metric_soft_static|
|H11|detector=C02/M；model=metric_soft_glvq|
|H12|detector=C02/M；model=metric_soft_anchored|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|H01|34.28|29.91|0.2671|42.53|18.44|
|H02|35.99|27.03|0.2323|16.96|18.44|
|H03|37.42|28.85|0.2472|17.60|18.44|
|H04|33.93|29.50|0.2619|42.60|18.44|
|H05|36.50|27.84|0.2431|18.02|18.44|
|H06|36.50|27.95|0.2432|18.65|18.44|
|H07|37.49|31.22|0.2463|30.23|18.44|
|H08|36.67|26.21|0.2190|8.92|18.44|
|H09|38.10|27.93|0.2411|8.92|18.44|
|H10|35.67|29.26|0.2393|31.43|18.44|
|H11|35.33|24.97|0.2169|10.84|18.44|
|H12|35.16|24.76|0.2157|10.77|18.44|

### I RPM degree1／2，static／GLVQ／aux

程式入口 experiments/fault_type_context_prototypes.py；參數及 sources 沿 output\fault_type_context_prototypes_report\2026-10-03-20-44-37\summary.json.gz 與 catalog[context_prototypes_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|I01|detector=C02/M；model=identity_1_static|
|I02|detector=C02/M；model=identity_1_glvq|
|I03|detector=C02/M；model=identity_1_auxiliary|
|I04|detector=C02/M；model=identity_2_static|
|I05|detector=C02/M；model=identity_2_glvq|
|I06|detector=C02/M；model=identity_2_auxiliary|
|I07|detector=C02/M；model=metric_1_static|
|I08|detector=C02/M；model=metric_1_glvq|
|I09|detector=C02/M；model=metric_1_auxiliary|
|I10|detector=C02/M；model=metric_2_static|
|I11|detector=C02/M；model=metric_2_glvq|
|I12|detector=C02/M；model=metric_2_auxiliary|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|I01|29.34|28.21|0.2640|63.85|18.44|
|I02|25.96|21.39|0.1950|49.08|18.44|
|I03|25.68|21.33|0.1938|50.52|18.44|
|I04|26.31|24.97|0.2344|66.07|18.44|
|I05|27.13|25.86|0.2282|65.57|18.44|
|I06|27.16|25.90|0.2286|65.61|18.44|
|I07|35.69|28.87|0.2322|28.95|18.44|
|I08|36.01|27.40|0.2614|19.51|18.44|
|I09|36.01|27.40|0.2615|19.51|18.44|
|I10|37.12|30.00|0.2739|25.84|18.44|
|I11|38.90|31.21|0.2872|21.31|18.44|
|I12|38.89|31.21|0.2871|21.38|18.44|

### J distance／ambiguity／OR 拒絕

程式入口 experiments/fault_type_context_rejection.py；參數及 sources 沿 output\fault_type_context_rejection_report\2026-10-04-16-29-39\summary.json.gz 與 catalog[context_rejection_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|J01|detector=distance；model=identity_1_static_distance；parent_arm=I01|
|J02|detector=ambiguity；model=identity_1_static_ambiguity；parent_arm=I01|
|J03|detector=or；model=identity_1_static_or；parent_arm=I01|
|J04|detector=distance；model=identity_1_glvq_distance；parent_arm=I02|
|J05|detector=ambiguity；model=identity_1_glvq_ambiguity；parent_arm=I02|
|J06|detector=or；model=identity_1_glvq_or；parent_arm=I02|
|J07|detector=distance；model=identity_1_auxiliary_distance；parent_arm=I03|
|J08|detector=ambiguity；model=identity_1_auxiliary_ambiguity；parent_arm=I03|
|J09|detector=or；model=identity_1_auxiliary_or；parent_arm=I03|
|J10|detector=distance；model=identity_2_static_distance；parent_arm=I04|
|J11|detector=ambiguity；model=identity_2_static_ambiguity；parent_arm=I04|
|J12|detector=or；model=identity_2_static_or；parent_arm=I04|
|J13|detector=distance；model=identity_2_glvq_distance；parent_arm=I05|
|J14|detector=ambiguity；model=identity_2_glvq_ambiguity；parent_arm=I05|
|J15|detector=or；model=identity_2_glvq_or；parent_arm=I05|
|J16|detector=distance；model=identity_2_auxiliary_distance；parent_arm=I06|
|J17|detector=ambiguity；model=identity_2_auxiliary_ambiguity；parent_arm=I06|
|J18|detector=or；model=identity_2_auxiliary_or；parent_arm=I06|
|J19|detector=distance；model=metric_1_static_distance；parent_arm=I07|
|J20|detector=ambiguity；model=metric_1_static_ambiguity；parent_arm=I07|
|J21|detector=or；model=metric_1_static_or；parent_arm=I07|
|J22|detector=distance；model=metric_1_glvq_distance；parent_arm=I08|
|J23|detector=ambiguity；model=metric_1_glvq_ambiguity；parent_arm=I08|
|J24|detector=or；model=metric_1_glvq_or；parent_arm=I08|
|J25|detector=distance；model=metric_1_auxiliary_distance；parent_arm=I09|
|J26|detector=ambiguity；model=metric_1_auxiliary_ambiguity；parent_arm=I09|
|J27|detector=or；model=metric_1_auxiliary_or；parent_arm=I09|
|J28|detector=distance；model=metric_2_static_distance；parent_arm=I10|
|J29|detector=ambiguity；model=metric_2_static_ambiguity；parent_arm=I10|
|J30|detector=or；model=metric_2_static_or；parent_arm=I10|
|J31|detector=distance；model=metric_2_glvq_distance；parent_arm=I11|
|J32|detector=ambiguity；model=metric_2_glvq_ambiguity；parent_arm=I11|
|J33|detector=or；model=metric_2_glvq_or；parent_arm=I11|
|J34|detector=distance；model=metric_2_auxiliary_distance；parent_arm=I12|
|J35|detector=ambiguity；model=metric_2_auxiliary_ambiguity；parent_arm=I12|
|J36|detector=or；model=metric_2_auxiliary_or；parent_arm=I12|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|J01|29.34|28.21|0.2640|67.34|6.76|
|J02|29.34|28.21|0.2640|64.76|20.62|
|J03|29.34|28.21|0.2640|68.25|24.60|
|J04|25.96|21.39|0.1950|53.34|7.03|
|J05|25.96|21.39|0.1950|50.20|13.25|
|J06|25.96|21.39|0.1950|53.93|19.62|
|J07|25.68|21.33|0.1938|54.29|6.91|
|J08|25.68|21.33|0.1938|51.43|12.96|
|J09|25.68|21.33|0.1938|54.85|19.22|
|J10|26.31|24.97|0.2344|66.28|3.10|
|J11|26.31|24.97|0.2344|66.17|4.83|
|J12|26.31|24.97|0.2344|66.38|7.90|
|J13|27.13|25.86|0.2282|65.82|3.09|
|J14|27.13|25.86|0.2282|65.78|6.06|
|J15|27.13|25.86|0.2282|66.03|9.14|
|J16|27.16|25.90|0.2286|65.85|3.07|
|J17|27.16|25.90|0.2286|65.75|6.08|
|J18|27.16|25.90|0.2286|65.99|9.14|
|J19|35.69|28.87|0.2322|29.58|10.73|
|J20|35.69|28.87|0.2322|32.73|11.03|
|J21|35.69|28.87|0.2322|33.01|18.97|
|J22|36.01|27.40|0.2614|20.04|11.74|
|J23|36.01|27.40|0.2614|20.82|6.99|
|J24|36.01|27.40|0.2614|21.14|15.49|
|J25|36.01|27.40|0.2615|20.01|11.74|
|J26|36.01|27.40|0.2615|20.82|6.97|
|J27|36.01|27.40|0.2615|21.14|15.48|
|J28|37.12|30.00|0.2739|25.84|8.78|
|J29|37.12|30.00|0.2739|29.61|5.63|
|J30|37.12|30.00|0.2739|29.61|14.41|
|J31|38.90|31.21|0.2872|21.39|8.78|
|J32|38.90|31.21|0.2872|23.26|9.10|
|J33|38.90|31.21|0.2872|23.26|14.80|
|J34|38.89|31.21|0.2871|21.45|8.78|
|J35|38.89|31.21|0.2871|23.29|9.10|
|J36|38.89|31.21|0.2871|23.29|14.80|

### K S3 核 alpha=0/.5/1

程式入口 experiments/fault_type_axis_kernel.py；參數及 sources 沿 output\fault_type_axis_kernel_report\2026-10-04-21-32-27\summary.json.gz 與 catalog[axis_invariant_kernel_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|K01|detector=C02/M；model=alpha0|
|K02|detector=C02/kNN；model=alpha0|
|K03|detector=centroid；model=alpha0|
|K04|detector=C02/M；model=alpha1|
|K05|detector=C02/kNN；model=alpha1|
|K06|detector=centroid；model=alpha1|
|K07|detector=C02/M；model=alpha2|
|K08|detector=C02/kNN；model=alpha2|
|K09|detector=centroid；model=alpha2|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|K01|27.31|22.14|0.1740|45.98|18.44|
|K02|27.31|22.14|0.1740|45.98|5.45|
|K03|27.31|22.14|0.1740|45.98|13.01|
|K04|27.79|23.04|0.1862|47.65|18.44|
|K05|27.79|23.04|0.1862|47.65|5.45|
|K06|27.79|23.04|0.1862|48.88|14.09|
|K07|28.47|24.39|0.1999|50.49|18.44|
|K08|28.47|24.39|0.1999|50.49|5.45|
|K09|28.47|24.39|0.1999|69.62|22.69|

### L REx beta=0/1/10

程式入口 experiments/fault_type_risk_extrapolation.py；參數及 sources 沿 output\fault_type_risk_extrapolation_report\2026-10-04-21-40-24\summary.json.gz 與 catalog[rpm_risk_extrapolation_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|L01|detector=C02/M；model=base75_beta0|
|L02|detector=C02/kNN；model=base75_beta0|
|L03|detector=MSP；model=base75_beta0|
|L04|detector=C02/M；model=base75_beta1|
|L05|detector=C02/kNN；model=base75_beta1|
|L06|detector=MSP；model=base75_beta1|
|L07|detector=C02/M；model=base75_beta2|
|L08|detector=C02/kNN；model=base75_beta2|
|L09|detector=MSP；model=base75_beta2|
|L10|detector=C02/M；model=harmonic69_beta0|
|L11|detector=C02/kNN；model=harmonic69_beta0|
|L12|detector=MSP；model=harmonic69_beta0|
|L13|detector=C02/M；model=harmonic69_beta1|
|L14|detector=C02/kNN；model=harmonic69_beta1|
|L15|detector=MSP；model=harmonic69_beta1|
|L16|detector=C02/M；model=harmonic69_beta2|
|L17|detector=C02/kNN；model=harmonic69_beta2|
|L18|detector=MSP；model=harmonic69_beta2|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|L01|31.43|26.00|0.2406|40.91|18.44|
|L02|31.43|26.00|0.2406|40.99|5.45|
|L03|31.43|26.00|0.2406|44.74|4.60|
|L04|31.37|25.95|0.2404|41.03|18.44|
|L05|31.37|25.95|0.2404|41.06|5.45|
|L06|31.37|25.95|0.2404|44.85|4.60|
|L07|31.03|25.67|0.2393|41.64|18.44|
|L08|31.03|25.67|0.2393|41.68|5.45|
|L09|31.03|25.67|0.2393|45.29|4.72|
|L10|37.29|31.25|0.2666|30.46|18.44|
|L11|37.29|31.25|0.2666|30.46|5.45|
|L12|37.29|31.25|0.2666|30.67|5.30|
|L13|37.32|31.28|0.2668|30.46|18.44|
|L14|37.32|31.28|0.2668|30.46|5.45|
|L15|37.32|31.28|0.2668|30.71|5.27|
|L16|37.32|31.28|0.2668|30.46|18.44|
|L17|37.32|31.28|0.2668|30.46|5.45|
|L18|37.32|31.28|0.2668|30.78|5.03|

### M 兩表示與四遮蔽控制

程式入口 experiments/fault_type_self_challenging.py；參數及 sources 沿 output\fault_type_self_challenging_report\2026-10-05-22-17-39\summary.json.gz 與 catalog[feature_self_challenging_v1].protocol。訓練／校準／測試 motor 按正文三折固定。沒有 global winner。

|方法 ID|固定配置|
|---|---|
|M01|detector=C02/M；model=base75_unmasked|
|M02|detector=C02/kNN；model=base75_unmasked|
|M03|detector=MSP；model=base75_unmasked|
|M04|detector=C02/M；model=base75_random|
|M05|detector=C02/kNN；model=base75_random|
|M06|detector=MSP；model=base75_random|
|M07|detector=C02/M；model=base75_signed_gradient|
|M08|detector=C02/kNN；model=base75_signed_gradient|
|M09|detector=MSP；model=base75_signed_gradient|
|M10|detector=C02/M；model=base75_contribution|
|M11|detector=C02/kNN；model=base75_contribution|
|M12|detector=MSP；model=base75_contribution|
|M13|detector=C02/M；model=harmonic69_unmasked|
|M14|detector=C02/kNN；model=harmonic69_unmasked|
|M15|detector=MSP；model=harmonic69_unmasked|
|M16|detector=C02/M；model=harmonic69_random|
|M17|detector=C02/kNN；model=harmonic69_random|
|M18|detector=MSP；model=harmonic69_random|
|M19|detector=C02/M；model=harmonic69_signed_gradient|
|M20|detector=C02/kNN；model=harmonic69_signed_gradient|
|M21|detector=MSP；model=harmonic69_signed_gradient|
|M22|detector=C02/M；model=harmonic69_contribution|
|M23|detector=C02/kNN；model=harmonic69_contribution|
|M24|detector=MSP；model=harmonic69_contribution|

|方法|known %|fault %|條件 F1|完整健康誤報 %|unknown recall %|
|---|---|---|---|---|---|
|M01|31.43|26.00|0.2406|40.91|18.44|
|M02|31.43|26.00|0.2406|40.99|5.45|
|M03|31.43|26.00|0.2406|44.74|4.60|
|M04|27.95|24.83|0.2183|56.11|18.44|
|M05|27.95|24.83|0.2183|56.18|5.45|
|M06|27.95|24.83|0.2183|61.31|3.89|
|M07|24.71|26.22|0.2033|83.31|18.44|
|M08|24.71|26.22|0.2033|83.31|5.45|
|M09|24.71|26.22|0.2033|83.60|1.68|
|M10|25.41|26.99|0.2175|82.82|18.44|
|M11|25.41|26.99|0.2175|82.82|5.45|
|M12|25.41|26.99|0.2175|84.28|1.21|
|M13|37.29|31.25|0.2666|30.46|18.44|
|M14|37.29|31.25|0.2666|30.46|5.45|
|M15|37.29|31.25|0.2666|30.67|5.30|
|M16|35.83|29.53|0.2489|30.60|18.44|
|M17|35.83|29.53|0.2489|30.60|5.45|
|M18|35.83|29.53|0.2489|31.13|6.36|
|M19|35.20|30.54|0.2519|39.47|18.44|
|M20|35.20|30.54|0.2519|39.47|5.45|
|M21|35.20|30.54|0.2519|39.96|2.51|
|M22|36.44|30.08|0.2379|29.75|18.44|
|M23|36.44|30.08|0.2379|29.79|5.45|
|M24|36.44|30.08|0.2379|30.21|3.50|

## 附錄二 契約理由與來源恢復索引

### M01 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；motor F1 T2 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；motor F1 T2 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；motor F1 T2 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M02 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；motor F1 T2 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；motor F1 T2 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；motor F1 T2 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M03 契約未通過原因

health ('T3', '6000rpm', 0)；coverage ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；coverage ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；coverage ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；coverage ('T1', '6000rpm', 0)；coverage ('T1', '6000rpm', 1)；coverage ('T1', '6000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；motor F1 T2 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；motor F1 T2 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；motor F1 T2 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M04 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M05 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M06 契約未通過原因

health ('T3', '6000rpm', 0)；coverage ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；coverage ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；coverage ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M07 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M08 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M09 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；coverage ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；coverage ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；coverage ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M10 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M11 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M12 契約未通過原因

health ('T3', '6000rpm', 0)；health ('T3', '8000rpm', 0)；coverage ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '6000rpm', 1)；health ('T3', '8000rpm', 1)；coverage ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '6000rpm', 2)；health ('T3', '8000rpm', 2)；coverage ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '6000rpm', 0)；health ('T2', '8000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；health ('T2', '6000rpm', 1)；health ('T2', '8000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；health ('T2', '6000rpm', 2)；health ('T2', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M13 契約未通過原因

health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T2', '11000rpm', 0)；health ('T2', '11000rpm', 1)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M14 契約未通過原因

unknown noninferiority ('T3', '11000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M15 契約未通過原因

unknown noninferiority ('T3', '11000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M16 契約未通過原因

health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T2', '11000rpm', 0)；health ('T2', '11000rpm', 1)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M17 契約未通過原因

unknown noninferiority ('T3', '11000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M18 契約未通過原因

unknown noninferiority ('T3', '11000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M19 契約未通過原因

health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；health ('T2', '11000rpm', 0)；health ('T2', '11000rpm', 1)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M20 契約未通過原因

unknown noninferiority ('T3', '11000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M21 契約未通過原因

health ('T3', '8000rpm', 0)；coverage ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；health ('T3', '8000rpm', 1)；coverage ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；health ('T3', '8000rpm', 2)；coverage ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '11000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '11000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T1', '11000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M22 契約未通過原因

health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；health ('T2', '11000rpm', 0)；health ('T2', '11000rpm', 1)；health ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M23 契約未通過原因

unknown noninferiority ('T3', '11000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；primary F1 seed1；primary accuracy seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；primary F1 seed2；primary accuracy seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

### M24 契約未通過原因

coverage ('T3', '6000rpm', 0)；coverage ('T3', '8000rpm', 0)；unknown noninferiority ('T3', '11000rpm', 0)；coverage ('T3', '6000rpm', 1)；coverage ('T3', '8000rpm', 1)；unknown noninferiority ('T3', '11000rpm', 1)；coverage ('T3', '6000rpm', 2)；coverage ('T3', '8000rpm', 2)；unknown noninferiority ('T3', '11000rpm', 2)；health ('T1', '6000rpm', 0)；health ('T1', '8000rpm', 0)；health ('T1', '6000rpm', 1)；health ('T1', '8000rpm', 1)；health ('T1', '6000rpm', 2)；health ('T1', '8000rpm', 2)；unknown noninferiority ('T2', '8000rpm', 0)；health ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '11000rpm', 0)；unknown noninferiority ('T2', '8000rpm', 1)；health ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '11000rpm', 1)；unknown noninferiority ('T2', '8000rpm', 2)；health ('T2', '11000rpm', 2)；unknown noninferiority ('T2', '11000rpm', 2)；primary F1 seed0；primary accuracy seed0；postrejection seed0；motor F1 T3 seed0；class collapse T3 seed0；motor unknown floor T3 seed0；motor F1 T1 seed0；class collapse T1 seed0；motor unknown floor T1 seed0；class collapse T2 seed0；motor unknown floor T2 seed0；primary F1 seed1；primary accuracy seed1；postrejection seed1；motor F1 T3 seed1；class collapse T3 seed1；motor unknown floor T3 seed1；motor F1 T1 seed1；class collapse T1 seed1；motor unknown floor T1 seed1；class collapse T2 seed1；motor unknown floor T2 seed1；primary F1 seed2；primary accuracy seed2；postrejection seed2；motor F1 T3 seed2；class collapse T3 seed2；motor unknown floor T3 seed2；motor F1 T1 seed2；class collapse T1 seed2；motor unknown floor T1 seed2；class collapse T2 seed2；motor unknown floor T2 seed2。

R2 多 subset／壓力證據未完成；fresh final test 與每類群組數 INCOMPLETE，採集來源 UNKNOWN。

|M stage|實際索引路徑|實體 SHA256|
|---|---|---|
|protocol|output\fault_type_self_challenging_lock\2026-10-04-22-01-49\protocol.json|9d32f19808b921d15b26f618e3b21b7194e27a0d248fa49cf97e3847ffa07032|
|fit|output\fault_type_self_challenging_fit\2026-10-04-22-03-00\locked_study.json|b42c9c2058d7eaa424c770cfd0aaa7197d1b2c6108780355532c3b4a20c4a5c3|
|source_proof|output\fault_type_self_challenging_source_verify\2026-10-04-22-09-26\source_verified.json|212b703894e128ca31c317c050167189ebd2fb1639420a1ffda982e364f31a04|
|evaluate|output\fault_type_self_challenging_evaluate\2026-10-04-22-16-34\evaluation.json.gz|7b405ea0f39311ce5ae26f37e6bab8105e4c274b4477b6df16dfb2860e4118ab|
|verify|output\fault_type_self_challenging_verify\2026-10-04-22-18-59\verified.json.gz|5f2124752c31b6281d1a53b4eff3c3f9ca958b418455a9586ed7aa5f3beda472|
|report|output\fault_type_self_challenging_report\2026-10-05-22-17-39\summary.json.gz|1fb611a2b93d98deba6d4e395ee268275cba466f22549d197bb2a140508a0fff|
|backup|output\fault_type_fixed_delivery\2026-10-05-22-32-32\member_verification.json|732a2b1866ffd975d91437b7900b16768b15a4c5d39ba4bbe8277b5f871079b7|

盤點根目錄 output\fault_type_research_closeout\2026-10-05-22-34-03；當前內容產物 output\fault_type_research_closeout\2026-10-05-22-53-29。checkpoint_inventory、decision_record、fold_support、method_catalog.json.gz 與 arm_inventory.json 是可重算／追溯入口。 accuracy study 背景另見 reports/fault_type_accuracy_study/result_index.json：198新評估、18 A0重用，不與主研究controls重複加總；老師歷史2,490另列。

本回合先行手冊 4fb72015d8461846d90f19dd9fac7e25dcd56a8e、盤點63f1e2e9a161b31e4a5a8c23c7d31a5918770630 均已push並核對remote。M協定5d4893b7ac89d4570cc764703952354841058592、fit ffbc0aac9bea74f70f5f4bd151653a3b0f7efa07、source e0798d72254b03bd3177aa5dd00d965cfec6a93f 均已保存；後續交付commit以execution_log與delivery_index為準，避免把文件自己的SHA循環寫入文件。


## 附錄三 2026年10月6日引用稽核與原待辦核對

原完整報告保留，本版本加本輪勘誤與閱讀深度。不繼承舊全文聲明作本輪重新全文閱讀證據。原有所有方法數值不變。

### #22 原待辦核對：hard600 outer 已執行，未通過改善契約

2026-10-05，Asia/Taipei。本文件更正 issue 原 checkbox 的進度，不修改封存研究產物。

## 完成證據

exp13 的 E02 是 hard600 對角距離＋train 子集的距離加權 5NN；E04 是同一距離＋全部 known train 的 5NN。E01／E03 為各自 identity 配對基線。E10／E12 另測同學習空間的 factory Mahalanobis-LW／k-NN；E08 使用原 LMNN Eq.15 的三項 energy 分類。這正是原待辦的 outer，不是以後續不同研究代替。

本輪唯讀核對 `output/fault_type_citation_audit/2026-10-05-23-51-20/existing_evidence_verified.json.gz`：

| 項目 | 結果 |
|---|---|
| 90 CSV／28,910 筆／105 維 | 指紋 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d 一致 |
| 九份 hard600 權重＋solver diagnosis／protocol | 逐檔實際 SHA 與 outer protocol 指定一致 |
| E protocol seal | 9ca9be082013349680b642e509be761d84ca150a947429251bd1c50f86ed1a8b |
| E evaluation seal | f7b055a5f3081d0c0718fa52d0705c0edd29528f2cbc5cdfb9617101a41cb60a |
| E verification seal | 66b5dce1ce08d3d0dd778faac7b13ab3893e5097372c46ae1d275ec65cd084d5 |
| E report seal | cc05eabc98cfce711dda0999032fec524d0ea3ac720d82cf285365a7fa4b277c |
| 實際 outer 評估 | 108 組、失敗清單空、1,040,760 筆預測紀錄、28,910 unique samples |
| 本輪訓練／新預測 | 0／0；上述為既有封存核對 |

完整參數、每 motor／RPM／seed 結果、來源與備份已在 [exp13 結果](../metric_classification_v1/final_findings.md) 與 [索引](../metric_classification_v1/result_index.json)。本輪只驗 seals、綁定與來源 SHA，不冒稱重新推論全部預測；先前 exp13 verification 保存逐筆重推證據。

## 配對結果與收尾理由

固定 seed0、三 motor 等權描述平均，fault accuracy 僅 true known faulty：E01 28.475% → E02 24.968%，下降 3.507 個百分點；E03 28.464% → E04 24.809%，下降 3.655 個百分點。三 seeds 全部保留，不能取 E06 seed2 的較高值替代主成績。E 方法 T1 unknown recall 仍為 0%；12 方法全部未過可靠性契約。

之後 M 批 216 組／24 方法也全部 FAILED。既有各批及無效／未完成格子見 [完整研究報告](../research_closeout_20261005/final_report.md)。本輪收尾，不啟動預先規劃但未執行的 N／Group DRO，不把它寫為算法已完成。#22 可依本輪階段收尾結案；#9 仍追蹤來源與獨立研究資格。

研究分層：用途與產物核驗 VERIFIED；可靠提升 FAILED；fresh final INCOMPLETE；session／原始錄製／視窗／物理一致性 UNKNOWN。正式 default105／linear／LW、PolarMap 與可切換 factory k-NN 不改。


### 原始文獻內容、適配與主張稽核

工作始於2026-10-05，部分交付跨至2026-10-06（Asia/Taipei）。範圍與候選擷取見exp23手冊；書目驗證與內容判定分開。原來源題名與作者保持原文，新筆記使用繁體中文。下列是本輪實際核對的關鍵章節，不繼承前回合「全文閱讀」作本輪重新逐頁閱讀聲明。

## 六項直接取用來源

### B26：LMNN

Weinberger與Saul（2009），JMLR10:207–244，[原文](https://jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。本輪查§3.1–3.2、Eq.10–13、§4.1 Eq.15、Appendix A；原法固定同類target neighbors，使用拉近距離與推離impostors的hinge，學PSD metric。原方法是已知分類，不保證新motor或unknown辨識。

本站core/fault_type_continuous.py、fault_type_smooth_margin.py、fault_type_metric_classifiers.py將metric限制為非負對角，採mean-scaled loss、identity ridge、class×RPM子集及固定optimizer。E02／E04把收斂hard600接5NN；E08另取Eq.15三項energy分類。判定PARTIAL／明確改編，不是忠實full-PSD重現。收斂只是訓練問題成功，不是泛化成功。

### B27：MMMF的單一smooth loss

Rennie與Srebro（2005），ICML，[作者稿](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf)。查§3.3、Eq.9：shifted generalized logistic為γ⁻¹log(1+exp(γ(1−z)))。本站只取scalar，把z對應負／正距離差，τ=.1與γ=10相對應；另保留本站pull、mean與ridge。沒有rating matrix、低秩factorization或MMMF推論。判定PARTIAL；不得將27個solver診斷稱27次完整MMMF實測。

### B34：Invariant Kernel

Haasdonk與Burkhardt（2007），Machine Learning68:35–61，[作者稿](https://lmb.informatik.uni-freiburg.de/papers/download/ha_bu_MachineLearning6807.pdf)。查Eq.2、Proposition11及有限群平均條件。本站core/fault_type_axis_kernel.py使用S3軸排列、共享同名特徵scaler與RBF；共同正交置換使雙群平均可化為六項。α=1才對完整排列群不變，α=.5只是混合。既有105→66抽取、參數、RKHS拒絕是本站適配，不支持任意連續旋轉、安裝變動或真正物理一致性。判定PARTIAL；代數不變不等於診斷可靠。

### B35：REx

Krueger等（2021），ICML／PMLR139:5815–5826，[原文](https://proceedings.mlr.press/v139/krueger21a/krueger21a.pdf)。查§2.5模型選擇、§3.1 Eq.8、§3.2理論限制。Eq.8為風險sum＋β variance；本站core/fault_type_risk_extrapolation.py為三RPM等類risk的mean＋β population variance＋ridge。固定mean不是逐式相同：乘三後，相當於原sum式variance係數3β及相應ridge。RPM不是三個獨立motor環境；因果介入與同方差假設未獲證明。判定PARTIAL。risk variance降低不能被寫成跨motor因果或可靠性已成立。

### B36：RSC

Huang、Wang、Xing、Huang（2020），ECCV，[arXiv v1](https://arxiv.org/pdf/2007.02454v1)。查§3.1 Eq.1–5、Algorithm1與遮蔽條件；原法以learned image representation的true-class signed梯度遮蔽特徵再更新網路。本站core/fault_type_self_challenging.py在固定手工特徵與linear softmax上做200固定SGD steps、exact-ceil比例、stable ties、train-only ERM warm及四個controls。貢獻遮蔽另列variant，不冒稱唯一原RSC。最後iterate不代表收斂，影像理論不自動移植；判定PARTIAL。M24方法全部FAILED只否定本站有限條件，不反證原文章的影像實驗。

### B20：MSP

Hendrycks與Gimpel（2017），ICLR，[v3原文](https://arxiv.org/pdf/1610.02136v3)。查§3 baseline、正負score與PR定義。原MSP以最大softmax判別；本站NoveltyReference用1−MSP，另一motor known-only q95是本地校準約定。LDA／線性手工特徵不同於原深網路。MSP不是已校準信心；q95不保證跨motor5%FPR。判定PARTIAL，未知positive AUPR須報prevalence。

## 其他需同步更正的主張

| ID | 專案原位置／主張 | 判定 | 正確界線 |
|---|---|---|---|
| C01 | main README.md「T1/T2/T3三個壽命期、run-to-failure模板」 | CONTRADICTED | 固定Guide支持不同個體，沒有時間／failure endpoint，不支持生命週期串接 |
| C02 | README.md「7→1 screws天然嚴重度階梯」 | UNVERIFIED | 配置數量／位置不是經量測的損傷嚴重度，不能據此RUL |
| C03 | README.md持續學習引EWC／iCaRL支持完整rehearsal | PARTIAL | [EWC原文](https://doi.org/10.1073/pnas.1611835114)為權重保護；[iCaRL原文](https://openaccess.thecvf.com/content_cvpr_2017/html/Rebuffi_iCaRL_Incremental_Classifier_CVPR_2017_paper.html)含exemplar／representation learning。本站全資料重fit不是這兩法，也無跨域不忘保證 |
| C04 | 原始Mahalanobis1936引用2019 DOI | SUPPORTED_WITH_VERSION_NOTE | 10.1007/s13171-019-00164-5為重印，不是1936原始DOI；現main實驗手冊已注明 |
| C05 | factory k-NN引用Cover／Ramaswamy／Sun | PARTIAL | [Sun2022](https://proceedings.mlr.press/v162/sun22d/sun22d.pdf)為normalized deep embedding第k距離；本站逐類平均k距離＋known校準，不是其完整方法或同資料成績 |
| C06 | q95＝5%跨motor誤報保證、conformal可保證跨motor | CONTRADICTED_IF_ASSERTED | [Conformal原來源](https://arxiv.org/html/2107.07511v6)需對應exchangeability；本站未證明，不給coverage保證 |
| C07 | core數值改編等同原論文全部算法 | PARTIAL | 上述六卡逐一列來源與差異；新文件不得省略adaptation |
| C08 | OpenSet_Recognition.md的2607.13368不存在 | NOT_A_VALID_CRITICISM | [原arXiv](https://arxiv.org/abs/2607.13368)確認Jeon／Lee，2026-07-15；查§3.1–3.5，需raw STFT與CSAE，不是本站既有105維忠實實測 |
| C09 | MetaMax是OpenMax後續、已在本站做過 | METADATA_SUPPORTED_ONLY | [arXiv](https://arxiv.org/abs/2211.10872)作者Lyu／Gutierrez／Beksi，v1 2022、v2 2026；本輪摘要與HTML方法局部查核，不冒稱本站實作 |
| C10 | 樹模型／DG原文headline可保證本站提升 | UNVERIFIED | 資料、架構、切分與模型選擇不同；只能作候選動機，本站以封存實測判定 |
| C11 | LOF兩個ACM DOI是誤引 | NOT_A_VALID_CRITICISM | 335191.335388為SIGMOD Record、342009.335388為proceedings登錄；保留manifestation，不將其計成兩個新方法 |
| C12 | AGLVQ DOI登錄題名與PDF不同 | METADATA_VARIANT | 登錄含「Algorithms」，原PDF題名為Making Generalized Learning Vector Quantization Aware of Context；以[原PDF](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)為本文題名，不把差異寫成不存在 |

上述勘誤在新研究交付稿與老師回覆中生效；不改sealed模型或覆寫歷史README、manifest、prediction。main／Albert文件的文字修正列為清楚的後續patch範圍，沒有直接覆寫PR #36所涉文件。

另外兩項關鍵未解：C13為Ancestor固定1ef4a891的論文轉錄（論文全文.md／html）缺參考文獻表，末節只指向原稿p.89；正文部分作者年分無法辨識。判定UNVERIFIED，不猜唯一論文或聲稱捏造。C14為Ancestor摘要約99.90%與本期跨馬達25%直接比較：資料角色、類別、表示與unknown評估不同，判定UNVERIFIED_COMPARISON；不能繼承原成績或計算純演算法下降。

## 全部清冊的未解界線

paper_catalog保留舊40筆B來源及新找到的出版／DOI／arXiv／作者來源。citation_occurrences逐筆保留ref、Git blob/file SHA、路徑、line/cell、source IDs及待判定狀態；非論文software、repo與schema另標，不把所有URL當論文。

未取得全文的書、付費文章、只有搜尋摘要的跨語言候選，以及README只有作者年分的Wang2008等，不能填SUPPORTED。王姓2008PHM雖有可能題名，但原文未給唯一ID，不能用猜測合併。多語言候選不是多語言演算法實測；不清除未解條目，不把全部候選自動改VERIFIED。

因此本輪可交付完整固定範圍清冊、核心六來源內容與重大主張勘誤，但#19的「全部內容相符」仍未驗收。保留OPEN，精確未解由catalog、search_log與unresolved索引追蹤。頁面403、SSL錯誤、429或沒有citation tags只表示取得受限，不作論文不存在的判決。未繞付費牆或停用TLS驗證。
