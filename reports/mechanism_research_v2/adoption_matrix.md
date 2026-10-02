# 採用矩陣

| 分類 | 方法 | 本輪動作／理由／反例 |
|---|---|---|
| 已測、控制重用 | LR/LDA各shrinkage/RDA-inspired/RF/ET/HGB/RBF-SVM/GNB/kNN/PCA/NCA | 舊完整arm+SHA仍封存。NCA9fits收斂，不是待修bug。C02/C17/C24/C18作匹配/機制控制，不換名新算法。 |
| 已測、控制重用 | factory M/K、RMD/OAS/diag/multicenter/GMM/IF/LOF/OCSVM/MSP/entropy/margin/fusion/LDA Energy/ViM | 新metric重算健康完整誤報。R17六格routing不足仍INCOMPLETE。不能以深網論文名代表tabular faithful replication。 |
| 真正新增組合 H-D | 分類 C17/C24 與拒絕 C02 解耦 | 三個完整組合；可保留分類与更高C02 recall，不能消除classifier健康錯誤。 |
| 新改編 H-P | RPM partial-pooling LDA-like | 固定β0/.5/1；mean及within-cov收縮，保留amplitude，C02 detector固定。反例：motor shift大、單RPM樣本少。 |
| 新改編 H-G | amplitude-preserving block-LW geometry | stats/shape/amp三塊每維等權，λ0/1 background、classifier固定/nearest對照。反例：跨塊關係有用、cal shift。 |
| 新機制但延後 | LMNN / SupCon / LogitNorm / OpenMax / DeepSVDD | 有文獻方法查閱；solver/tail/neural與合法開發/augmentation契約未驗證，有限預算優先可解釋改編。不是說這些已失敗或一定不適用。 |
| 當前缺資料 | raw envelope / order / STFT/wavelet | 沒有可驗證row→recording/rate/timing，不排列105特徵當waveform。 |
| 違當前資訊邊界 | target-fit CORAL / DATF | cal僅threshold，不以targettest covariance/pseudo labels fit；不增加跨fold共同selector。 |
| 限制與反證依據 | DomainBed / Wheat leakage / trees-vs-deep / conformal | 規範selection/來源/假設，不是新研究arm或部署保證。 |

選擇依已曝光診斷與歷史結果，整輪exploratory。無合法內層session groups，固定文獻啟發參數，不造row-validation。
暫定每motor/RPM健康total≤10%為第一安全篩選；之後呈現worst class/unknown與trade-off，不產生部署selected winner。
