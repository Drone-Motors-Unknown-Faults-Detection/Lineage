# 指標修正與控制重算（2026-10-02）

VERIFIED：624 組、6,013,647 筆已存 predictions 重算；unique samples 28,910。
17 份來源 artifact SHA、原 protocol/234 fit audits、逐組 prediction SHA/IDs 與舊指標均核對。
未重 fit、未重新 inference、未改門檻；6 個 R17 INCOMPLETE 保留。13 項新人工案例測試通過。

final decision 固定為 score > threshold 時 unknown，否則原分類標籤；tie 接受。
unknown 為 AUROC/AP 正類，分數越高越未知，負分數不反轉、不取絕對值。
既有 factory 分數沿用其原始定義；signed RMD 沿用原 score/threshold，不能混為全部平方距離。
健康→unknown 與 accepted 健康→known fault 互斥，兩者加總才是完整健康誤報。
分類原始正確率與拒絕後正確率分開；後者分母仍是全部 known。
fault-only confusion 保留預測 healthy 欄，不刪錯類。coverage 分母含全部 unknown/known。
缺分母為 null，不補零；缺類 support 明列，macro-F1 的 declared labels 仍納入。
沒有可靠時間戳：不算每小時警報、延遲或生命週期。

以下為 seed=0；三個 seeds 是設定重複，不是九顆馬達。數字百分比，非相對增幅。

| 方法 | test motor | 健康→unknown | 健康→known fault | 完整健康誤報 | 最差 RPM 完整誤報 |
|---|---|---:|---:|---:|---:|
| C02/M | T3 | 0 | 22.12 | 22.12 | 50.37 |
| C02/M | T1 | 0 | 0.61 | 0.61 | 0.96 |
| C02/M | T2 | 0 | 57.88 | 57.88 | 99.60 |
| C17/M | T3 | 0 | 0 | 0 | 0 |
| C17/M | T1 | 0 | 31.58 | 31.58 | 100 |
| C17/M | T2 | 0 | 10.79 | 10.79 | 33.60 |
| C24/M | T3 | 0 | 100 | 100 | 100 |
| C24/M | T1 | 0 | 57.42 | 57.42 | 100 |
| C24/M | T2 | 26.98 | 5.82 | 32.80 | 100 |

R18 的最差 RPM 完整誤報也是 100%；T1/8000 的分類錯誤不會被「unknown-FPR 低」抵銷。
本輪暫定研究篩選：**每個 motor/RPM 完整健康誤報 ≤10%**，不是部署或統計保證。
這是執行前固定的安全取捨篩選，不用 test 找 threshold；不符合時受約束 unknown recall 為 null。
目前 C02/C17/C24 均不能通過全部九格安全條件，沒有全面最佳或 production 替換依據。

機器結果：`output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json`（同目錄 gz 入庫）。
metrics seal：`19c1dd6b5a27d5de6c3ec8898f24123cbb68252f2e774a19141586fabf6ae59b`。
重現：`.venv310/Scripts/python.exe -m experiments.fault_type_metrics_v2`。
測試：`.venv310/Scripts/python.exe -m unittest tests.test_fault_type_metrics_v2 -v`。
