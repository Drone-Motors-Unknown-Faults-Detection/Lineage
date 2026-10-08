## 合併範圍

已備份 main 的64cb71d到 `backup/main-before-integration-20261008-131410`，兩種遠端查詢SHA相同。只整合：

- 固定研究b3d68f的獨立導覽與exp24七問文件；不覆蓋core、原首頁或health搬家。
- JW-Albert的PR #36／544d4ed中exp1/3/4 iter_run、SSE與背景小窗。排除health_monitor與health串流，#35/#36不自動關閉。
- 最小編排修補：close例外也釋放鎖、拒絕非有限速率與非物件參數；新增顯式localhost綁定選項以安全做本機QA，原預設不變。

## 證據

Python3.10.19。main既有76測試、完整候選111測試均0failed/errors/skipped；pip check與四CLI、兩JS語法檢查通過。同來源seed42導覽1190逐筆差異0；exp1/3兩detectors與exp4對原main共5組完全相同。瀏覽器實際驗證build/confirm/reset/mode/dataset/reload、SSE完成、停止、錯誤後批次恢復。負面測試與ABORTED紀錄保留。

研究defaults與core未修改：105維、Mahalanobis-LW/q95、kNN5 factory、PolarMap保留；資料唯讀60檔不是歷史90檔，未重跑2490研究。source branches、所有備份、原checkout保持，無tracked deletions／data／大型ZIP／secret提交。其他研究模組仍待主線相依驗證，保留固定來源，不升級FAILED或UNKNOWN研究結論。

詳細報告 `docs/integration_20261008/integration_report.md`，機器索引manifest.json，逐批commit/ref/tests在execution_log.md。給老師入口 `docs/navigation/exp24_README.md`。D槽證據ZIP29entries全CRC通過。

請以目前候選SHA核對checks/reviews；不使用admin bypass、不刪head branch。合併後fetch main再跑111項驗收與必要配對，補存delivery紀錄。

Co-authored-by: Codex <noreply@openai.com>
