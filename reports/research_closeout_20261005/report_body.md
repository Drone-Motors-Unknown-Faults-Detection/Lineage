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

{{fold_table}}

這些筆數由 records_for 與既有 manifest 重算，不讀 test 特徵、不擬合。fold_support.json 保存逐類／RPM 支持及排序 sample IDs 的 SHA。完整 sample IDs、來源檔 SHA、fit audits 在原 manifests、locks 和各批 source proof，並由 checkpoint_inventory 串接。

{{support_table}}

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

{{control_table}}

{{control_rejection_table}}

{{control_delta}}

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

{{batch_table}}

各批以 batch／arm／fold／seed 身分去重，表內 prediction records 是重複推論，不新增獨立資料。表中 reliability FAILED 和 runner error 分開；INCOMPLETE 留原缺項，不能補做容易格後報全部完成。本回合只讀歷史產物與補 M report，不重跑歷史 2,490 格。

Q 的數值失敗由封存末 weights、optimizer message 與固定預算記錄；使用額度中斷不能算演算法失敗。solver27 只有 train-only 診斷，沒有追加 outer prediction。hard600 九 fit 收斂於 ftol，不能隱藏 projected-gradient 尚高於 gtol 的情況。該結果支持預算／停止規則的重要性，不支持 test 成績提升。

K 的不變核全部九方法、L 的風險外推十八方法，以及 M 的自挑戰二十四方法未通過原契約。L 增大 beta 可降低 train RPM 風險差異，但跨 motor 最差類仍為零，反駁「train 工況更一致即可得到可靠 cross-motor」這個充分條件。

## 八 成績 消融與最差工況

{{selected_table}}

這些是解釋失敗的代表，沒有指定 global winner 或部署替換。所有新 arms 的主數值在附錄列出；全部 fold／seed／RPM／class 的原指標與混淆矩陣在 method_catalog、各批 summary 和 evaluation，一併引用來源與 SHA。

{{m_seed_table}}

{{m_delta}}

{{m_motor_table}}

{{m_rpm_table}}

{{m_class_table}}

M13 的 seeds 0／1／2 結果完全相同；random 版有微小變動，其他版相同時亦原樣保留。不能把三 seeds 的低 SD 當馬達母體信賴區間。三顆 motor 沒有足夠採集群組支援逐窗 IID bootstrap 的精準泛化保證。

{{m_gate_table}}

所有 M 方法逐 seed 最差 known fault recall 為零，健康 motor-macro 三seed實值範圍約 29.75%–84.28%。逐方法原始 reasons 包含 motor／RPM／seed，見 decision_record.full_contract_gates；附錄保留原因計數及完整索引，沒有只留下表現較好 seed。

## 九 失敗分析與可反駁假說

已排除的工程疑點包括 test IDs／SHA 不匹配、來源副本別名繞過、cal 混入 fit、test truth 改變推論、NaN／分數方向／reject 符號與報表分母錯配。來源 proof 從 known train／cal 重建模型與 threshold，test_numeric_reads=0；outer verifier 再逐筆重推及重算。工程 VERIFIED 的範圍是保存的 formal 計算鏈，沒有由此推導 raw 採集獨立性。

配置重疊有模型行為證據：D01 三 motor 的 2screws recall 都為零，多支線仍有零類別。它支持「現有表示與已知分類邊界不足」的診斷，不能直接證明原始物理訊號不可分。T1 的 factory 未知召回為零；相同 reference 下更換分類器仍為零是控制預期，不能只改 classifier 就稱 OOD 已改善。

motor domain shift 與 calibration transfer 有跨 motor／RPM 的分層差異支持。T1 可在某些替代 detector 得到較高 unknown recall，但會伴隨健康大幅誤報；J03 與 K09 是明確例子。局部召回提高不足以通過安全保護。AUROC 接近有限排序能力也說明只調 threshold 未必解決分布重疊，本輪沒有用 T1 test 掃最有利閾值。

形狀與幅值、軸對應、RPM context 等改編有合理機制，卻沒有通過全面契約。L 的 train 風險差異降低、M 的遮蔽訓練完成都沒有消除最差類與健康誤報。這些失敗反駁有限適配的充分條件，不否定原論文。感測器安裝、實際負載、個體老化是否造成偏移，目前缺證據，只列可能解釋。

未取得時間順序與 raw session，不能計算每小時誤報／警報延遲；未取得退化真值，不能計算 RUL 或損壞百分比。失敗後未回寫本輪 test 規則，保留全部不利格。

## 十 可信度狀態與老師問題回覆

{{status_table}}

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

原 618 項完整科學測試已在 10 月 4 日兩環境通過，pip check 與 37 CLI helps 等共 39 commands 全部 exit0；本次沒有再跑618。新盤點9項 toy tests 在兩環境均 PASS。Word 使用 loader 的 bundled Python 與 python-docx，與科學環境分開，不升級原實驗依賴。

{{reproduction}}

內容與 JSON 對照、引用、Word editable elements、ZIP 及 SHA 分開驗收。頁面 PNG 渲染必須使用 bundled renderer；目前 Windows bundled runtime 無 LibreOffice，不能改用使用者 desktop 安裝。若正式 renderer 無法啟動，另以 content_qa.json 記錄 LAYOUT_UNVERIFIED，內容檢查不冒充逐頁視覺檢查。

## 十四 參考文獻與閱讀範圍

以下書目與正文 B 編號對應；原論文方法、官方 API 與本站操作約定分開。來源卡證明的全文閱讀與僅核對摘要的項目分開，本回合沒有重新讀完全部40篇。公式差異與程式碼以先行手冊和 method_catalog.protocol 為準。

{{references}}

## 附錄一 全方法主數值與配置

下表不作最佳方法排序。方法按 sealed registry ID，保留對照與 INCOMPLETE。主表數值採 motor-macro seed0；全部 seeds、完整 final 分母、每 motor／RPM／class、來源與參數都留在附帶機器索引。部分早期分數的 healthy_safety.false_positive_rate 僅記 unknown alarm，不能冒稱完整健康誤報；早期方法該欄標 NA，完整值沿 metric_definition_v2 重算報告。

{{all_methods}}

## 附錄二 契約理由與來源恢復索引

{{m_reasons}}

{{artifact_table}}

{{delivery_notes}}
