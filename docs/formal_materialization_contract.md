# #45：archive 物化的路徑與通道契約

日期：2026-10-09。程式基線 main `0282209`；本分支接在 #27 候選 `d2647f3`，讓 Windows／Ubuntu CI 能驗證新 fixture。兩個 PR 分開審查，不自行合併。
已重讀 AGENT.md、#45 本文、PR #36／#53 公開 diff；目前沒有 #45 的其他公開實作。不能確認他人未推送工作。

## 已由程式確認的缺口

`core/formal_data.py` 的 `_convert_condition()` 從 archive member 倒數第二節直接取 config，未先驗證 archive 路徑；`n_windows=min(widths)` 靜默裁短。
既有反例只證明 `..` 可離開 RPM 子目錄，沒有證明曾在 output_root 外實寫。
研究分支 `b3d68f1` 的 `core/synchronized_raw.py` 已拒絕沒有 clock bridge 的分檔通道，並只讓 shared rows 經明確 timebase／quality 規則切窗。本次不搬整套研究管線，也不把此 adapter 的同長通道當成同步證據。

## 寫入路徑盤點與政策

1. Stage1／3：外層 ZIP → myfeature.zip → `myfeature/MOTOR/RPM/CONFIG/檔名` → output_root/Step-N/myfeature/相對路徑。
2. Stage2：外層 ZIP → csv.zip → MOTOR/RPM.zip → CONFIG/五通道 CSV → output_root/Step-2/myfeature/MOTOR/RPM/CONFIG/特徵檔。
3. manifest：output_root/formal_materialization_manifest.json。
4. 每個檔案的原子暫存：已驗證目標的同目錄；失敗／中斷清除暫存檔。
5. 執行證據：run/main 由 setup_run 寫 logs/formal_materialization 與 output/formal_materialization，不把來源路徑寫入公開摘要。

ZIP 路徑一律使用 `/`。拒絕空節、`.`、`..`、反斜線、絕對路徑、Windows drive／UNC、冒號與 ZIP symlink；所有層級都驗證，不能只檢查最後輸出檔。
MOTOR／RPM／CONFIG 只接受目前程式定義及已存在的 `1screw` alias；不把輸入字串當任意目錄。
所有目的檔案先 resolve，再 relative_to 解析後的 output_root；字串前綴相似不算包含。拒絕 output_root 內沿途任何 symlink（即使指向根內），避免別名或覆寫連結。
output_root 本身由呼叫者明確指定並 resolve，不能在唯讀 source_root 內。無法消除同時有惡意本機寫入者造成的 TOCTOU；此介面不是敵對多使用者安全隔離。
讀取／驗證／計算完成後才開始寫入；所有待寫目的地先檢查。錯誤來源不得先寫合法子集再失敗。
個別寫入採同目錄唯一暫存與 os.replace；中斷不保留該檔暫存。若磁碟故障發生在多檔提交途中，可能保留已完成的檔案，但不發布 completed manifest；不宣稱整批資料庫交易。
正式來源與舊產物不覆寫；測試只用 TemporaryDirectory。既有 `force` 是顯式操作選項，本輪不對正式資料使用。

## 通道政策 equal_window_counts_v1

五個通道的窗口數和每窗口 sample row 數必須全部相等且非空；不同直接拒絕，沒有隱藏 truncate 選項。
拒絕訊息保存各通道原始 shape、丟棄數為 0 與原因；成功 manifest 保存 shape、政策版本與 `alignment_status=UNKNOWN`。
同長只證形狀相容；沒有原始時間戳／clock bridge，不能宣稱物理同步已通過。
合法等長 fixture 的 CSV bytes／SHA 必須和固定 main 程式相同；不改統計量、FFT、IQR、列順序或欄位順序。

## 事前驗收與影響檔案

新增 `tests/test_formal_materialization_safety.py`：traversal、absolute、drive、UNC、根字串前綴別名、symlink、正常路徑、2／3 窗口拒絕、不同 sample 長度、重複通道、錯誤前零檔案、原子寫入中斷清理、來源 SHA 前後相同，以及 run/main。
修改只限 `core/formal_data.py`、工程 fixture／證據入口與本契約；不改正式 data、Web、health、LW／k-NN／PolarMap。
本機與兩平台 CI 分別報實際通過／skip／未驗證，不將缺少 symlink 權限說成通過。
程式可交付候選 PR，但 #45 必須等 main 整合與全部驗收後才可關閉。
本項是工程安全契約，不增加實驗編號，不產生新研究準確率。
