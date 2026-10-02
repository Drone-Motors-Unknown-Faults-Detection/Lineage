# fault_type_continuous_study 技術手冊

2026-10-02 補寫既有 Q 批，未改模型／切分。原 protocol 在外層評估前已封存；手冊補寫不宣稱事前盲測。與 [registry](fault_type_continuous_registry.md)、[報告 v2](fault_type_continuous_report_v2.md) 共讀。

## 方法、資料與參數

正式 90 CSV、28,910 筆 105 維，fingerprint 見 [分支說明](../research_improvements_20260920.md)。healthy=8screws；known faulty=`1screws,2screws,3_14screws,3screws,4screws`；unknown=`4_146screws,5screws,6screws,7screws`。同一既有 parent manifest，fold0 T1/T2/T3、fold1 T2/T3/T1、fold2 T3/T1/T2，順序 train/calibration/test。三 RPM=6000/8000/11000，seeds=0/1/2。

validation/selection 空，selection_policy=none；representation/scaler/classifier/reference 只 fit train-known。cal-known 只校準固定 threshold；unknown 不進 fit/cal。沿已曝光資料研究，不做共同 winner，不提供 fresh C。

| arm | 分類分支 | detector |
|---|---|---|
| Q01 | harmonic69、identity、subset k-NN | C02/M |
| Q02 | harmonic69、diagonal margin、subset k-NN | C02/M |
| Q03 | harmonic69、identity、all-train k-NN | C02/M |
| Q04 | harmonic69、同 Q02 metric、all-train k-NN | C02/M |
| Q05 | gain63、uniform LDA | self/M |
| Q06 | gain66、uniform LDA | self/M |
| Q07 | gain69、uniform LDA | self/M |
| Q08 | 同 Q06 classifier | C02/M |

k-NN：k5、distance weights、brute、p2、n_jobs1。LDA：lsqr、shrinkage=auto、uniform priors。RobustScaler quantile_range=(25,75)。LW factory 使用 parent 實值參數，校準分位數 .95/linear，score>1 拒絕；等於1接受。

metric subset 每 class×RPM 最多20 rows，上限360，僅 train，default_rng(seed)，不是獨立 development。固定原空間同類3個 target neighbors：
`J(w)=.5 mean_target d_w(i,j)+.5 mean_triplets max(0,1+d_w(i,j)-d_w(i,l))+.01 mean((w-1)^2), w>=0`。
L-BFGS-B maxiter150/maxfun500/maxls50/ftol1e-9/gtol1e-6/120秒；未收斂保留 INCOMPLETE，不替換參數。

gain63 保留各軸11統計＋10諧波比例，用逐列 RMS 去除相關幅值尺度；gain66 加3個 relative amplitude；gain69 再加3個 absolute amplitude。floor=max(train median×1e-6,1e-12)，只從 train fit。RMS 比值的正 gain 不變性僅在 floor 未啟動範圍成立；幅值屬 nuisance 尚未有物理證明。

## 文獻與改編來源

- Kilian Q. Weinberger、Lawrence K. Saul（2009），Distance Metric Learning for Large Margin Nearest Neighbor Classification，JMLR 10:207–244，[作者論文](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。原 full PSD/sum 的 LMNN，本地改為非負對角、mean-normalization、identity ridge；不稱完整復現。
- Chwan-Lu Tseng、Shun-Yuan Wang 等（2014），A Diagnostic System for Speed-Varying Motor Rotary Faults，Mathematical Problems in Engineering，Article 310626，[DOI 10.1155/2014/310626](https://doi.org/10.1155/2014/310626)。提供諧波／幅值背景；逐列 RMS 比值是本專案改編，不歸給該文。
- Olivier Ledoit、Michael Wolf（2004），A well-conditioned estimator for large-dimensional covariance matrices，Journal of Multivariate Analysis 88(2):365–411，[DOI](https://doi.org/10.1016/S0047-259X(03)00096-4)；透過既有 core.openset factory 使用。
- 工具與閱讀深度見 [source ledger](../../reports/continuous_research/source_ledger.md)。20 rows/subset、獨立分支與可靠性 gate 是本地操作約定。

## 預期與反駁判準

metric 的目標是改善跨馬達配置幾何；Q02↔Q01、Q04↔Q03 固定資料量分離 metric 效果，Q03↔Q01 分離 classifier reference 數量。gain63→66→69 檢驗消除／恢復幅值資訊；Q08↔Q06 分離 detector 效果。

成功以封存 reliability_contract 為準：fault macro-F1 對 C17、fault accuracy 對 C24 各至少+2pp；每 motor/RPM 健康總警報≤10%；unknown 對 C02 最多退2pp、每 motor unknown≥10%；每 motor known-class recall≥10%。其餘 coverage/postreject/motor guard 以 JSON 實值為準，不在 test 後改。若未收斂、健康越線或未知退步，記失敗或 INCOMPLETE。B 還需至少3 known subsets、消融與壓力驗證；C 需要真實未曝光資料。預期不保證分數上升。

## CLI 與續跑

repo 根目錄，科學環境 Python3.10.19：

```powershell
$python='.\.venv310\Scripts\python.exe'
$protocol='output/fault_type_continuous_registry/2026-10-02-18-40-41/protocol.json'
$lock='output/fault_type_continuous_fit/2026-10-02-18-42-53/locked_study.json'
$evaluation='output/fault_type_continuous_evaluate/2026-10-02-18-47-45/evaluation.json'
& $python -m experiments.fault_type_continuous_study verify --protocol $protocol --data-root data/formal_local --lock $lock --evaluation $evaluation
```

原 fit/evaluate 已執行，不為讀文件重跑；新 protocol 才使用 `fit --protocol ... --data-root ...`，封存 lock＋commit/push 後使用 `evaluate --protocol ... --data-root ... --lock ...`。`--resume` 僅接受該 action 的既有 output 目錄，保留 checksum/來源校驗，不混 protocol。

setup_run 為各 action 建 logs/output；保存逐 sample predictions、模型、fit audits、失敗、工況指標、SHA。verify 重推論、truth mutation、原始資料前後 hash 及 metrics。预算各 action1800秒，C槽保留1GB；不足保存 checkpoint。joblib 僅載入可信本機產物，SHA 不保證 pickle 安全；禁止跨 sklearn runtime 載入。

## 影響程式碼範圍與實際狀態

讀/執行：`experiments/fault_type_continuous_study.py`、`experiments/fault_type_continuous_registry.py`、`core/fault_type_continuous.py`、`core/fault_type_reliability.py`、`core/openset.py`、`core/fault_type_metrics_v2.py`；父來源 `experiments/fault_type_literature_study.py`、`experiments/fault_type_mechanism_study.py`。本文件未修改這些 scientific code。

2026-10-02 aggregate：72 planned、60 completed、12 INCOMPLETE；576,144 records、28,910 unique。T2/T3 train metric 達迭代上限，Q02/Q04 各只3 runs。verify/report 尚待完成；不計缺失 fold 平均，不回填0。
