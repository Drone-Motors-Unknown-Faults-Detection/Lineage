# 瀏覽器實測紀錄

2026-10-08；Codex in-app browser；本機 http://127.0.0.1:8611/assets/guide.html；真實唯讀 T1/8000rpm、seed42、預設 Mahalanobis-LW。

| 操作 | 畫面實際結果 |
|---|---|
| 首次載入 | 待建基準、尚未擬合；build/start disabled |
| 選 T1/8000rpm、確認資料 | 十來源筆數出現、105維、seed42；沒有自動 fit |
| 建立基準 | 先 busy，後 session1/epoch1；只有健康 known |
| 冷啟動 start/pause | 逐筆 score 更新，暫停後停止 |
| 匿名 S03 inject/start/pause | unknown，拒絕率100%（本 UI run 145 已計入筆）；候選48筆，未顯示配置答案 |
| confirm | 之後才顯示 5screws，last action 已更新；完整配置池重擬合，非 arrival-only |
| 展示／研究模式 | 同 session1/epoch1/t260；沒有重訓；七問 Markdown 表有載入 |
| reset | 確認對話框後 epoch2/t0；未知重回匿名，舊紀錄保留 |
| A 劇本 | 260筆後自動暫停；gradual，t99、transition43、latency59筆 |
| reset 後 B | epoch3，160筆後自動暫停；sudden，t48、transition6、latency8筆 |
| 改選 T3/6000rpm | 尚未重建時 start disabled，畫面明示不能拿舊模型判新工況 |
| 檢查後明確 build | session2/epoch1/t0；新資料來源筆數，舊 session 保存 |
| start 後 reload | 相同 session2/epoch1，停在 t4，未重訓；前端折線重設，後端紀錄保留 |
| 瀏覽器 console | 未觀察到 error/warn |

截圖：guide_trend_a.png（A進行中）、guide_trend_a_done.png、guide_trend_b_done.png、guide_reconnected.png。

busy、未建立先 start、重複／過期確認、錯誤阻擋、empty data、來源缺欄等負面情境由 HTTP／WebSocket fixture tests 驗證；沒有把它們冒稱瀏覽器點擊。Maha/k-NN 算法等價見 navigation_regression summary，不由此 UI 的取樣數推論分類改善。延遲是 CSV 筆數，不是現場秒數或警報延遲保證。
