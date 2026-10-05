# 單顆馬達跨馬達研究的證據盤點與文件交付

2026-10-05，Asia/Taipei。本手冊固定本次收尾程序，先於新增匯整程式提交。不改已封存方法、指標、切分、模型、門檻或可靠性契約。

## 方法與判定

讀取各批 result_index、原始 protocol、evaluation、verification 與 summary。核對索引內實體 SHA；語意 seal 另依各批既有 verifier 核對。將方法參數與全 fold／seed 指標原樣編入小型索引，沒有選參或 global winner。正式資料維持唯讀。

M 批沿既有 exp21 report 子命令完成 1,134 組配對。所有方法以原 continuous_reliability_v1 契約判定；只有完整主篩通過且關鍵保護無明確失敗，才能支持有限確認。若完整結果無此候選，採 B 路徑收尾；Group DRO 保留為已規劃未實作，不啟動 fit 或 test。程序中斷、數值不收斂、資料缺組與可靠性失敗分開列示。

## 預期產物

checkpoint_inventory、method_catalog、decision_record、繁體中文 Markdown 技術報告與可編輯 Word 報告。輸出使用 core.logger.setup_run，科學 runtime 執行盤點與內容檢查；Word authoring 使用 bundled workspace Python，不升級科學環境。CLI 為 `python -m experiments.fault_type_research_closeout`，提供 run 與 main。Markdown 與 Word 使用同一內容來源；圖表若有，僅由已驗證結果生成。文件內容與排版驗收分開，不將 ZIP 或文字檢查當逐頁渲染驗收。

驗收預先固定：篡改 SHA 必須拒絕；缺項保留 INCOMPLETE／UNKNOWN；不得把 planned 方法列為已執行；健康兩項誤報及 final F1 沿 sealed summary 的完整分母；toy case 驗證匯整和百分比呈現；實際報告的關鍵值與 authoritative JSON 一致。文件改動不反覆重跑既有 618 科學測試。

## 來源

此程序是專案的證據盤點與文件編排約定，未提出新機器學習方法。演算法來源沿各批 sources、source ledger 與先行手冊；引用原始論文與作者程式，並保留閱讀深度和本站適配差異。主要可靠性判定直接沿 `core/fault_type_reliability.py:CONTRACT`，不是論文的部署安全保證。

## 影響範圍與保存

新增 `experiments/fault_type_research_closeout.py`、對應測試及本次 reports。唯讀各批 result_index、protocol、summary 與來源文件。exp19／20／21 已封存程式、正式 data、core.openset factory、PolarMap 均不改。大型原始預測／模型留在既有 D 槽；新增結果包核對 whole／member SHA 與 CRC。同機 D 槽不稱異地備份。282 筆無關 tracked deletions 不 stage。
