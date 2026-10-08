# 實驗八：健康指數封存彙總重算

2026-10-09，對應 [#25](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/25)。先提交本手冊與來源契約，再新增程式。本輪從 main `4f783c676849a27185cd28d2410b4e76639b7357` 建立 `delivery/exp8-aggregate-20261009`；不修改 PR #40 或 Albert PR #36。

## 方法與事前定義

唯讀輸入是 `reports/exp8_health_index_results/` 的 manifest、六個 JSON、六個 CSV、舊彙總及 README，共 16 檔。以 [來源契約](exp8_health_index_aggregate_contract.json) 的 SHA256 鎖定位元組，載入前核對；資料指紋是 `81c9192476ecd1e23a17b3ed5a343dcd50cdc2e5b7e0cc5466e9162941898228`。此指紋屬於 exp8 封存，不混用後續 fault-type 資料的 `c4145d6e…`。

- schema 為 1；seed 固定 42、123、2026，方法固定 Mahalanobis、k-NN。唯一 run 鍵是 `(seed, method)`，唯一列鍵是 `(seed, method, motor, rpm)`。
- 工況是 T1/T2/T3 × 6000/8000/11000rpm。`dataset` 必須對上 motor/rpm；六 run 各九列，共 54 列。方法間與 seed 間的樣本數必須一致。健康配置 `8screws` 的依據是既有 benchmark；每列 `n_unknown_classes=9`。JSON 未存未知配置名稱、逐窗 ID 或原始視窗，不填造這些欄位。
- run 必備欄位含 schema、experiment、status、seed、method、confidence、formal_condition_count、dataset_root、dataset_fingerprint、score_direction、health_direction、unknown_calibration_leakage、rul_available、commit_sha、python、rows。列必須具備 benchmark 原有的全部 33 欄，型別、方向、參數與數值範圍要檢查。
- 原設定：Mahalanobis 使用 Ledoit–Wolf；k-NN 的 k=5；confidence=0.95；分數大代表較異常；健康指數大代表較健康。重算不呼叫 fit、predict 或載入正式 CSV。
- 全域摘要：每方法 27 列等權重，各 seed 與各工況均等；不按窗口數加權。逐工況摘要：`(method, dataset)` 分組，三 seed 等權重。排序固定 method、dataset 字串升冪，CSV 的 index 從零開始。
- 七個彙總欄：`health_gap_known_minus_unknown`、`open_set_accuracy`、`auroc`、`unknown_recall`、`unknown_f1`、`known_health_mean`、`unknown_health_mean`。平均 `sum(x)/n`；標準差 `sqrt(sum((x-mean)^2)/(n-1))`，即 ddof=1。它描述列間變動，不是母體信賴區間。
- 健康平均是各測試組的窗口平均，health gap 是已知減未知；accuracy 是 score>1 的二元正確比例；AUROC 以未知為正類、原分數排序；unknown recall 與 F1 沿用 `experiments/health/evaluation.py` 的定義。只彙總已保存數值，不從健康平均反推預測。
- JSON 的 mean/std 與方法差值四捨五入至六位；方法差值先取未四捨五入的 k-NN 平均減 Mahalanobis 平均，再四捨五入。CSV 保留 double 精度。舊 JSON 比對 atol=0.0000005、rtol=0；CSV atol=1e-12、rtol=1e-10。每欄保留舊值、新值、差值、容差與判定；ID、類別與欄位集合精確比對。
- NaN/Infinity 或必備欄位缺失一律拒絕，不省略、補零或降低分母。正規矩陣的 train/cal/known/unknown 數量必須正整數；零分母一律失敗。`health_effect_size=null` 只在已知與未知 std 都為零時允許，且不加入七欄彙總。其他 null 拒絕；單類 AUROC 不適用於這份完整矩陣。
- 不提供部分成功模式。缺檔、額外來源、重複 run、錯 seed/方法、錯指紋、矩陣不足、來源 SHA 不符皆中止，輸出失敗紀錄，不稱完整結果。六個 CSV 是附帶封存來源；彙總唯一數值輸入是六個 JSON，並核對 CSV 是否逐列相符。

## 歷史定義的證據邊界

歷史彙總首次提交於 `ff656cb325f4f4178904f4b3963bbc28fef88b19`，只有四個結果檔，沒有產生程式。該版 README 明載「mean over 9 conditions × 3 seeds」，支持列平均；找不到原始程式來直接證實 ddof、四捨五入順序或是否曾用樣本加權。本輪規則在執行前固定；之後若數值吻合，只能證實這套規則能重現封存，不能倒推原作者必然用了同一段程式。原生成過程保留 UNKNOWN，不能為關單改成 VERIFIED。

## CLI 與預期驗收

```powershell
python -m experiments.health_index_aggregate
```

`run(source_root, contract_path) -> dict` 與 `main()` 均使用 `core.logger.setup_run("exp8_health_index_aggregate")`。寫入 `logs/exp8_health_index_aggregate/{ts}.log`、`output/exp8_health_index_aggregate/{ts}/`；不接受指向封存的輸出路徑。新結果為 aggregate_summary.json、aggregate_by_condition.csv、field_differences.csv、source_inventory.json、recomputation_audit.json。記錄當前 commit、Python、套件、命令、來源 SHA、契約 SHA 與來源修改前後核對。

預期是完整六 run、54 列、18 組逐工況摘要，所有比對欄有判定。差異可以為零，也可以揭露舊檔不一致；差異不觸發覆寫或重新訓練。未取得歷史原公式，#25 留待審查；新程式未合入 main 時也不關單。本輪不評估準確率提升。

## 參考依據

算術平均、樣本標準差與容差是本專案重算約定，不另宣稱研究演算法。原健康映射、Open Set 與文獻見 [benchmark 手冊](exp8_health_index_benchmark.md)；原矩陣來源見 [matrix 手冊](exp8_health_index_matrix.md)。歷史 `health_effect_size` 用兩組 population variance 平均的平方根，不在本輪改成另一種效果量。

AGENT.md 指定的數位時代寫作文章本輪讀取失敗（non-retryable）；依 AGENT.md 已列出的五項規則寫作。

## 程式碼與輸出

| 路徑 | 本輪用途 |
|---|---|
| `experiments/health_index_aggregate.py` | 新增嚴格載入、彙總、逐欄比對與 CLI |
| `tests/test_health_index_aggregate.py` | 不依賴 data 的完整與失敗 fixtures |
| `docs/experiments/exp8_health_index_aggregate_contract.json` | 固定來源 SHA、矩陣與統計規則 |
| `experiments/health_index_benchmark.py`、`health_index_matrix.py`、`experiments/health/evaluation.py` | 唯讀核對來源定義，不修改 |
| `core/logger.py` | 使用既有日誌，不修改 |
| `reports/exp8_health_index_results/` | 16 檔唯讀；包含舊彙總 |
| `logs/exp8_health_index_aggregate/`、`output/exp8_health_index_aggregate/` | 新重算與差異、SHA 清冊 |
| `docs/experiments/exp8_health_index_aggregate_delivery.md` | 實際驗證與交付紀錄，完成後新增 |

web 層不改；不改正式 105 維、Mahalanobis/LW、k-NN factory、PolarMap，也不改健康池或串流。只比對已存 exp8 結果，不新增 fresh final、跨馬達 fault-type 或物理退化結論。
