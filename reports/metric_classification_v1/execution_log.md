# 實驗13執行紀錄

所有新增敘述採繁體中文。日期2026-10-03，Asia/Taipei。

| 階段 | 實際指令與結果 | 提交／推送 |
|---|---|---|
| P0 | 讀最新 main AGENT.md、本機規範、歷史來源帳冊與最新 Q／solver；282個無關 tracked deletions保留；exp13未使用 | `a83e4f8f62f6d45b505931a270b0b2447c6b215d`；remote核對一致 |
| P1 | 新公式14項測試；第一次空矩陣測試失敗，修正後14通過。synthetic smoke僅工程測試 | `1d1fd9cba6eacfab4046e51122dcbfc0f9865d1d`；remote核對一致 |
| 環境 | `.venv310/Scripts/python.exe -m experiments.fault_type_continuous_acceptance`；Python3.10.19，410通過，pip check與既有37 CLI通過。`venv/Scripts/python.exe`同指令：Python3.14.6亦410通過；兩個新增CLI各於兩環境 --help通過 | 環境證據位於下列output；加入7項來源測試後仍需最後完整回歸 |
| lock | `python -m experiments.fault_type_metric_classification lock --solver-protocol output/fault_type_solver_lock/2026-10-02-23-46-28/protocol.json --diagnosis output/fault_type_solver_fit/2026-10-02-23-51-52/diagnosis.json` | protocol先推送才 fit |
| fit | 同模組 `fit --protocol output/fault_type_metric_classification_lock/2026-10-03-09-42-02/protocol.json --data-root data/formal_local`；九份模型封存 | fit lock待本階段提交；未執行 outer |
| 來源核對 | 新 verifier 的7項人工污染測試，兩環境各7通過；正式九模型正在重建；不變更方法或參數 | 狀態依後續行更新 |

協定 SHA：`9ca9be082013349680b642e509be761d84ca150a947429251bd1c50f86ed1a8b`。fit 路徑 `output/fault_type_metric_classification_fit/2026-10-03-09-43-55/locked_study.json`。環境 output 路徑 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-09-41-18`、`output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-09-41-36`。新 verifier 路徑 `output/fault_type_metric_source_verification/2026-10-03-09-48-46`。

已確認基線不改，尚未取得本批正式 accuracy；不把收斂或測試通過算成可靠提升。raw來源 UNKNOWN、fresh unavailable，但不阻擋現有資料比較。

## 09:54接續檢查點

九份模型從原 manifest 的 known train／calibration 數值重建，全部精確相符；四種分類器陣列、三種原型、四個 factory detector 與 energy reference 均逐份核對。來源校驗 SHA：`5611f1e6ab41451a7c9c38090a597a01efe76c242ca53e00dc8566f5a0eaf673`。此 verifier 未讀取 test 特徵，不能因此宣稱採集獨立性或 fresh test 已成立。

新增7項來源污染測試後，Python3.10.19完整測試417項通過（169.047秒），Python3.14.6亦417項通過（171.419秒）。最終CLI環境摘要仍在產生；先前已完成的410項環境摘要保留。新摘要路徑為 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-09-50-03` 與 `output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-09-50-16`。

本階段封存 fit lock、來源核對程式／測試／手冊及來源摘要後，才執行：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_metric_classification evaluate --protocol output/fault_type_metric_classification_lock/2026-10-03-09-42-02/protocol.json --lock output/fault_type_metric_classification_fit/2026-10-03-09-43-55/locked_study.json --data-root data/formal_local
```

待辦：108格正式配對、逐樣本重算、固定門檻判定、完整分母的 final fault F1、D槽備份、後續 LFDA 文獻與有界協定。九份 joblib 與大型 audit 不加入Git；以後續 archive 索引交付。既有282個無關刪除不納入提交。

## 10:08執行檢查點

來源核對／fit lock已提交 `a821d42e643bd0c29597e39dbb91853598aa4cbf` 並確認remote一致。兩個417項測試環境的pip／既有37 CLI最後均PASS。

首次evaluate在60個checkpoint後因C槽剩餘不足1GB停止，退出1；保留原目錄與失敗log，不算模型失敗、不調參。當時本輪預測檔僅約55MB，不能把所有磁碟減少歸因於其輸出；OS頁面檔資訊唯讀查詢被拒絕，原因未確認，未調整OS設定。

已將兩份先前工程smoke的未tracked `fit/evaluate/verify` 六個子目錄移到 `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/relocated_engineering_smoke/`，按原timestamp分目錄。每個目標預先確認在明確D槽範圍、不存在、不含tracked檔；逐檔移動前後SHA相同。共11+631+2+11+631+2=1,288檔，可由新位置或既有完整ZIP恢復。原tracked smoke_index保留；沒有移動正式資料或本輪依賴。這是可恢復的移動，不是刪除；既有歷史索引的source path以原封存位置保留，新對照在此記錄。

以同protocol／lock及 `--resume output/fault_type_metric_classification_evaluate/2026-10-03-09-55-17` 續跑，108／108完成、0模型失敗，1,040,760筆輸出、28,910個unique samples。新evaluation SHA `f7b055a5f3081d0c0718fa52d0705c0edd29528f2cbc5cdfb9617101a41cb60a`；90CSV前後指紋相同。verify於 `output/fault_type_metric_classification_verify/2026-10-03-10-06-11` 重推全部保存輸出與truth mutation；尚待完成、report及備份。不以checkpoint重推算新增獨立試驗。

## 15:11驗收檢查點

verify已完成108格、全部逐筆精確相符，SHA `66b5dce1ce08d3d0dd778faac7b13ab3893e5097372c46ae1d275ec65cd084d5`。report `output/fault_type_metric_classification_report/2026-10-03-10-12-38/summary.json.gz` 封存12方法、每motor／RPM／class／seed、完整分母final fault F1與安全契約；12方法main_screen全部FAILED。數字見final_findings，不將工程測試通過稱為研究通過。

新增事後診斷手冊先於程式。第一次診斷 `2026-10-03-10-21-25` 在程式載入後又修改來源檔，故不採其程式綁定證據；保留產物，不列VERIFIED。第二次 `2026-10-03-10-23-33` 拒絕於verified binding，退出1：原verifier的runs是run_id／rows／reinference flags精簡schema，新增檢查誤要求與完整評估runs字典相等。修正為唯一ID、逐run筆數、成功flags、資料來源及unique samples核對；每個評估checkpoint仍驗seal、逐樣本SHA與IDs。另加入執行前後程式SHA相同保護，未放寬原模型／來源guard，未改任何參數或正式推論。

修正後 `output/fault_type_metric_failure_diagnosis/2026-10-03-15-07-58/diagnosis.json` 完成432組分布與18組Q01/Q03對照；對照全部逐筆EXACT，diagnosis SHA `3e172400df4c2172c53a262707a808595a6a6d741396a9e97040486579acd05d`。五項診斷測試兩環境各通過。T1 seed0 unknown分數最大值：E09=.771471、E10=.615236、E11=.996801、E12=.712990；固定門檻1，全數未拒絕。這支持校準位置與排序分開分析；沒有依T1掃門檻。

新增診斷後完整回歸：`.venv310/Scripts/python.exe -m experiments.fault_type_continuous_acceptance`，Python3.10.19共437項通過；`venv/Scripts/python.exe`同入口，Python3.14.6亦437通過。兩者pip check及原37 CLI均PASS。摘要為 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-15-08-09/environment.json` 與 `output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-15-08-20/environment.json`；先前432／417摘要保留。

備份新增有效診斷後為11 ZIP／413來源成員；`output/fault_type_fixed_delivery/2026-10-03-15-10-24/member_verification.json` 全檔SHA、逐成員SHA／CRC均PASS。D槽路徑 `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/metric_classification_v1`，不是離站備份。首次診斷無效／第二次失敗log保留，正式資料與282無關刪除均不stage。本階段提交hash於下一階段紀錄，避免自引用commit造成循環。
