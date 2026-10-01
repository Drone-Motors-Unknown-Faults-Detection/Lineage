# Known-validation 小型模型比較：預先登錄

只比較 healthy+5known 的配置分類，不與healthy-only冷啟動混合。
使用原N5全126 registry的第一組（非最差／最好挑選）：known為
1screws、2screws、3screws、3_14screws、4screws；其餘4類unknown。
沿用3份原frozen manifests與seed42/123/2026，seed是fold識別，不是新採集。
每個fold只載入known train及known validation；unknown/test不進選擇。
此句僅指同折的輸入範圍，不代表共同global selector獨立於全部outer tests。
2026-10-01後續ID稽核確認三fold validation union為17,546個known rows，全部也在某outer test出現。
ExtraTrees的共同三fold選擇同樣依賴outer-test known rows，test改善只能描述性exploratory。
不改舊locks/predictions；完整相依數量見 `reports/data_independence/audit_20261001.md`。

候選集在實際訓練前保存並提交：

| 模型 | 固定參數 | 用意 |
|---|---|---|
| 原balanced logistic | C1,lbfgs,max_iter1000,tol1e-4 | 原baseline |
| RBF SVM | C1,gamma=scale,class_weight=balanced | 固定非線性局部相似性對照 |
| ExtraTrees | 200trees,depth12,minleaf5,max_features=sqrt,balanced | 分段非線性樹模型對照 |

所有候選用同一個該fold train-only RobustScaler，保持105维，沒有路径/T-code
特徵、PCA、embedding或故障label的numeric ID當輸入。樹/SVM random_state
沿用該fold seed；沒有為了分數重試seed。SVM probability=False，決策margin
不是機率，不偽造confidence或logits。

選擇依3fold known-validation macro-F1平均，其次balanced accuracy平均，
1e-12同分則linear→SVM→ExtraTrees。每類recall/confusion與fold表現逐列保存，
不僅報最好一fold。係數/樹importance可以描述特徵關聯，非故障因果解釋；
RBF SVM也不能冒稱白盒物理模型。

[Cortes與Vapnik(1995), Machine Learning20:273–297](https://doi.org/10.1007/BF00994018)
提出support-vector networks；本工程使用sklearn多類別RBF實作，非論文完全重現。
[Geurts、Ernst與Wehenkel(2006), Machine Learning63:3–42](https://doi.org/10.1007/s10994-006-6226-1)
提出Extremely randomized trees，固定small registry避免大範圍搜尋。

限制：三份fold的train/validation都曾在別fold test曝光，且validation/calibration
共用。此比較只屬exploratory已曝光資料；即使validation分數提高也不證明新
motor/generalization可靠。detector仍由factory、known-onlycalibration/confidence.95
設定，不根據未知/歷史最差label調門檻。Mahalanobis仍正式預設。

```powershell
.\venv\Scripts\python.exe -m experiments.fault_type_model_selection --data-root data/formal_local --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --feature-audit output/fault_type_feature_audit/2026-10-01-01-04-50/feature_audit.json --prepare-only
# 先commit/push候選registry，再使用該檔執行，不能重生registry後改選擇規則
.\venv\Scripts\python.exe -m experiments.fault_type_model_selection --data-root data/formal_local --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --feature-audit output/fault_type_feature_audit/2026-10-01-01-04-50/feature_audit.json --registry output/fault_type_model_selection/2026-10-01-01-18-13/candidate_registry.json
```

輸出selection_report、locked_config、fit/calibration audit gzip與3fold training
joblib（大型衍生artifact存D槽archive，Git存SHA索引）。locked之後才可做已曝光
test再分析；沒有合格freshfinal，正式独立驗證仍未完成。

## 實際 known-validation 結果（01:19:31–01:19:37）

| 模型 | 3fold macro-F1平均 | balanced accuracy平均 |
|---|---:|---:|
| 原linear | .188776 |22.5878%|
| RBF SVM | .156778 |21.9895%|
| ExtraTrees | .236452 |31.9710%|

按預登錄criterion選ExtraTrees：macro-F1增加.047676，balanced accuracy
增加9.3832百分點。三fold ExtraTrees的macro-F1為.285909/.201712/.221735，
linear為.144396/.170760/.251172；最後一fold ExtraTrees反而較低。
不是每fold改善，也不能把選擇集表現當unbiased final test。

已保存3份selected/baseline classifier+scaler+2detectors的training joblib，
實際參數與各input IDs、calibrationaudit、registry與checksum lock。
Locked checksum c39437ab92b74ea31c94a220bfd2e3cbc83a91f3670c1a7246b45dc81493b5c5。
未更改正式classifier/default detector；ExtraTrees只在獨立研究入口成為候選優勝，
尚不是production升級。接續比較原test需明確exploratory opt-in，不能據結果重選。
