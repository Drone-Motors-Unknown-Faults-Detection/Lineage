# 固定方法、專用馬達校準：執行紀錄

## P0 / 2026-10-01 Asia/Taipei

- 真實 checkout：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。
- 分支 `research-improvements-20260920`；起始 HEAD `97a4434b97549851b9bae41b8b7dd5836b974f04`；remote 為 Drone-Motors-Unknown-Faults-Detection/Lineage。
- 已完整閱讀 AGENT.md、四份指定研究報告，並檢查 split、manifest、validator、leakage、factory、表示法、受控評估與相關測試。未發現額外子目錄 AGENT/AGENTS 指引。
- 90 CSV / 28,910 rows / 105 維；重新唯讀掃描 fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`，與基線一致。
- 原有 282 tracked deletions、158 untracked 路徑保留；本輪只 stage 明列的新增/修改檔案。不處理舊 D 槽 checkout。
- Python 3.10.19 (`.venv310`) 與 3.14.6 (`venv`)；上輪各 217 tests，此數字不是本輪測試結果。
- 歷史來源：matrix `output/fault_type_matrix/2026-09-30-19-05-42`，representation fit `output/fault_type_representations/2026-10-01-08-38-17`、evaluation `2026-10-01-08-38-59`，exposure `output/fault_type_exposure/2026-10-01-01-10-40`。
- 已完成：90 檔副本/數值重複稽核、18 fit / 36 saved prediction 校驗、來源別名 guard。不要重做 2,490 runs。
- 本輪範圍：新 no-selection protocol、36 配對 detector 評估、T1 只讀失敗分析。尚未完成 P1–P5，不宣稱 fresh final validation。
- 不變限制：所有 rows 歷史已曝光，每折只有一顆 test motor；session/raw windows/實際負載與安裝等 UNKNOWN。缺硬體不阻擋本輪探索性研究。

## 提交記錄規則

每階段驗證後 scoped stage / diff --check / Co-author commit / 非 force push / remote SHA 核對。階段 commit 寫入下一次紀錄，避免自我引用 SHA。

## P1 封存

- `c24584b9a0898c430ecead5186d1694f283dcfd1` commit/push；remote SHA相符。
- `output/fault_type_fixed_calibration/2026-10-01-15-32-22/protocol.json`；protocol checksum `3b6cde9f5c19e627c0694f7488660b783228ae2354e96b8fa25b9dd1085edf1e`。準備過程未fit任何模型；真實資料正式fit尚未開始。

## P2 工程路徑

- 小型新core overlay、fit用途稽核與no-selector dependency，重用原 immutable manifest/Representation/LogisticRegression/core.openset factory。舊manifest及原表示法module未改，原registry SHA仍有效。
- 新run/main/setup_run：prepare→fit（只load train/cal）→evaluate（讀封存模型、test），來源90SHA每次before/after實查，不以FeatureStore cache當作不變證据。CLI可指定三份既有N/class manifests，不需要重建class split/matrix。
- schema2 + protocol_version精確匹配才接受空validation；其他歷史protocol空validation仍INVALID。single-fold用途重疊、wrong motor、unknown、fit/reference混入cal、shared-valcal、global winner拒絕；舊source SHA/raw alias guards保留。
- 壓縮fit audits綁train/scaler/classifier/covariance/neighbor reference/cal IDs、資料與config checksums、transform checksum、class thresholds、耗時；lock明列18fits、模型SHA、manifestSHA及exposure ledger。沒有selected_representation/global_winner。
- 保存predict的逐類raw distance / class thresholds / ratios，原factory score再次一致核對。reporter核對gzipSHA、IDs/真值/RPM/class role、>1符號、零門檻epsilon、metrics重算與detector配對；摘要只有固定方法motor平均/範圍與seed SD，不輸出CI/winner。
- targeted最初20tests PASS；首次完整雙Python各237tests PASS。加入saved prediction tamper/metrics/grid regression後最終數接續核對；中間237不是最終數。
- Synthetic兩環境CLI prepare/fit/evaluate已通過（各36 engineering evaluations）；不是正式資料研究成績。最後新來源before/after檢查版本也執行smoke。
- 未改Maha/openset/PolarMap/default105/linear/正式data。既有282tracked deletions仍未stage。
- 19:26:43/54 的兩環境241測試有1個negative fixture失敗：第一列本來就是unknown，test寫成改為unknown等於未修改；不是檢查器放過真實篡改。修fixture使role必然相反，並加subTest。保存這兩次FAILED stdout，不冒充PASS；接續重新全套驗收。
- 修fixture後19:28:20/31雙環境241tests PASS。之後再加入lock→labels/exposure與model→parameters/transform/threshold audit的綁定檢查，最終驗收為19:29:26/37，均241tests及pip check/6 CLI help PASS。24項新增測試（217→241）；無來源資料/正式預設變更。
- 最新source-checked synthetic CLI smoke：Python3.10 `output/fault_type_fixed_smoke/2026-10-01-19-27-27/smoke_index.json`、Python3.14 `.../2026-10-01-19-27-38/smoke_index.json`，各36 engineering evaluations；直接新增完整suite亦每環境在自身interpreter內fit/load模型並36評估、重算SHA/指標和重跑決定性，不跨runtime載入joblib。

- P2 `414c30f24c31bb7441432400862303040bea4e5c` commit/push，remote一致。正式資料fit始於此提交之後。

## P3：現有正式資料的新探索性比較

- Python3.10.19：19:31:08–19:31:38 fit 完成，18固定分類器/36detector模型；無validation/test features被fit入口load、無selector。output `fault_type_fixed_calibration/2026-10-01-19-31-08`。
- 90來源檔案before/after SHA fingerprint相同；source_verification.json記錄。3 manifests 明列validation=[]，train/cal/test motor角色分開；INCOMPLETE保留。
- locked_methods.json綁定模型/manifest/audit SHA、protocol SHA、程式HEAD與環境；fit_audits.json.gz約27.9MB、18joblib共約75MB屬大型衍生證據，以既有archive工具D槽新目錄保存，不放Github。封存模型lock及backup索引先提交，再評估。
