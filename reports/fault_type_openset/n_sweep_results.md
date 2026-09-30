# Known fault configurations 數量 N：實際趨勢與限制

2026-09-30 20:12:22 完成 remaining sweep：1014/1014 runs、0 failed，
507 個相同 manifest／test IDs 的 detector pairs，unmatched=0。
加上先前全枚舉 N=5 的 756 runs，Protocol A 合計 1770 次、885 pairs。
每個組合都有三個預先登錄的 campaign folds（seed 42、123、2026）。

N=1、8：各全部九組；N=2、3、4、6、7：各固定 balanced30 組；
N=5：全部 126 組；N=9：全部一組、只作 closed-set baseline。
每種 detector 的 runs 數依序為 27、90、90、90、378、90、90、27、3。
所有組合與設定在正式結果檢視前登錄，未依結果換 seed／模型／門檻。

## Equal-run macro

accuracy 含 healthy＋N faulty known classes。兩方法共用分類器，所以
accuracy 完全相同。方括號為 nominal 95% Student-t intervals；**高度
相關的組合／folds 只容許描述性解讀，不是獨立馬達母體的信賴保證**。

| N | Known accuracy % [nominal interval] | AUROC Mahalanobis | AUROC k-NN |
|---:|---:|---:|---:|
| 1 | 69.35 [63.31,75.40] | 0.6019 | 0.6086 |
| 2 | 47.58 [45.26,49.89] | 0.5552 | 0.5566 |
| 3 | 36.72 [34.70,38.73] | 0.5382 | 0.5362 |
| 4 | 29.55 [27.95,31.15] | 0.5313 | 0.5208 |
| 5 | 25.74 [25.00,26.49] | 0.5277 | 0.5245 |
| 6 | 22.33 [20.97,23.68] | 0.5227 | 0.5207 |
| 7 | 20.47 [19.18,21.76] | 0.5221 | 0.5210 |
| 8 | 18.54 [16.23,20.85] | 0.5193 | 0.5216 |
| 9 | 16.44 [2.26,30.63] | unavailable | unavailable |

| N | Unknown recall M % | Unknown recall k-NN % | Healthy FPR M % | Healthy FPR k-NN % |
|---:|---:|---:|---:|---:|
| 1 | 39.899 | 26.138 | 16.327 | 8.112 |
| 2 | 26.227 | 18.078 | 10.996 | 5.791 |
| 3 | 20.982 | 12.208 | 6.495 | 4.306 |
| 4 | 17.166 | 9.738 | 3.642 | 2.502 |
| 5 | 14.995 | 7.943 | 2.259 | 1.268 |
| 6 | 13.390 | 6.334 | 1.610 | 0.688 |
| 7 | 11.972 | 5.893 | 0.423 | 0.218 |
| 8 | 10.807 | 4.734 | 0.011 | 0.053 |
| 9 | unavailable | unavailable | 0.000 | 0.034 |

M = Mahalanobis + Ledoit–Wolf。N=9 沒有 unknown positives，AUROC、AUPR、
FPR95、unknown F1/recall 均 unavailable/null，不是 0，也不是完美拒絕。
N=9 只有三個 campaign folds，區間很寬；它是 empirical closed-set baseline，
不是已證明可以達到高準確率的「上限」。

## 直接回答趨勢，不作過度歸因

1. 本固定 baseline 隨 N 增加，已知分類 accuracy 單調下降，unknown AUROC
   從約 .60 降至約 .52，未知 recall 也下降。N=5/更高 N 都不可靠。
2. accuracy 任務從二類變十類，chance baseline 與難度也改變；不同 N
   的 known/unknown 集合及 scaler/classifier/reference fit 都改變。
   不能只看 accuracy 差值就宣稱加入已知資料造成模型品質退步，更不能作因果結論。
3. Detector 接受任一已知類別區域即接受樣本；已知參考區域增加可能覆蓋
   更多未知配置。觀察到健康誤報與未知召回一起下降，符合「較少拒絕」的
   現象，但不能單靠此結果證明唯一成因就是接受區域擴張。
4. Mahalanobis 在本次 N=1…8 平均 unknown recall 均高於 k-NN；AUROC
   排名隨 N 改變，沒有在全部條件下都更好的方法。N=8 的健康 FPR
   甚至是 Mahalanobis 更低，不能概括宣稱 k-NN 永遠更安全。
5. 所有 1770 Protocol A runs 的 manifests 都 INCOMPLETE。僅三個 coarse
   campaigns、共用 validation/calibration、raw provenance 缺失，不能支持
   完整獨立物理馬達或不同故障機制泛化宣稱。沒有 test-based tuning。

## 可稽核證據

- Remaining-sweep model/manifest commit：`3d8b9f02269ad1eb030f45c34e3a20612b1d7f77`。
- Matrix：`output/fault_type_matrix/2026-09-30-19-37-27/`；16 個
  protocol/N/detector 分層 aggregate 包含 macro mean/SD/CI、pooled metrics、
  confusion matrices、per-unknown-label 與 matched-pair deltas。
- Combined report：`output/fault_type_report/2026-09-30-23-49-34/`；
  `results_table.csv` 含完整 AUROC 等各指標區間與 pooled rates，
  `paired_by_protocol_and_N.json` 將 A/B 與 N 完全分開，`known_fault_sweep.png`
  顯示三種主要趨勢（已檢視確認標籤／陰影／N=9 unavailable 正確）。
- Complete ZIP64：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30\fault_type_2026-09-30-19-37-27.zip`。
- ZIP：4,691,045,317 bytes、3570 files、CRC PASS、SHA-256
  `64ad06dac8625e838a6df251b247d7bc295837f602a3a7f9c2d98ceeea36377b`。
- Feature ablation 明確 skipped：目前只有正式 105-D features，沒有可用的
  neural embedding pipeline/artifact；未杜撰比較。
