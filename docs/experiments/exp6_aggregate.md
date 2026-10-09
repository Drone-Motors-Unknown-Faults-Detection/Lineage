# 實驗六彙總：讀取矩陣摘要，不重新訓練

已完成的工況×seed×方法結果，如何放在一起比較？本工具只讀[矩陣](exp6_matrix.md)manifest指向的JSON，計算平均、標準差與配對差。沒有載入105維資料、fit模型、重設門檻或新增測試樣本。

## 輸入與驗證邊界

load_matrix要求manifest status=completed、runs長度符合expected_runs，每run有completed摘要、方法／seed相符且共同dataset_fingerprint一致，八個指標須有限值。缺檔、不完整或NaN會失敗，不補零。

現行驗證**沒有完整重建九工況×seed×方法預期鍵集合、唯一run鍵及來源SHA檢查**；摘要可含多列，未逐一核對manifest的motor／rpm。status=completed不能單獨證明54格無重複或來源正確；dataset_fingerprint本身限制見[正式版](exp6_formal_benchmark.md#輸出怎麼讀)。此手冊不把防護不足包成已驗證完整矩陣。

## 怎麼算

八欄是known_accuracy、open_set_accuracy、auroc、aupr_unknown_positive、fpr_at_tpr95、unknown_precision、unknown_recall、unknown_f1，意義見[正式版](exp6_formal_benchmark.md#輸出怎麼讀)。known只指healthy，不是known fault type。

| 產物分組 | 權重與計算 |
|---|---|
| condition_summary | dataset×method，對保存的seed列等權平均 |
| macro_summary | method，所有工況×seed列等權，不按視窗數加權 |
| paired_differences | dataset×seed匹配，k-NN減Mahalanobis；兩方列數須匹配 |

mean用保存的已round6指標；std用ddof=1，單列std設0；輸出再round6。seed不是獨立馬達，這些std只描述保存列的變動。paired的knn_better_pairs欄實際計算「差值>0的筆數」；對FPR等越低越好的指標，名稱**不代表k-NN較好**，須反向解讀。其他正差也不是統計顯著性。

## 怎麼使用

在repo根目錄依[環境政策](../runtime_policy.md)準備uv，不需要data目錄，但需要完整結果包：

```bash
uv run --locked python -m experiments.aggregate_exp6 --help
uv run --locked python -m experiments.aggregate_exp6 --manifest output/exp6_formal_matrix/matrix_manifest.json --output-root output/exp6_formal_matrix/recompute_001
```

選未使用的recompute_001；預設會寫manifest旁的aggregate/，**會覆寫同名檔**，不要對封存直接使用預設。API aggregate(manifest_path)只算dict；write_aggregate(manifest_path,output_root)寫檔；main提供CLI，沒有run(pools)、Web重算按鈕或續跑機制。Web唯讀讀原正式aggregate，新根不會自動部署到頁面。

## 輸出、判斷與限制

writer是[write_aggregate](../../experiments/aggregate_exp6.py)，寫五檔：aggregate.json、condition_summary.csv、macro_summary.csv、paired_differences.csv與aggregate.md。aggregate.md雖是Markdown，確由程式生成，不是手寫報告。此模組尚未setup_run，沒有標準logs/與environment.json；不能宣稱完整執行環境已自動保存。

預期同來源重算數字一致，paired鍵對齊，缺件明確失敗。它只能核對摘要算術，不證明逐樣本預測、錄製獨立、fresh test或最佳部署方法。未知正類比例不同時不直接比accuracy／AUPR；不同指紋／split／cal策略不可混為方法提升。完整舊平均查[固定正式aggregate](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/1fa9431bb7b86959f29540d07b2b9290ab39ce42/output/exp6_formal_matrix/aggregate)，不人工複製分數表。

## 依據與程式碼

平均、ddof與配對方向是Lineage統計約定，沒有新模型；原演算法文獻見[正式benchmark](exp6_formal_benchmark.md#方法來源與程式碼)。[aggregate_exp6](../../experiments/aggregate_exp6.py)讀取、驗證與寫檔；[test_aggregate_exp6](../../tests/test_aggregate_exp6.py)提供不依賴data的fixtures；[web/experiments](../../web/experiments.py)只讀正式結果。程式元件測試不替代來源完整性查核。
