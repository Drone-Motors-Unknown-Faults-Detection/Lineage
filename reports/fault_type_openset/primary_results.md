# N=5 全枚舉結果：目前基線尚不可靠

完成 Protocol A 全部 126 組 healthy+5 known 對 4 unknown，三個 campaign
fold（seed 42/123/2026），兩個 detector，共 756 次執行，失敗 0 次。
每種方法有 378 runs、3,642,660 筆預測；相同來源會在不同組合重複
評估，不是 364 萬次獨立採集。

全部切分皆為 INCOMPLETE：每類只有一個 test campaign、validation
與 calibration 共用，而且 physical motor/session/raw-window interval
等 metadata 缺失。以下是探索性跨 campaign 結果，不能當成完整獨立
馬達測試的主要結論，更不能宣稱可靠辨識未知物理故障類型。

## 實測總表（equal-run macro）

| 指標 | Mahalanobis + Ledoit–Wolf | k-NN |
|---|---:|---:|
| Known accuracy | 25.744% | 25.744% |
| Known balanced accuracy | 25.805% | 25.805% |
| Known macro-F1 | 0.20219 | 0.20219 |
| Fault-only classification accuracy | 23.714% | 23.714% |
| Unknown-positive AUROC | 0.52775 | 0.52448 |
| Unknown recall（score > 1）| 14.995% | 7.943% |
| Unknown F1 | 0.17235 | 0.11332 |
| FPR@95TPR | 91.104% | 92.661% |
| Healthy FPR | 2.259% | 1.268% |

分類器完全相同，所以切換 detector 不會改變 closed-set accuracy。
兩種 unknown AUROC 都接近隨機判別的 .5；FPR95 很高、未知召回率很低。
健康誤報低並不代表偵測整體良好，也可能因接受區域過寬而漏掉未知配置。

## 同 manifest 配對比較

差值方向 k-NN − Mahalanobis，共 378 pairs：

- AUROC −0.003266，nominal CI [−0.008323, +0.001792]；不能宣稱明確優勝。
- Unknown recall −7.052 個百分點，nominal CI [−8.271, −5.832]。
- Unknown F1 −0.059030，nominal CI [−0.070387, −0.047673]。
- Healthy FPR −0.991 個百分點，nominal CI [−1.757, −0.225]。

這些 Student-t intervals 是相關組合／fold 的描述性區間，不是獨立
馬達母體的有效信賴保證。Mahalanobis 比較能拒未知；k-NN 健康誤報
較低，但此基線兩者都不能稱「可靠」。保留原本 Mahalanobis 預設，
沒有根據 test scores 改演算法、挑 seed 或調 threshold。

## 已知／未知困難配置與工況

- 最難分類的 known：2screws，兩方法相同 classifier，平均 recall
  6.537%（210 known-role runs）。
- Mahalanobis 最難拒絕：4screws，平均 recall 4.216%（168 unknown-role
  runs）；跨組合合計最常吸引它的已知參考配置為 3screws。
- k-NN 最難拒絕：7screws，平均 recall 1.533%（168 unknown-role runs）；
  合計最常吸引它的已知參考配置為 4_146screws。
- 同為 1screws、11000rpm 的 known-role pooled classification：test
  campaign 1 為 13.332%，campaign 2 為 84.470%。顯示跨 fold 差異很大。
  每折的 train/calibration 也同時改變，因此不能把差異直接因果歸因
  於馬達身分、壽命、轉速或某個具體物理原因。

可能的解釋（尚非已證實的因果）：九個 labels 是同一螺絲鬆動機制的
配置，而不是九種不同故障機制；known/unknown 特徵區域可能重疊。
跨階段分布變動可能影響分類與校準；已知 calibration 很寬時，距離
分位數門檻可使未知配置被接受。必須進一步稽核 sensor orientation、
實際馬達/session、工況、原始來源與 105-D 特徵的跨階段語意一致性。
本次結果本身不證明是哪一項造成，也不證明其他分類器必然無法改善。

## 完整證據與保存

- 模型/manifest commit：`dd7f679ec498d9836e7f3c2aeb355322776c158b`。
- Matrix：`output/fault_type_matrix/2026-09-30-19-05-42/`。
- 報告：`output/fault_type_report/2026-09-30-19-32-34/`，包含全部 SD/CI/
  pooled rates、per-class、逐 N 配對、RPM/campaign 分析。
- 所有原始逐樣本機率、fit audit、manifest、逐 run metrics 已保存。
- Pooled task-N 描述修正由 code review 發現，僅區分 per-run N=5 與
  九標籤聯集，數值指標、原始預測、不可變 manifests 均未變動；
  `pooled_metadata_migration.json` 留有修改前／後摘要檔 hash。
- 完整 ZIP64 已保存到
  `D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-19-05-42.zip`，
  3,712,231,384 bytes，2654 files，CRC PASS，SHA-256
  `25fc12c6982143f72fdf8c5534837dcd4767ba98ab106af39bdbb10eacb3d540`。
  原始工作檔沒有刪除。Raw/formal feature source data 不在 ZIP 中。

N-sweep 與 Protocol B 將依預先登錄接續執行、分表呈現，不用這份
N=5 test 結果回頭選模型／閾值／組合。
