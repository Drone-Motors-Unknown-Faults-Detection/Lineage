# fault_type_solver_diagnosis：train-only 最佳化診斷

2026-10-02，先寫手冊，再實作。此批不讀 calibration/test 特徵或評估標籤，不發布新外層準確率；原 Q02/Q04 的12格 INCOMPLETE 保留。

## 觀察、假說與比較

Q 的 hard hinge 對角 metric：train=T1三seeds收斂，train=T2/T3六fit達150iter上限。現有失敗artifact只保存例外字串，不能由字串推算最後loss／weights。

假說：hinge折點妨礙L-BFGS-B終止；競爭解釋是單純預算不足或病態尺度。固定三條train-only版本：

| method | triplet損失 | maxiter/maxfun | 其他條件 |
|---|---|---|---|
| hard150 | max(0,u) | 150/500 | 完整對照；新的診斷run不覆蓋原Q |
| smooth150 | τ log(1+exp(u/τ))，τ=.1 | 150/500 | 只改函數 |
| hard600 | max(0,u) | 600/2000 | 只改預算 |

u=1+d_w(i,j)-d_w(i,l)，只使用不同類impostors。三者皆使用原Q的harmonic69 train-only transformer、相同class×RPM20-row subset（最大360）、固定同類3target、w初值1／非負、pull=.5、push=.5、identity ridge=.01、maxls50、ftol1e-9、gtol1e-6。每fit120秒、總批1800秒、C槽至少1GB。三fold×seeds0/1/2×三loss/budget=27個train診斷，並非27個獨立實驗受試群。

τ=.1固定為unit margin的十分之一；逐triplet upper-bound誤差最多τ log2=.069315，objective push加權差最多.034657。這是數學近似尺度的本地約定，不由cal/test選τ。用logaddexp/expit避免overflow。

## 文獻

- Kilian Q. Weinberger、Lawrence K. Saul（2009），Distance Metric Learning for Large Margin Nearest Neighbor Classification，JMLR10:207–244。[原文](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)，§3.1–3.4/Appendix：LMNN與原subgradient/PSD solver。本地diagonal/mean/ridge及L-BFGS-B與原文不同。
- Jason D. M. Rennie、Nathan Srebro（2005），Fast Maximum Margin Matrix Factorization for Collaborative Prediction，ICML，[作者PDF](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf)，DOI10.1145/1102351.1102441，§3.3 Eq9 的 shifted generalized logistic。原問題為矩陣補全；本地僅改編此scalar函數到train triplets，並未復現MMMF。已讀方法與原評估的weak/strong generalization；作者原搜尋不提供本專案跨motor保證。
- [SciPy1.15.3 L-BFGS-B官方參數](https://docs.scipy.org/doc/scipy-1.15.3/reference/optimize.minimize-lbfgsb.html)：success不代表測試可靠，亦記projected gradient和停止理由。

## 執行與資訊邊界

run(pools,...)與main()；透過setup_run保存logs/output，每fit獨立checkpoint、config/data/source SHA、train subset IDs、optimizer、weights、同hard objective loss、time/memory。calibration_fit_ids與selection/test_input_ids明確空。parent manifest metadata可讀以確定fold，不load cal/test feature rows。SHA核對需唯讀所有CSV bytes，不將其內容fit。

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_solver_diagnosis smoke
.\.venv310\Scripts\python.exe -m experiments.fault_type_solver_diagnosis lock --q-protocol output/fault_type_continuous_registry/2026-10-02-18-40-41/protocol.json
# lock的實際protocol.json需commit/push後才能fit
.\.venv310\Scripts\python.exe -m experiments.fault_type_solver_diagnosis fit --protocol PROTOCOL_JSON --data-root data/formal_local
```

--resume只接受相同program既有output根目錄，每cell核對config/source/IDs/SHA，拒絕混版本。模型權重只是診斷产物；不直接回填Q模型、不選部署winner。原Q科學code及source ledger不改。

## 預期、反駁與下一步資格

如果smooth150在相同預算提高收斂覆蓋而hard600仍失敗，支持折點／solver適配線索；若只有hard600成功，支持預算解釋；兩者皆成功仍不能分離所有數值因素。若loss/gradient算錯、未知進fit、source變動就工程FAILED。全部不收斂則保留INCOMPLETE，不看outer分數找τ。

只有收斂、解析gradient/近似界/決定論和來源tests通過，才能在新的完整方法protocol中預登錄outer比較。訓練loss下降不能宣稱fault accuracy提升。父資料全部已曝光，任何後續比較仍exploratory；fresh final與獨立group缺口不因收斂修正而改PASS。

## 程式範圍

新增 `core/fault_type_smooth_margin.py`、`experiments/fault_type_solver_diagnosis.py`、`tests/test_fault_type_smooth_margin.py`；讀既有 `core/fault_type_continuous.py`、`experiments/fault_type_continuous_registry.py`、`experiments/fault_type_literature_study.py`、`core/fault_type_features.py`、`core/logger.py`。這份手冊先於新程式，未修改production、Q protocol或原結果。
