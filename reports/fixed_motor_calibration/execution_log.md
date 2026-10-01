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
- 新run/main/setup_run：prepare→fit（只load train/cal）→evaluate（讀封存模型、test），來源90SHA每次before/after實查，不以FeatureStore cache當作不變證據。CLI可指定三份既有N/class manifests，不需要重建class split/matrix。
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
- fit checkpoint `b1eec1b2a3c110b05108570617a6d15cdd28a96a` commit/push remote一致；只有lock/來源校驗/113656368-byte ZIP索引/log，不提交joblib或raw。fit ZIP24files/CRC/wholeSHA通過。
- 19:32:25–19:33:43 真實正式資料探索性 evaluate 完成36/36，0失敗。18classifier共享，每樣本12次predict；346920 records但unique test IDs仍28910，不是346920獨立受試。code實作SHA為414c30f，執行當時HEAD為文件/lock checkpoint b1eec1b。
- evaluator `output/fault_type_fixed_calibration/2026-10-01-19-32-25/evaluation_report.json`與36 gzip predictions，來源before/after fingerprint不變。T3/T1/T2 test rows9294/9759/9857；known5604/5935/6007；unknown3690/3824/3850。
- 19:34:14–19:34:51 reporter完成36runs/346920rows SHA、IDs/truth/score/threshold/metrics/RPM、配對及12歷史對照；`output/fault_type_fixed_report/2026-10-01-19-34-14/verified_results.json`。
- 每固定method/motor的3seeds預測值完全相同；seed SD0是決定性演算法結果，不是motor母體不確定性為0。沒有method winner；descriptor只有各motor及平均/範圍。
- 與原同N5同fold同fit/cal方法相比12配對所有classifier/reject變動0，score最大絕對差0、accuracy/recall差0。本輪取消globalselector/shared選參角色改變解釋與流程，不必然改變同樣fit/cal的分數。
- T1四方法unknown recall0、healthyFPR0。維持失敗，不重新挑seed/threshold，未重跑126 combinations或2490舊run。

- P3 `4044600dea9dd2c899ed529955fc7298434db9ac` commit/push，remote相符。evaluate38files ZIP79953456bytes、verifiedreport ZIP702576bytes，CRC/wholeSHA通過。逐樣本與模型大型包留在D槽新目錄。

## P4：T1只讀診斷

- 3新增helpers tests PASS；19:36:47–19:37:03實際完成4固定方法T1診斷，3seeds相同所以不把重複seed當獨立證據。每方法3,824 unknown / 5,935 known / 991 healthy。
- 僅load sealed models，未fit/改threshold；model SHA和90source before/after不變。真值/方向/NaN/分位數/保存模型score一致，排除覆蓋範圍內工程報表錯誤。
- 分布JSON涵蓋train/cal/test每label每RPM，raw distance及threshold ratio拆開；四ECDF人工視覺核對，無投影圖因果推論。
- 特徵/score重疊、跨motor分布差異、寬鬆calibration class接受區支持，但物理原因UNKNOWN。Maha75 unknown最大.595545、AUROC.507380；kNN75最大.660435、AUROC.584985；均未達1。細節與反證見t1_failure_analysis.md。
- Python3.10.19與3.14.6最終此phase各244tests/pip check/8CLI help PASS：`output/fault_type_fixed_acceptance/2026-10-01-19-37-22`、`.../2026-10-01-19-37-33`。27新增測試，舊217無未解釋退步。原moments/single-labelwarnings與negativeCLI stderr保留，exit0。

- P4 `341e76336c20d7ba05e32906478e6717ba023dde` commit/push remote一致。

## P5：報告與交付

- final_report.md完整列用途與teacher建議層級、36新runs vs歷史2490、三motor/9motor-RPM結果與unknown prevalence、兩method配對、default未改、FAILED/INCOMPLETE/UNKNOWN；沒有以支持CLI當作全N已重跑。
- T1按RPM追加重要反證：75/Maha AUROC6000=.761686而11000=.047005。不是所有RPM都隨機；没有藉此翻轉score或挑有利RPM，主結果不變。保持兩個下一輪方案未實作標記。
- 新只讀delivery verifier用既有archive索引，核wholeZIP SHA/bytes/CRC與BUNDLE_INDEX每member SHA/bytes/精確inventory；不extract/刪除/覆寫。兩新增negative tests（wrong wholeSHA、valid CRC但member digest篡改）PASS。
- 最終Python3.10.19/3.14.6各246tests PASS，0failures，pip check/9CLI help PASS；實際完整輸出 `output/fault_type_fixed_acceptance/2026-10-01-19-41-26` / `.../2026-10-01-19-41-37`。較早244與237/241 checkpoints保留，最终只引用246；29新增tests。
- `reports/fixed_motor_calibration/result_index.json`提供repo/所有實際root/研究counts/phaseSHA/備份索引；reproduction.md提供不fit的保存結果驗證、必要重跑、診斷、工程fixture與safe恢復限制。
- 19:45:30 最終兩acceptance outputs另存ZIP28727/29090bytes、各12files；原three data_independence ZIP不覆蓋，whole/memberSHA再核對。9ZIP/107members的中間驗證未包含最末兩新env ZIP；最後11ZIP/131members完整驗證另存新timestamp。
- 最後再次唯讀掃描正式90CSV/28910/105D fingerprint相同。Git diff基線到HEAD的openset/Maha/monitor/fault_type_openset/Representation均空；282tracked deletions仍未stage。未修改正式default、PolarMap、binary與kNN factory。
- P5只stage自身文件/新verifier/兩tests/驗收outputs/compact索引/log，不stageraw、formalCSV、largeZIP/joblib或別人的刪除。正常commit+push/remoteSHA核對；成功後追加實際SHA，不預填。
- 完整備份核驗19:46:09–10，11ZIP/131members wholeSHA/CRC/memberSHA/length全部PASS；包含8個本輪新正式研究/驗收包與3個原稽核包。output/fault_type_fixed_delivery/2026-10-01-19-46-09/member_verification.json保存所有ZIP的SHA、bytes、source_root、member count。原三包wholeSHA仍與舊index一致；未extract/移動/刪除任何material資料。
