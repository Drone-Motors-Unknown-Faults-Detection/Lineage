# 2026-10-01 接續研究：來源追溯與可靠性

## 身分更正（優先於 2026-09-29/30 舊稽核的身分敘述）

固定來源為 [Experiments_Guide.md，afcfcc4](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/afcfcc419dab3103a86a8f95601d3af85890eb38/docs/Experiments_Guide.md#L218)，L218、L230–231。
文件支持 T1 是新機、T2/T3 是老機，且為三顆不同馬達。它們可作為
document-supported motor ID；沒有 serial number 不等於沒有任何身分依據。
程式核對 90 CSV 的 stage/T-code 路徑映射後，三折可解讀為 documented
leave-one-motor-out。文件不能單獨證明所有實體採集到檔案的來源鏈。

舊報告「不是三顆不同馬達／motor-level holdout 完全沒有依據」已撤回。
舊 frozen manifests 的 campaign/null motor 欄位、checksum、2490 次結果不改寫；
本次以獨立 evidence overlay 補充文件、程式、artifact、重建、未知五類證據。
原 numerical results 不受文字更正影響，INCOMPLETE 也不自動升為 PASS。

個體差異與老化混雜；不能由三顆馬達推論同一顆的 longitudinal degradation。
兩個 test groups/類是舊研究預先設定的完整度門檻，不是所有 LOMO 研究的通用
定理。「至少五組」只是分開 train/validation/calibration 及兩個 test groups
的規劃範例，不等於必須五顆馬達，也不是統計 power 保證。

## 基線核實與再現

研究 branch research-improvements-20260920 的本機及遠端在啟動時均為
9c09ab4cb0143fda79b56a18f3907dd55564d179；D 槽 Lineage checkout 同 HEAD。
137 tests 於 2026-10-01 00:57 Asia/Taipei 重跑通過。既有 282 tracked deletions
與未納 Git 的原研究 predictions 不納入新提交。不重跑2490次研究。

在研究 worktree 根目錄執行（非 data 目錄）：

```powershell
$env:PYTHONIOENCODING = 'utf-8'
$env:MPLCONFIGDIR = Join-Path (Get-Location) 'output/fault_type_mplcache'
.\venv\Scripts\python.exe -m experiments.fault_type_provenance --data-root data/formal_local
.\venv\Scripts\python.exe -m unittest discover -s tests -q
```

輸出 output/fault_type_provenance/<timestamp>/motor_evidence.json 與相應 logs。
檔案 SHA/row IDs 由現有 catalog 核對；不填虛構 serial、hours、session、raw intervals。

初始訊息停在「【5. 執行契約】」；詢問後已收到 Phase5–7、驗收與交付要求。
依補充執行 final-test guard、exposure ledger、三候選模型與逐階段測試／push。
硬體採集只提供規格，不宣稱完成；不主動聯絡學長、其他 task 或外部人員。
