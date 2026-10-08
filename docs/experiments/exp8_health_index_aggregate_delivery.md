# 實驗八彙總重算：驗證與交付紀錄

## 本輪邊界

2026-10-09，checkout `D:\schoolshit\專題\src\lineage_integration_20261008`，分支 `delivery/exp8-aggregate-20261009`，從 main `4f783c676849a27185cd28d2410b4e76639b7357` 開始。開始時乾淨；先前 PR #40 分支保留在 `5a54cf1e500ddb8c8f1f031ce3cd0e0282429467`。已完整讀 AGENT.md，目錄內沒有其他 AGENT/AGENTS 指引。

重新查 GitHub：main 未變；PR #40、#36 都 OPEN、未合併。PR #36 head `544d4ed8c6516622e2f46c095351f9483a61635c`。15 個開放 issue 無 assignee；#25 只有 Albert 的改名留言，公開 PR 未見彙總實作。無法知道其他人尚未推送的工作。

不改 PR #40 防護，不改 Albert 同檔，不建立新 issue，不合併 PR、不直接推 main。#9、#13～16、#19、#24～30、#35、#37 保持原狀。關單需完整驗收與 main 整合，本輪尚未滿足。

## 分階段紀錄

| 階段 | 實際內容 | commit／推送 |
|---|---|---|
| 手冊 | 先固定 16 檔 SHA、六 run／54 列、等權重、ddof=1、容差與 UNKNOWN 邊界 | `aeab6eb48c27d1c63ef5fb3260632a204c8b1c3f`；已 push，ls-remote 相符 |
| 程式與 fixtures | 獨立彙總入口、來源與 CSV 檢查、失敗稽核、37 項 fixtures；無 fit/predict | 本階段提交後記錄固定 SHA |
| 實際重算與交付 | 使用已提交程式重算封存、核對每欄與來源不變、建立 PR | 尚待執行，不先寫完成 |

## 已執行的測試

既有環境 `D:\schoolshit\專題\src\tmp\lineage_integration310\Scripts\python.exe`，Python 3.10.19；沒有重建 venv。只驗證目前 pyproject 宣告的版本，未宣稱其他 Python 相容。

- main 程式基線：111 項、0 failure、0 error、0 skipped；在手冊 commit 執行，當時未新增程式。證據 `output/exp8_aggregate_baseline/2026-10-09-03-28-48/test_summary.json`、對應 log。
- 初次 fixture 執行在受限 Windows 暫存目錄遭 ACL 拒絕：27 項 setup error，並非成功測試。相同程式改用正常權限後，27 項通過；後續增補至 37 項。
- 新程式提交前相關測試：56 項通過；完整測試：148 項通過。pip check 都通過。保存 `output/exp8_aggregate_validation_related/2026-10-09-03-33-51/`、`output/exp8_aggregate_validation_full/2026-10-09-03-33-55/` 與對應 logs。這兩次 summary 的 HEAD 是手冊提交，程式仍在 working tree；正式重算前將再核對提交版程式與回歸。
- 完整測試內 generator.close 失敗、無效 CLI 參數等訊息是既有刻意失敗 fixtures；測試總結果仍為 OK，原訊息保留在 check_0.txt。

重現指令（專案根目錄）：

```powershell
python -m tests.exp8_aggregate_validation --scope related
python -m tests.exp8_aggregate_validation --scope full
python -m experiments.health_index_aggregate
```

完整測試需要允許本機 HTTP/WebSocket；Windows fixture 暫存也須有正常 ACL。遇到拒絕應使用正常權限流程，不改測試標準。

## 待核對與限制

實際重算尚未完成；先不報差異數或新準確率。原彙總生成程式沒有提交，ddof 與精度順序的歷史證據仍 UNKNOWN。九個未知配置逐名清單與逐窗來源不在六份 JSON 裡；本輪驗證工況、配置數、方法與封存指紋，不能填造採集來源。

給老師的本輪說明放在這份文件；七問與研究背景仍見 [exp24 導覽](../navigation/exp24_README.md)。本輪驗收只處理封存重算，不能把 exp8 的接近 100% 二元結果當成可靠 fault-type、RUL 或 fresh final。
