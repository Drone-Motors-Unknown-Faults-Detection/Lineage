# 失敗診斷：有證據、反證與未知

只讀既有 C17 封存模型，seed 0 三折；模型/234 audits/來源 SHA 前後核對。没有新 fit。
訓練診斷是 **in-sample 樂觀資料**；cal/test 是跨馬達且已曝光的事後診斷，不能當獨立開發集選參。
產物 `output/fault_type_mechanism_diagnosis/2026-10-02-12-53-20/mechanism_diagnosis.json`。
seal `9ce597e1ec609ece68b8b2a9a5b2ee8e9bf9e1c02897ada1a1c43343f4097d4f`。
兩幅圖已檢查（train/cal/test class collapse；centroid shift），不是 causal proof。

| train → cal → test | 2screws train/cal/test recall | train 2screws n | test true-class margin median |
|---|---|---:|---:|
| T1 → T2 → T3 | 100% / 0% / 0% | 980 | -135.86 |
| T2 → T3 → T1 | 100% / 0% / 0% | 1020 | -422.06 |
| T3 → T1 → T2 | 100% / 31.63% / 0% | 985 | -54.93 |

整體 train accuracy 100%、100%、99.9643%；不是 train 缺少該類。每類約 900–1050 筆，不支持單由嚴重類別不平衡解釋。
test 的 2screws 全部 true-class margin <0；不是 reject 後才消失。最近競爭類包含 3screws/4screws。
每類 covariance rank 63/69，shape 有和約束等冗餘；不能由 rank 單獨判定數值 bug。
label/source mapping 與有限值、順序均沿原 validators/FeatureStore；沒有確認 label sign/index bug。

同 RPM 的 2screws cross-motor centroid displacement / train within-RPM RMS dispersion：
fold0 8.14–19.95；fold1 3.89–6.81；fold2 3.27–9.87。
同 motor 跨 RPM 比值分別 5.48–8.47、3.62–6.09、1.91–3.85。
跨馬達與 RPM 均有明顯表示位移；效果只是描述性比值，沒有逐窗 IID CI。
物理單位/安裝/負載未知，所以不能歸因老化、感測器或真正故障機制。

harmonic69 三塊 train RMS logit contribution（stats/shape/amplitude）：
108.68/2192.02/111.68，323.47/1215.53/206.98，53.74/832.45/70.31。
這是仿射分量尺度，**不是 causal importance 或可相加的 explained variance**。
scaled train 無 constant columns；最大 abs 16.26/10.89/14.66。
既有 C18 刪 amplitude 後分類下降；因此不直接丟 amplitude，而研究分塊幾何與維度平衡。

R17 的實際 parent 是 C01，不是 C17。cal 原始每类皆≥850筆；predicted-class routing：
fold0 的 3screws=0，fold2 的 2screws/4screws=0。原六格不足是 routing 缺樣，不是 cal 真類缺失。
不補零、不改原 R17；本輪 pooled minimum-class score 不使用 predicted cal group。

分類/拒絕衝突可由 metric_v2 全 624 組的 conflicts、per-class confusion、RPM health alarms 查核。
C17/M unknown recall 8.44% vs C02/M 18.44%，而 C17 known accuracy 較高；不支持「分類改善必定改善拒絕」。
R18 增 unknown recall 但最差健康完整誤報仍 100%，不支持單靠 signed background subtraction 即可靠。

UNKNOWN：sessions、raw overlap、刪點、單位、實際使用時數、獨立 development groups。
不計每小時警報/延遲/RUL；不把三顆不同馬達串成生命週期。
