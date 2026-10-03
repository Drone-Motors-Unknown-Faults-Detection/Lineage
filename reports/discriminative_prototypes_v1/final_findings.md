# 實驗15：原型loss與模糊拒絕實測

2026-10-03，Asia/Taipei。216／216格完成、模型失敗0格，逐筆重推與truth mutation通過。24方法均未通過原reliability CONTRACT，尚未找到R2可靠提升；正式105維／linear／Mahalanobis-LW、k-NN factory切換與PolarMap均未改。

## 新方法與資料範圍

Sato／Yamada GLVQ的有限適配：固定β=4的平均sigmoid相對距離loss、批次L-BFGS-B、ε=1e-12；新增本站anchor λ=.01作配對。全部known train初始化每類1個平均或3個KMeans中心，loss只用既有train分層子集。identity harmonic69／已收斂hard600對角幾何，static／GLVQ／anchored，共12分類器；每個配C02/M與原型模糊拒絕，24方法×3fold×3seed=216格。原文與改編公式、解析導數、作者工具差異見[先行手冊](../../docs/experiments/exp15_discriminative_prototypes.md)。新增依賴0。

healthy=8screws，known faulty=1screws／2screws／3_14screws／3screws／4screws，unknown=4_146screws／5screws／6screws／7screws。train/cal/test=T1/T2/T3、T2/T3/T1、T3/T1/T2；seeds0／1／2，9個motor×RPM工況。無validation／selector、unknown不fit／cal。108模型（36static、72最佳化）全完成、72最佳化全收斂；train/cal來源全部108模型重建，test_numeric_reads=0。

2,081,520筆預測來自28,910個unique rows／90CSV，不增加獨立motor或採集次數。正式fingerprint仍 `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`，來源SHA前後不變。所有樣本已有歷史test曝露，僅一組known subset初篩；沒有重跑全部126組或2,490歷史runs。

## 配對結果

以下均為seed0的三motor等權平均。accuracy只看raw classifier的true known faulty，兩detectors相同是共用分類器的預期行為；完整final分母F1另列機器報告，不能混稱分類改善。

| 分類器（C02/M arm） | 故障accuracy % | conditional fault F1 | 完整健康誤報 % | 三seed故障accuracy % |
|---|---:|---:|---:|---|
| C17基準 | 30.432 | .285191 | 14.126 | 見歷史鎖定控制 |
| G01 identity／1／static | 30.366 | .260646 | 42.635 | 30.366／30.366／30.366 |
| G03 identity／1／GLVQ | 27.492 | .233048 | 32.822 | 27.492／30.761／29.040 |
| G05 identity／1／anchor | 27.559 | .234499 | 32.857 | 27.559／30.825／29.039 |
| G07 identity／3／static | 26.659 | .255057 | 19.293 | 26.659／26.659／26.659 |
| G09 identity／3／GLVQ | 28.058 | .269568 | 18.840 | 28.058／29.722／27.193 |
| G11 identity／3／anchor | 28.038 | .269403 | 18.840 | 28.038／29.655／27.234 |
| G13 hard600／1／static | 25.504 | .190424 | 17.272 | 25.504／31.312／37.111 |
| G15 hard600／1／GLVQ | 26.637 | .207072 | 8.924 | 26.637／20.148／25.680 |
| G17 hard600／1／anchor | 26.670 | .207416 | 8.924 | 26.670／20.188／25.644 |
| G19 hard600／3／static | 26.657 | .216842 | 22.769 | 26.657／24.737／23.456 |
| G21 hard600／3／GLVQ | 24.857 | .205656 | 21.516 | 24.857／25.880／22.589 |
| G23 hard600／3／anchor | 24.857 | .205656 | 21.516 | 24.857／25.880／22.589 |

H15a只得到局部支持：identity單中心更新−2.873pp，identity三中心更新+1.399pp；hard600單中心+1.133pp、三中心−1.800pp。不支持「只要移動原型就會可靠改善」。anchor相對GLVQ的差值多很小，未得到一致穩健提升。沒有挑G13 seed2的37.111%作主成績。

所有C02/M支線未知召回18.437%，T1仍0%。模糊拒絕支線如下，與同分類器C02/M配對：

| 模糊arm | unknown recall % | 完整健康誤報 % | 全樣本final fault F1 |
|---|---:|---:|---:|
| G02 | 8.804 | 45.175 | .206284 |
| G04 | 4.033 | 33.870 | .189534 |
| G06 | 3.780 | 33.870 | .189509 |
| G08 | 6.508 | 19.535 | .209654 |
| G10 | 6.375 | 19.051 | .215556 |
| G12 | 6.298 | 19.086 | .215603 |
| G14 | 14.166 | 18.175 | .180974 |
| G16 | 20.225 | 8.924 | .164150 |
| G18 | 20.363 | 8.924 | .163443 |
| G20 | 9.152 | 23.689 | .195414 |
| G22 | 11.150 | 23.509 | .180597 |
| G24 | 11.160 | 23.509 | .180561 |

## T1與最差工況，不能只報平均

G16的T1 unknown recall三seed為16.579%／2.197%／9.074%；AUROC .557034／.557085／.583862；known-cal門檻 .962681／.972578／.987784。G18為17.259%／2.144%／8.944%。相較C02/M的0%有可重現局部增益，但後兩seed仍低於既有motor floor .10。門檻只由known calibration定義，沒有用T1掃quantile。

G16 seed0各motor：

| test motor | faulty accuracy % | unknown recall % | 完整健康誤報 % | 2screws recall % |
|---|---:|---:|---:|---:|
| T3 | 31.306 | 2.276 | 0 | 0 |
| T1 | 25.769 | 16.579 | 0 | 0 |
| T2 | 22.837 | 41.818 | 26.772 | 31.275 |

G16的T2／6000、8000、11000 RPM健康完整誤報為0%／0%／100%，三seed都如此。平均8.924%低於10%並不滿足「每個motor／RPM」健康保護。所有24方法的最差RPM健康誤報皆為100%，最差known fault class recall皆為0%。有些GLVQ恢復T3或T2的2screws召回，但T1仍零；其他類別亦有崩潰。全部FAILED，B多配置／壓力測試與C獨立final驗證未完成。

分數與label mapping、strict >、threshold、finite values及逐筆模型推論經verify一致，沒有發現能靠修報表解決的T1工程bug。支持的解釋：loss與幾何改變會影響類別邊界，模糊分數捕捉部分未知但未穩定區分全部工況。motor domain shift、配置特徵重疊與calibration transfer仍是競爭解釋；現有結果不證明某一項為唯一物理原因。T1新／T2T3老的個體與老化混雜不變。

## 驗收與老師建議

- VERIFIED：本批108模型數值來源、用途分離、無selector、216格逐筆重推／truth mutation、1,296組配對差值及6ZIP／468members的whole/member SHA與CRC。
- FAILED：24方法全部可靠提升主篩；分類、最弱類、unknown非劣或最差工況健康保護未達要求。
- INCOMPLETE：本輪多known subsets／壓力驗證及每類至少兩獨立test groups；fresh final仍無。
- UNKNOWN：raw錄製邊界／session／視窗重疊／刪點遮罩／安裝與負載等來源事實。

老師問題1部分完成：healthy＋5known／4unknown本批確有實測，其他N及126組的歷史成果保留，本批未重跑；螺絲配置不冒稱9種已確認物理故障。問題2部分完成：用途洩漏與共同選擇依賴可驗證排除，校準專用另一motor；來源群組、少量獨立motor與test曝露無法由新seed修復。

## 測試、提交與重現

實驗15的15項小測試／native合成smoke成功；其先行完整驗收兩環境各452項通過。新增實驗16核心12項後，Python3.10.19／3.14.6完整驗收各464通過、失敗0（58.290／59.537秒），pip check及37個歷史CLI成功；實驗13至16 CLI／smoke另列，不冒稱在37項內。實驗16後加8項來源測試各20小測試通過，其新的全套驗收待下一階段，不回填464產物。

程式／手冊 `8cfe68f`；協定 `8927918`；fit與source `64b6f88`；均commit+push且當時remote SHA一致。實驗16核心 `85a35f9`為獨立提交，沒有改本批sealed程式。結果提交SHA看execution log／Git歷史，不能將尚未提交寫成已push。

`result_index.json`保存protocol／lock／source／evaluation／verification／report與備份路徑、seals。重現順序為 `python -m experiments.fault_type_discriminative_prototypes fit/source-verify/evaluate/verify/report`，實際參數見execution log與先行手冊；native `.venv310/Scripts/python.exe`，資料 `data/formal_local`。D槽只是一個磁碟備份，不稱異地備份；父harmonic69／hard600／C02 models與既有manifests仍為必要依賴。

下一批平滑L1已事前寫手冊與核心驗證，runner仍在實作。α=20沿原文；沒有用G16局部test改善去改本批threshold或挑seed。之後需要另外封存新protocol、擬合、來源重建及配對實測。
