## 2026-10-01：同步 raw／feature／fresh engineering 交付

分支 `research-improvements-20260920`。P0–P6 程式與本機工程驗收完成，**獨立研究驗證仍為 BLOCKED_NO_ELIGIBLE_DATA**，沒有宣稱完成硬體採集或可靠模型。

- 認證核對 Ancestor 固定文件：同步設計、10kHz/RPM/欄位只能標 documented/code_setting；header 衝突、實際 fs/clock/physical/session 仍需錄製證據。T1/T2/T3 為文件支持的三顆個體，不因缺序號否定身分，也不分離個體與老化。
- 新 shared-row parser 保留原 index/time；品質 masks 不刪點，不裁最短、不跨錄製/插值。四個分離105版本與 sidecar/raw 重算；分檔無 clock bridge 明確拒絕。
- fresh CLI 完整 validate/evaluate/resume/receipt/recover；canonical ledger 綁歷史 genesis，OS鎖/CAS/journal/receipt 在prediction前，failed exposure保留。fixture不能轉真實，real physical/model/coverage不足直接拒絕。
- 獨立 Python3.10.19 與原3.14.6各 **204 tests PASS**，pip check/CLI均通過。Synthetic 300窗六paired runs＋resume，共一筆exposure，real final=false。
- 六種預登錄表示×三舊motor folds×兩detectors，共36 runs/0failed。先known validation選振動75，再鎖定/commit後才exploratory test。分類accuracy29.63%→34.15%（+4.52pp）、macro-F1 .2620→.3028；MahaAUROC .5311→.5746、unknown recall15.07%→18.44%。T1未知召回仍0%、kNN健康FPR變差，因此default不換。不能與全部126組平均直接比較。
- 90正式CSV與8,751歷史artifact files/11,774,540,137 bytes逐檔SHA核對未改；舊2,490 runs不重跑，282既有deletions不stage。13個新ZIP於D槽保存，wholeSHA/CRC/memberSHA全部通過；無實測DAQ或私人全文上傳。

仍需：一份未刪點未切窗原始錄製＋真實recording/session/run、fs/time/alignment及單位/軸向/校正/安裝/負載引用；正式研究另外需要獨立known train/val/cal或bridge、未曝光且符合coverage的final。原始時序不存在時不能恢復真實raw-window mapping，metadata文字更正不能將split升為PASS。

完整報告 `reports/synchronized_pipeline/final_delivery_20261001.md`、指令 `reproduction.md`、模板 `examples/raw_config.template.json`；各phase commit及實際push見execution_log。所有本輪舊資料效能仍EXPLORATORY，fresh研究未完成。

Co-authored-by: Codex <codex@openai.com>
