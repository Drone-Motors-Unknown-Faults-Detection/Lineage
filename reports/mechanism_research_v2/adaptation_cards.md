# 九個完整改編與匹配消融（尚未執行新 outer test）

## D01–03：分類／拒絕解耦（H-D）

原 C17 harmonic69＋equal-prior auto-shrink LDA、C24 perRPM base75＋同LDA、C02 mixed base75＋balanced LR與factory。
以 Vaze2022 關係研究及本站反例作動機，不是取其未取得全文的特殊公式。
D01 C17/C02-M；D02 C17/C02-K5；D03 C24/C02-M。只換組合，不重新fit父模型。
detector score仍min-over-class factory，>1 unknown；clf與detector transforms/scalers/fit IDs/父SHA各記。
匹配控制 C17/M/K、C24/M、C02/M/K。D01 vs D02 isolate detector；D01 vs D03 isolate classifier。
分類與score必須逐筆等於對應父方法；健康完整誤報可能上升。這是本站新組合，不叫新論文算法。

## P01–03：RPM partial pooling（H-P，paper-inspired）

原來源 Fisher/Gaussian判別、Friedman1989 pooling觀念、Ledoit–Wolf2004 covariance，與本站C01/C24。
不是忠實原RDA；Friedman沒有在本引用提出本站RPM mean收縮公式。
固定global base75 parent RobustScaler（train-only），不各RPM重fit scaler。
每class/RPM μ_cr、全RPM μ_c；每RPM residual covariance S_r=LW(z_i−μ_y,r)，全RPM S=LW(z_i−μ_y)。
μ_cr(β)=(1−β)μ_cr+βμ_c；S_r(β)=(1−β)S_r+βS。
δ_c(z,r)=zᵀS_r(β)⁻¹μ_cr(β)−½μ_cr(β)ᵀS_r(β)⁻¹μ_cr(β)，uniform priors，argmax。
P01 β0、P02 β.5、P03 β1，detector全為固定C02/M；不test/cal挑β。
β0/1是此**新公式**端點；不假稱完全重現C24或C01（scaler/covariance估計不同）。
匹配 P01/P03端點、C24/C01歷史參考；RPM只routing不是故障特徵。
缺任何RPM/class≥2train或known-cal coverage→INCOMPLETE，不借test/fallback。

## G01–03：保留幅值的分塊幾何（H-G，paper-inspired）

原來源本站C17/C18 harmonic69/66（historical band maxima不是energy）、LW2004、Ren2021 RMD。
原RMD d_c−d_0 使用全feature共享within covariance；本改stats36/shape30/amp3三塊獨立LW residual/background。
d_c=(1/3)Σg[(z_g−μ_cg)ᵀP_g(z_g−μ_cg)/D_g]；d_0同式以all-known background。
s_λ=min_c d_c−λd_0；λ0/1固定；cal q95線性quantile，signed raw > q95，不除負threshold。
G01 C17clf/λ0，G02 C17clf/λ1，G03 block-nearest clf argmin d_c/λ0。
G01/G02 isolate background，G01/G03 isolate classifier；C17/M、C18shape-only、R18全cov作歷史控制。
amplitude三座標保留；去cross-block covariance與per-dimension權重是自訂，不聲稱原文已有。
全class minimum與argmin僅train means，不用test true class選normalizer。cal僅定threshold。

數值特例固定 eigen floor=max(trace/D,1e−12)×1e−10；零cov與負/空cal/缺class需測試。
新碼 `core/fault_type_mechanisms.py`；registry `experiments/fault_type_mechanism_registry.py`；runner `experiments/fault_type_mechanism_study.py`。
三機制×三arms×三fold×三seed=81，不額外交叉detectors。one round；若僅剩test微調則停止。
所有方法來源於已曝光診斷：execution前鎖定≠盲測；無獨立development，不選winner、不改production。
