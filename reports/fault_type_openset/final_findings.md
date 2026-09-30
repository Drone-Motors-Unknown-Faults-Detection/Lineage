# 老師建議完成度與目前問題：完整研究回報

> 2026-10-01 更正：本文第3節「不是三顆已驗證不同馬達」過度否定文件證據，
> 已撤回。固定版本文件支持三顆不同個體；經路徑核對可解讀 documented LOMO。
> 身分、採集來源鏈、獨立測試完整度是不同層次。詳見 provenance_followup.md；
> 舊 immutable artifacts／數字與 INCOMPLETE 狀態不改寫。

結論：要求的 class-role／group-aware split、不可變 manifests、validator、
多類別 classifier、兩種 factory detectors、N=5、N-sweep 與 Protocol B
已實作並實際完成運算。2490/2490 detector runs 完成、0 failed，137 tests
通過。但**可信 fault-type 模型尚未被證明，完整獨立測試資料仍不足**。
全部現有研究切分為 INCOMPLETE，只能報告探索性 fault-configuration 結果。
這是負面研究發現，不是以「程式不 crash」替代有效性證據。

## 1. 老師兩個問題的直接答案

| 老師要求 | 工程／執行狀態 | 研究答案 |
|---|---|---|
| healthy+5 known faults，另4類 unknown | 已完成全部126組×3folds×2detectors，756 runs | 已知 accuracy 25.744%，unknown AUROC 約 .52，尚不可靠 |
| healthy+N faults，改變 N 驗證 | 已完成 N=1…8；N=9另列closed-set | N增加時本baseline分類／拒未知整體變弱，非簡單因果證明 |
| train/validation/calibration/test 切分要有依據 | 已按資料稽核採整個campaign留出，不隨機拆相鄰列 | 可重現且沒有已知fit/test混用，但無法證明物理馬達獨立 |
| 定義「測試切分不完整」並自動檢查 | 已完成15個required error codes及語意測試 | 本資料全部INCOMPLETE，不能宣稱已取得完整獨立測試 |

「有1 healthy＋9 faulty」代表可以設計這個任務，不代表九類有可分的
物理機制、105-D 特徵一定能跨採集泛化，或已有足夠獨立測試 groups。

## 2. 實際 labels、數量與物理語意

90 個 clean CSV、28,910 個有限值105-D windows；每label九檔，
三個campaign×三個RPM（6000/8000/11000）。

| Label | Windows | 本次語意 |
|---|---:|---|
| 8screws | 2822 | healthy |
| 7screws | 2637 | 螺絲固定／鬆動數量配置 |
| 6screws | 2876 | 同上 |
| 5screws | 2890 | 同上 |
| 4screws | 2803 | 同上 |
| 3screws | 2929 | 同上 |
| 2screws | 2985 | 同上 |
| 1screws | 2986 | 同上 |
| 3_14screws | 3021 | 數量＋位置配置 |
| 4_146screws | 2961 | 數量＋位置配置 |

九類主要是同一螺絲鬆動機制的 configurations，不是九種已驗證 fault
causes，也不是經扭力量測校準的 severity。最大／最小類樣本量比約1.15，
不能把低準確率只歸因於嚴重class imbalance。沒有事件數資訊；unknown
overlap/event counts 不等於0。

## 3. 最終 class-role 與 group-aware sample split

Class-role 先決定：healthy永遠known；A的N=5有5 known faulty／4 unknown
test，未知labels只在final test。B另有1 unknown-validation、3 unknown-test，
角色labels互斥；四種unknown-validation label輪替，只作diagnostic，不fit門檻。

Class-combination seed=42；sample seeds=42/123/2026，分別绑定以下folds：

| Seed | Train campaign | Validation/calibration | Test campaign |
|---:|---:|---:|---:|
| 42 | 1 | 2 | 3 |
| 123 | 2 | 3 | 1 |
| 2026 | 3 | 1 | 2 |

因verified motor/session/run缺失，採最粗可用的stage/T-code campaign；每
source CSV整組保留，未知labels的非test campaigns明確excluded並記理由。
這不是三顆已驗證不同馬達，三個seeds也不是三次新增獨立採集。
Scalers/classifier/reference/covariance只fit train；threshold只fit known
calibration；validation只diagnostic，本次沒有超參數搜尋。未用test選模型。

## 4. 測試切分不完整的正式定義與本次狀態

PASS：宣稱所需類別、樣本／groups／工況／可得追溯檢查都通過，且無
已知洩漏；不等於可證明未被紀錄的物理獨立性。

INCOMPLETE：缺預定類別或工況、test每類少於30windows／2acquisition
groups、validation/calibration共用、故障語意不足或需要卻沒有event邊界。
30windows是診斷門檻而非power analysis，不能稱30個獨立觀察。

INVALID：group／raw interval重疊洩漏、unknown-test進fit/calibration、test
被用於selection、配對manifest不同、未聲明排除或checksum/provenance失效。
會在fitting前fail fast，不進正式結果表。

Required codes：TEST_MISSING_HEALTHY、TEST_MISSING_KNOWN_CLASS、
TEST_MISSING_UNKNOWN_CLASS、TEST_INSUFFICIENT_SAMPLES、
TEST_INSUFFICIENT_GROUPS、TEST_CONDITION_COVERAGE_INCOMPLETE、
TEST_GROUP_LEAKAGE、TEST_WINDOW_OVERLAP_LEAKAGE、UNKNOWN_LABEL_LEAKAGE、
TEST_MANIFEST_MISMATCH、TEST_USED_FOR_SELECTION、TEST_EXCLUSION_UNDECLARED、
TEST_NOT_REPRODUCIBLE、LABEL_SEMANTICS_MISMATCH、EVENT_BOUNDARY_INCOMPLETE。

| Matrix | 完成／宣告 | Failed/pending | Validator |
|---|---:|---:|---|
| A N=5 全126組 | 756/756 | 0 | 全部INCOMPLETE |
| A remaining N-sweep | 1014/1014 | 0 | 全部INCOMPLETE |
| B N=5 輪替 | 720/720 | 0 | 全部INCOMPLETE |

直接觸發原因為每類只有一個test campaign與shared validation/calibration。
Missing raw intervals等另外保留warnings。沒有已知洩漏，不等於已證明
所有原始windows完全獨立；目前不能把任一研究run標成PASS。

## 5. N=5 known classification 與 unknown rejection

Train-only RobustScaler＋balanced multinomial logistic regression，C=1、
lbfgs、max_iter=1000；非收斂則failed。兩detectors走core.openset factory；
固定Mahalanobis/Ledoit–Wolf、k-NN k=5、known-only confidence=.95。

| Equal-run macro 指標 | Mahalanobis | k-NN |
|---|---:|---:|
| Known accuracy | 25.744% | 25.744% |
| Known balanced accuracy | 25.805% | 25.805% |
| Known macro-F1 | .20219 | .20219 |
| Fault-only accuracy | 23.714% | 23.714% |
| Unknown-positive AUROC | .52775 | .52448 |
| Unknown recall（score>1）| 14.995% | 7.943% |
| Unknown F1 | .17235 | .11332 |
| FPR@95TPR | 91.104% | 92.661% |
| Healthy false-positive rate | 2.259% | 1.268% |

Known accuracy nominal interval [25.00%,26.49%]；AUROC intervals分別
[.52062,.53487]、[.51721,.53175]。兩方法共用classifier，因此closed-set
accuracy不會因detector切換而提高。低健康誤報不能掩蓋大量未知漏拒。
每方法378runs／3,642,660筆repeated predictions，不是364萬次獨立採集。

## 6. N-sweep 趨勢與不確定性

詳細表含mean/SD/nominal CI/pooled，見n_sweep_results.md與combined CSV。
N=1→5→8的known accuracy為69.35%→25.74%→18.54%；Mahalanobis
unknown AUROC .6019→.5277→.5193，unknown recall39.90%→14.99%→10.81%。
k-NN AUROC .6086→.5245→.5216，recall26.14%→7.94%→4.73%。
N=9十類closed-set accuracy16.44%，只有三folds，nominal interval
[2.26%,30.63%]；unknown-positive各指標 unavailable/null，不能填0。

類別數／held-out labels／fit distributions一起改變，chance level也不同，
所以這不是N的單一因果實驗。區間只描述相關組合與campaign folds；
不能當作獨立馬達母體的有效95%信賴保證。所有runs均保留，未挑最佳seed。

## 7. Mahalanobis 與 k-NN paired comparison

A共885pairs，B共360pairs；合計1245pairs，均相同manifest與test IDs，
unmatched=0。比較方向k-NN−Mahalanobis；分A/B、分N，不混合平均。

Primary A N=5：AUROC−.003266，nominal interval[−.008323,+.001792]；
unknown recall−7.052百分點[−8.271,−5.832]；healthy FPR−.991百分點
[−1.757,−.225]。AUROC差值不能支持明確優勝，且兩者都不可靠。

B單獨結果：known accuracy25.262%，unknown AUROC .52884/.52219，
unknown recall14.536%/7.383%，healthy FPR2.721%/1.027%。B使用balanced30
而A全126，unknown labels亦不同，A/B平均數差異不是unknown-validation
tuning改善。B目前未以unknown-validation調門檻。

Mahalanobis維持預設，未依test選方法。Ledoit/Wolf(2004,J.Multivariate
Analysis)與k-NN OOD研究／本專案逐類5鄰居工程特徵變體差異，見
method_sources.md；沒有冒稱Deep Nearest Neighbors論文原樣重現。

## 8. 最難known／unknown與工況差異

Primary N=5：最難known為2screws，平均recall6.537%；Mahalanobis最難
unknown為4screws，recall4.216%，合計最常被3screws吸引；k-NN最難
unknown為7screws，recall1.533%，合計最常被4_146screws吸引。

同為1screws/11000rpm的known pooled classification：test campaign1
13.332%、campaign2 84.470%。Train/calibration也隨fold改變，不能把
差異直接歸因於馬達ID、壽命或某個感測物理因素。

## 9. 已遇到的問題、支持的結論與不能宣稱的事項

1. **模型效能不足：未解決。** 現有固定baseline難以分類known與拒unknown。
   可能有配置特徵重疊、linear classifier限制、跨campaign分布變化或
   calibration接受區域過宽；這些是待驗證假說，不是已找出的唯一原因。
2. **標籤語意：已澄清、不能誇大。** 九配置不等於九種物理故障機制。
3. **物理獨立性與完整測試：外部資料阻擋。** 缺verified motor/session/run、
   raw-window intervals/stride、日期、負載／溫度、事件邊界；每類test只有
   一campaign。不得宣稱完整獨立測試、真實磨損趨勢或每小時事件誤報。
4. **跨stage特徵語意：仍需來源稽核。** Stage2從raw重建，Stage1/3沿用
   clean features；23個header文字差異，以105個位置契約讀取。這能避免
   依文字錯接欄位，不能證明原始sensor方向／物理特徵全部等價。
5. **環境不一致：已記錄、跨版本驗證未完成。** 實跑Python3.14.6，專案
   宣告3.10.19，不能聲稱3.10也測過。缺失venv來源檔已用同版本修復。
6. **Worktree缺歷史檔：仍存在。** 282個既有tracked deletions原因未知；
   未stage／restore。研究artifacts額外保存到D槽，raw data沒改。
7. **GitHub push一度被阻擋：已恢復。** Approval review用量限制曾使
   Protocol B push未執行，恢復後以同審批流程推送成功，並確認SHA。
8. **Neural embedding ablation：明確skipped。** 沒有可用pipeline/artifact，
   未杜撰。OSCR curve與事件級每小時誤報也未聲稱已實作／可量測。

最小下一步：由實驗者補齊真實motor/session/run與原始window追溯，新增
足夠獨立groups；若要獨立train/val/cal且test至少2groups，先規劃每known
配置至少5個獨立採集groups，但這只是切分最低規劃，不是統計power保證。
先稽核stage特徵語意，再預先登錄用train/validation選擇的classifier／features
比較；保留新的final test，不能反覆對這次test調參後宣稱無偏改善。

## 10. 主要修改檔案與用途

- core/fault_type_class_split.py：known/unknown角色、balanced sampler、registry。
- core/fault_type_sample_split.py：正式catalog、whole-campaign folds、exclusions。
- core/fault_type_features.py：read-only105-D載入、source／row fingerprint驗證。
- core/fault_type_manifest.py、fault_type_validator.py：不可變manifest與完整性檢查。
- core/openset.py、mahalanobis.py：保留unsuppressed nearest known class作audit，
  原predict/default/binary/PolarMap不退步。
- experiments/fault_type_openset.py：train-onlyclassifier、factorydetectors、fit audit。
- experiments/fault_type_metrics.py：known／unknown／healthy／paired與descriptiveCI。
- experiments/fault_type_matrix.py：凍結plan、逐runstatus、checksumresume、atomiccheckpoint。
- experiments/fault_type_report.py、fault_type_archive.py：分層表圖與ZIP64保存。
- tests/test_fault_type_*.py、README.md、reports/fault_type_openset/：語意測試與紀錄。

## 11. 實際測試、實驗與成功／失敗

工作根目錄與完整PowerShell指令見reproduction.md；不要在data內執行寫入。

```powershell
$env:MPLCONFIGDIR = Join-Path (Get-Location) 'output/fault_type_mplcache'
.\venv\Scripts\python.exe -m unittest discover -s tests -q
.\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_40cb4312c2e92342.json --n 5
.\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_40cb4312c2e92342.json --n 1 2 3 4 6 7 8 9
.\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5 --protocol B
```

最後完整測試23:54:18：137passed、exit0；baseline92passed。Synthetic
single-label confusion warnings、invalid-CLI的預期argparse error不算failed。
曾有fixture錯誤／venv缺檔、FPR95 fixture期望值錯誤，已記原因與修正；
另修了fault-only confusion丟healthy誤分類欄位、pooled task-N語意及checkpoint。
這些沒有依test scores改模型。正式2490runs全部成功，failed/retry未被挑掉。
Formal90CSV最終SHA核對0mismatch；每run的保存預測與summary metrics已重算核對。

## 12. 每階段commit、branch與push

Branch：research-improvements-20260920；remote：
https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage.git 。
未merge main、不改寫history、不stage無關282deletions。以下提交均已push
並在執行紀錄確認remote SHA；所有本任務commits有Codex coauthor。

| 階段 | 完整SHA |
|---|---|
| Baseline | 72906cda8cf092c4080de3dcae7f885e24950865 |
| Data audit | 6efdfd259867e624599bbd532182f73eb803ae6f |
| Label ID contract | 58d8f234b1e937840d679b5be3e6fcaff977ad3a |
| Class-role split | e0a3eab983568c7e0de37318cea86048d01c9584 |
| Group sample split | 819c9d06b8cefa13d7b084838ea33b784536195e |
| Manifest/validator | 7a8507bd07097b24528316c6d0cf437f39b384f4 |
| Runner | 3f49a40a40e9ceef7d1f9a553a9465f2c52f5f66 |
| Metrics | 3bb4a7ccef254a120edd00d92132108a669a9fd9 |
| Matrix tests/resume | f2f09b44cbe8825676fca2383046b5d85ae1b71b |
| Full126 preregistration | dd7f679ec498d9836e7f3c2aeb355322776c158b |
| Report/archive support | 084e209aecb9a6e4002d793f502c9d69d69ae380 |
| Pooled task-N descriptor | 1cfdcb63e513a129f86f1a4054fd49108c53a775 |
| Primary N=5 results | 3d8b9f02269ad1eb030f45c34e3a20612b1d7f77 |
| Atomic checkpoint | a495c18d36eefa5c8aacd4d03c1bcc1c31a25992 |
| README/reproduction | 2104fec172e1b71d4047ee201cd080b5164e450d |
| Protocol B results | 9532e6d76911af9eb6bba8ecfb60dde01671cd9d |
| N-sweep results | 686cb38a1392e3da536a6e45e5e2d291014cd516 |
| Final report/tables/artifact paths | 79ff29200551627fb3a312c8deddb7f7a050b7b9 |

本最終report／evidence bookkeeping的後續SHA與GitHub issue連結，記錄於
execution_log.md及最後回覆，不將尚未生成的自身commit SHA寫成已完成。

已建立追蹤 [GitHub issue #9](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9)，
保留獨立來源metadata、更多test groups、跨stage特徵語意與模型可靠性驗證的
未完成條件。研究運算完成，不代表這些資料／效能條件已解決。

## 13. 主要artifacts完整路徑

見artifact_paths.md，列出可直接定位的完整Windows路徑與ZIP SHA/bytes。
Dataset fingerprint固定：
`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。
Git只有compact設定／summaries／indices／logs，完整逐樣本機率、manifest、
fit audits在三個research ZIP。Combined report另有第四個ZIP。
原始工作檔均保留；不是把raw data上傳GitHub或把Temp目錄當唯一長期副本。
