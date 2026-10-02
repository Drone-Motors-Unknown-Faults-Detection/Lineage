# 單輪機制研究結案：平均取捨改善，不是可靠模型

2026-10-02 Asia/Taipei。完成診斷、17文獻候選/7篇方法深讀、三個假說、九個完整改編、81配對評估、780,570逐筆重新推論與truth-mutation檢查。正式105/Mahalanobis-LW/PolarMap未變，kNN仍factory可切換。

**VERIFIED**：固定無selector、train/cal/test馬達分離、unknown不fit/cal、所有81格成功、資料SHA未變、配對IDs相同、來源/模型/預測SHA與重新算指標一致。
**FAILED**：九個新方法均至少一個motor/RPM健康完整誤報>研究暫定10%；皆仍有零recall故障類；T1未知召回全0。沒有production替換或可靠部署依據。
**INCOMPLETE/UNKNOWN**：fresh final test不存在、每類至少兩獨立test groups不足；sessions/raw intervals/overlap/刪點/units/mount/load未知。不降guard，不把新lock當盲測。

## 比較結果（seed0三馬達等權；三seeds逐筆完全相同）

M為正式factory Mahalanobis-LW。分類是**拒絕前**結果；健康total包含accepted known fault與unknown，非舊unknown-FPR。F1非accuracy。

| 完整方法 | healthy+known acc % | fault-only acc % | fault macro-F1 | unknown AUROC | unknown recall % | 健康total alarm % | 最差RPM健康alarm % |
|---|---:|---:|---:|---:|---:|---:|---:|
| C02/M（歷史控制） | 34.15 | 26.61 | .240 | .5746 | 18.44 | 26.87 | 99.60 |
| C17/M（歷史控制） | 39.29 | 30.43 | .285 | .5756 | 8.44 | 14.13 | 100 |
| C24/M（歷史控制） | 32.17 | 30.91 | .287 | .5388 | 21.07 | 63.41 | 100 |
| D01：C17 + C02/M | 39.29 | 30.43 | .285 | .5746 | 18.44 | 14.13 | 100 |
| D02：C17 + C02/K5 | 39.29 | 30.43 | .285 | .5711 | 5.45 | 14.76 | 100 |
| D03：C24 + C02/M | 32.17 | 30.91 | .287 | .5746 | 18.44 | 61.40 | 100 |
| P01：RPM pooling β0 + C02/M | 32.51 | 29.71 | .255 | .5746 | 18.44 | 52.48 | 100 |
| P02：β.5 + C02/M | 25.99 | 18.94 | .186 | .5746 | 18.44 | 37.01 | 100 |
| P03：β1 + C02/M | 23.85 | 17.01 | .150 | .5746 | 18.44 | 40.35 | 100 |
| G01：C17 + block λ0 | 39.29 | 30.43 | .285 | .5294 | 3.50 | 20.10 | 100 |
| G02：C17 + block λ1 | 39.29 | 30.43 | .285 | .5864 | 8.15 | 30.83 | 100 |
| G03：block nearest + block λ0 | 33.71 | 26.98 | .247 | .5294 | 3.50 | 36.50 | 100 |

shape-only C18與R18全cov背景控制也列機器summary/tradeoff。没有只挑正面方法。
每motor/RPM/class、precision/recall/F1、confusion、AUPR/prevalence、FPR95、coverage、known rejection、逐seed實值、243個paired條件都在新summary。

## 較佳研究折衷 D01 的改善與代價

對C02/M：known acc +5.13 **percentage points**；fault-only +3.82pp；健康total alarm平均−12.74pp；unknown recall不變。
對C17/M：分類與健康total完全不變；unknown recall +10.00pp，8.44→18.44。
但known拒絕率4.94→12.82%，拒絕後known正確率39.26→36.79%；coverage93.69→85.00%。
unknown precision .362→.279，AUPR .4498→.4397；沒有全面Pareto dominance。
final open-set accuracy 27.14→29.54%，仍非常低；不是分類器fault acc變成29.54%。

| D01 test motor（samples；known/unknown；healthy） | known acc % | 2screws recall % | unknown recall % | 健康total % | 6000/8000/11000rpm unknown recall % | 同順序健康total % |
|---|---:|---:|---:|---:|---|---|
| T3：9294；5604/3690；886 | 40.65 | 0 | 8.40 | 0 | 0 / 0 / 25.18 | 0 / 0 / 0 |
| T1：9759；5935/3824；991 | 38.84 | 0 | 0 | 31.58 | 0 / 0 / 0 | 0 / 100 / 0 |
| T2：9857；6007/3850；945 | 38.37 | 0 | 46.91 | 10.79 | 0 / 54.15 / 80.23 | 0 / 4.62 / 33.60 |

因此D01只有7/9健康安全格通過，最差unknown motor=0%，最差known fault類=0%。不能稱全面最佳。
sample-weighted D01：known39.2568%、fault30.4333%、unknown18.6202%、health14.7059%、final29.5988%；與motor等權不同，不混用。
9motor/RPM等權 D01：known39.3072%、fault30.4963%、unknown17.7294%、health15.3574%。
AUROC/AP的sample-weighted為within-fold值加權平均；不同模型的raw尺度不混在一起排ROC。
三seeds全27個arm/fold條件的pred/score/threshold/reject values exact；沒有seed變異，更不是9顆新motor。

## 假說判定與負面结果

- H-D部分支持：分類與拒絕可解耦，D01逐筆等於C17 classifier/C02 detector，平均unknown提升不是classifier變好。競爭解釋仍成立：分數排序弱、cal transfer與健康分類錯誤没有解決。
- H-P「中間收縮優於兩端」未支持：P02 fault18.94%低於P01 29.71%，只在health平均減少，仍有100%最差格。P01的T1 2screws僅2.55%、T2 32.16%；C24對T2本已有63.92%。不把小恢復說成可信辨識。
- H-G未可靠改善：G02 AUROC較C17稍高，但recall更低、health30.83%；G03 2screws T3 .41%、T2 1.18%、T1 0%。三塊去交叉cov、每維等權可能丟有用相關，亦可能cal/motor shift比幾何重要；本輪不能分辨全部原因。
- 原C17 train 2screws皆100%、跨motor test皆0，支持domain/overfit解釋，不支持「train根本缺該類」。同RPM crossmotor位移比值大，無units/session證據不能說一定是老化或感測器改裝。
- R17 raw cal各類足量但predicted routes空，六歷史INCOMPLETE保留。不補零、不用oracle分組。

只有三motor、unknown raw依賴且test已曝光：不作逐窗IID bootstrap/窄CI；不算每小時警報、延遲、RUL或損壞百分比。
停止第二輪：沒有新的可分辨證據支持再掃β/λ/threshold，剩餘係數微調會是test shopping。
下一個有界假說可研究「train-only LMNN能否保留跨RPM局部margin」，但 solver/開發群組與固定預算需先驗證；**本輪未實作、未聲稱有效**，不要求不存在硬體。

## 方法来源、原式與改動定位

完整公式/控制/參數在 adaptation_cards；文獻閱讀深度在 source_ledger。
| 機制 | 原始來源／原式 | 本地改動／位置 | 實測判定 |
|---|---|---|---|
| D01–03新組合 | [Vaze et al.2022 ICLR](https://robots.ox.ac.uk/~vgg/publications/2022/Vaze22/) 為動機，不取未讀全文公式；原C17/C24 classifier、C02 factory | `fault_type_mechanism_study.infer`分離transform/classifier與detector；無重fit父方法 | D01平均折衷改善；health/class collapse未過gate |
| P01–03自改 | [Friedman1989 JASA](https://doi.org/10.1080/01621459.1989.10478752) pooling觀念＋[LW2004 JMVA](https://www.ledoit.net/Well-conditioned2004.pdf) covariance；Gaussian δ=zᵀPμ−½μᵀPμ | `RPMPartialPooling.fit/predict` mean及within-cov向global收縮β0/.5/1；不是原RDA RPM復刻 | 中間係數沒有勝過兩端；保留負面結果 |
| G01–03自改 | [Ren et al.2021 RMD](https://www.gatsby.ucl.ac.uk/~balaji/udl2021/accepted-papers/UDL2021-paper-007.pdf) d_c−d_0；本站C17幅值座標、LW | `BlockGeometry.fit/distances/score` 36/30/3三塊LW、每維平均、λ0/1；G03改nearest clf | 保留amplitude仍未可靠改善；不是原文忠實deepfeature重現 |

沒有試LMNN/SupCon/LogitNorm/OpenMax/DeepSVDD；沒有把NCA（原九次已收斂）改名或宣稱修復。raw methods因mapping/timing未知不適用，不以特徵列當時序。

## 老師建議的完成層級

| 要求 | 實際證據 | 判斷／限制 |
|---|---|---|
| healthy+5faulty作known，4faulty作unknown | 本輪固定主配置81格＋先前126組756runs歷史索引 | 工程/配置實測完成；可信辨識**未完成**，不是九個物理故障原因 |
| 隨機healthy+Nfaulty | 歷史N1–8/N9closed-set、ProtocolB、共2490runs保存結果 | 歷史已執行，本輪新法未重跑所有N/126；不得由runner支援推算完成 |
| 切分有依據、避免selection依賴 | 整motor LOMO方向、selection/validation空、專用known-cal、81audits/舊234parent audits、ID/SHA guards | 本輪程式用途/全域選模/val-cal共用問題已修；固定CV角色輪換不是洩漏 |
| 完整獨立test條件 | 每折僅一testmotor、全部rows歷史曝光、raw/session未知 | **部分完成/INCOMPLETE**；不洗牌變fresh、不降≥2groups；來源獨立性UNKNOWN |

T1/T2/T3文件支持三顆不同個體；T1新/T2T3老，但age與個體混雜。工程證據不補造采集事實。

## 證據與長期保存

authoritative report：`output/fault_type_mechanism_report/2026-10-02-17-58-59/summary.json`（gz小型入庫），seal `69e4b6d126dc1129ed2bceb0c1ff6621a946a263496bc72c1f859bbe9a6f40a8`。
protocol ff6ddc29…；lock c1d47ead…；evaluation2ff6fdca…；verification1ff5c7fd…；完整SHA/絕對路徑在結果索引。
formal與舊manifest/predictions/models未覆寫。checkpoint總索引resume bug在test前有重現測試並版本化修正；初9fit保留，正式81只用新版本。
先前282 tracked deletions保留。tests/commits/push與備份驗證詳execution_log與delivery。
新的D槽包、SHA/CRC/member校验結果隨delivery/index列出；单D磁碟備份不是offsite。

最終工程驗收：Python 3.10.19／3.14.6各349 tests通過（0失敗）、pip check通過、28個CLI help通過。兩份acceptance在18:00:37／18:00:48。
研究備份：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-02\mechanism_research_v2`，14個新ZIP、301個來源檔、480,240,398 bytes，全包SHA／CRC／member SHA通過；舊8包未改。模型與原始逐樣本結果不直接入Git。
工程流程VERIFIED；研究健康安全gate FAILED，獨立final-test資格INCOMPLETE，session／raw視窗／設備一致性UNKNOWN。不得以完成349 tests或81評估代表部署可靠。
