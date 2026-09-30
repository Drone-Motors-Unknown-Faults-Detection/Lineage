# Protocol B：unknown-validation 輪替（次要、探索性結果）

2026-09-30 20:03:50 完成，720/720 runs、0 failed；30 組預先登錄的
balanced class combinations ×4 unknown-validation label 輪替 ×3 campaign
folds ×2 detectors。每種方法 360 runs、3,121,529 筆重複來源預測，
360 組相同 manifest 的 detector 配對，unmatched=0。

每次為 healthy+5 known faults、1 unknown-validation fault、3 unknown-test
faults。unknown-validation 只提供 diagnostic scores/recall；本次兩個固定
detectors 都不使用它 fit、選模型或調 threshold。unknown-test labels
與 unknown-validation 不重疊，未知測試資料未進入任何 fit/calibration。

## Equal-run macro 實測

| 指標 | Mahalanobis + Ledoit–Wolf | k-NN |
|---|---:|---:|
| Known accuracy | 25.262% | 25.262% |
| Known balanced accuracy | 25.315% | 25.315% |
| Known macro-F1 | 0.19887 | 0.19887 |
| Unknown-positive AUROC | 0.52884 | 0.52219 |
| Unknown recall（score > 1）| 14.536% | 7.383% |
| Unknown F1 | 0.15353 | 0.10034 |
| FPR@95TPR | 90.286% | 91.496% |
| Healthy FPR | 2.721% | 1.027% |

Known accuracy 的 nominal 95% interval 為 [24.543%,25.982%]；
AUROC 為 Mahalanobis [0.52130,0.53637]、k-NN [0.51347,0.53090]。
所有 SD、CI、pooled-sample 結果與 confusion matrices 保存在兩個
`aggregate_B_n5_*.json`，不是只保存上述平均值。

配對差值方向 k-NN − Mahalanobis：AUROC −0.006650，nominal CI
[−0.012535,−0.000764]；unknown recall −7.153 個百分點，interval
[−8.478,−5.828]；healthy FPR −1.693 個百分點，interval
[−2.605,−0.782]。這些區間只是高度相關組合／輪替／campaign folds
的描述性 Student-t intervals，不是獨立馬達的統計顯著性證據。

## 可解讀與不能宣稱的事項

- 兩種方法的未知排序接近隨機，未知漏拒很多；不能稱可靠。
- 全部 720 runs 的 manifests 均 INCOMPLETE：test 每類只有一個 coarse
  campaign、validation/calibration 共用，物理馬達與 raw-window interval 缺失。
- A 使用 126 組，B 使用預先登錄的 30 組；unknown-test label 集合也不同。
  A/B 平均數差異不是 unknown-validation 改善幅度，不能混合平均或當配對比較。
- B 設計允許另外的 unknown-validation role，但目前方法並未使用它調門檻；
  因此沒有宣稱 unknown-aware tuning 成效，也沒有事後更換主要 Protocol A 方法。

## 證據與保存

- 模型與不可變 manifest code commit：`3d8b9f02269ad1eb030f45c34e3a20612b1d7f77`。
- Registry：`class_roles_v1_6bdff74614f1d781.json`。
- Dataset fingerprint：`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。
- Matrix：`output/fault_type_matrix/2026-09-30-19-37-39/`。
- 日誌：`logs/fault_type_matrix/2026-09-30-19-37-39.log`。
- 完整 ZIP64：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-19-37-39.zip`。
- ZIP：3,375,246,908 bytes、2527 files、CRC PASS，SHA-256
  `24ec1e80346dcbc2d8244dfaa9c0cc2188788ae8eed0530d2fde3671b1e38f8f`。
- 原始工作檔未刪除；ZIP 包含逐樣本機率、fit audit、原始 manifests、逐 run
  metrics 與 BUNDLE_INDEX.json，不包含 raw/formal source data。
