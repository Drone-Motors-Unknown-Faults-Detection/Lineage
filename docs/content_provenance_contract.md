# #46：內容SHA與portable／private來源契約

日期2026-10-09。main `5a7865610fff07a455c0a23cec34fc5957ba3569`；依賴 #44 候選 `8126908` 的輸入schema。已重讀AGENT.md、#46、最新main與PR36／56，無其他公開同範圍實作；不推定他人未推送工作。

## 事前版本與雜湊規則

`source_content_v2`：對實際正式CSV bytes逐檔SHA256，以排序的POSIX相對ID＋內容SHA清冊作canonical JSON（sort_keys=True，UTF-8，compact separators），整體SHA作新資料指紋。size／mtime不進內容身分。無manifest仍檢查真實bytes；同內容異root副本可得到相同指紋，但不視為獨立錄製。同dataset內副本列為alias，不自行去重或當新馬達。
明確拒絕空清冊、無法讀取、損壞manifest／未知schema、不匹配已宣告輸出SHA／檔案清冊；前後來源變動拒絕完成。既有stat與manifest指紋只透過明確legacy入口讀取並標 `legacy_fingerprint_v1`；不回寫歷史輸出，不把舊指紋與新版本混為同資料ID。
物化新manifest `formal_materialization_v3`：來源根改固定portable ID，output為根內相對ID；每筆明記output SHA（歷史source_sha256實為衍生CSV bytes的欄位保留相容），archive內容SHA與member ID另存。採集session／時間／原始同步仍UNKNOWN。v1／v2可唯讀讀取；其絕對path只在本機解析成相對清冊，不複製到公共摘要。

## 公開與私人資料

公開只保存schema、相對ID、SHA、data version、合法schema版本與設定；不序列化解析後絕對root、不蒐集token／任意環境變數。私人sidecar放 `.lineage_private/`（新增忽略規則），保存source／output解析路徑；不stage、不上傳Actions。這是本機明文追溯檔，不聲稱加密或可抵抗擁有本機權限的人。
API若只有記憶體pools，將file來源標UNKNOWN，不能補造檔案SHA；可另記array內容指紋，不能當raw錄製身分。
環境只能重用 `core.runtime_environment.collect_environment`／`setup_run`，不新增第二套collector。formal API回傳實際環境與來源；formal CLI／物化run使用既有setup_run保存環境、portable source及resolved已傳入設定，失敗保存error type與已知來源狀態，不公開例外payload。

## 入口盤點與本階段範圍

exp1–7各CLI已有setup_run環境檔；多數run API只回傳運算結果、沒有file來源參數。formal API知道data_root，可先補真實來源。exp6_matrix有自訂run log但未全面setup_run，列 #43 後續整合；不得因formal子項完成就關#46／#26。
本小步先交付 `core/provenance.py`、`core/formal_data.py` 的v3 portable manifest、formal benchmark的新內容指紋與API環境／來源；必要fixture和手冊。其他非重疊API入口仍待後續補齊；exp1／3／health與Web保留不改，精確檔案見使用者分工。沒有替代採集證據或新模型比較。

## 事前驗收

fixture測同stat不同bytes、同內容副本、不同root、無manifest、legacy讀取、損壞／不符manifest、private不進Git公開清冊、來源讀取失敗及無Git。對同一固定fixture比較改動前後formal rows的科學score／threshold／classify指標，排除新增metadata／耗時欄後一致；不fit正式90份。相關與完整suite／pip／CLI及兩平台CI逐次保存，保留失敗。未完成全部runner或main整合時狀態PARTIAL，#46不可關閉。
入口遵循run/main、setup_run及logs/output，工程契約不占exp9–12。
