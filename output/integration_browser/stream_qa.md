# 串流瀏覽器 QA

2026-10-08，in-app browser，http://127.0.0.1:8612/；真實 T1/8000rpm、seed42、Mahalanobis-LW。

- 原即時展示 start，再切實驗一：背景小窗仍從 #2 增至 #343，顯示來源／分數／EWMA，畫布有更新；暫停後停在 #400。
- exp1 400筆/秒：SSE 完成9.86秒（含播放時間），healthy holdout64筆、FP10.9375%，九未知配置全池2736筆拒絕率100%、AUROC1。結果保存 exp1_2026-10-08-13-37-36.json。這是同工況工程回歸，與跨馬達 N5 結果不可混用。
- exp1 20筆/秒第二次開始後按「停止」：顯示「已停止（伺服器端同步中止）」、控制恢復；沒有把中斷 run 當成完成結果。
- 停止後 exp3 可開始。n_trials=2、400筆/秒：完成0.62秒、四次劇本均判對；A延遲61/56筆、B8/7筆；最終結果與原 main 配對一致。
- exp4 完成0.7秒，geometry/direction/severity 都有畫面與保存的完整 JSON。PolarMap core 未修改。
- exp8_monitor 卡片沒有「邊跑邊畫」，保留原批次按鈕；#35 未修復，不冒稱可播放所有故障配置。
- exp3 n_trials=0：畫面明示「必須在1～100」，無完成結果；改回2後原批次「執行」正常完成0.08秒，證明錯誤後鎖可恢復。
- console 未觀察到 error/warn。完成後關閉自己的測試頁；沒有部署或對外開放。

截圖：stream_exp1_done.png、stream_exp3_done.png、stream_exp4_done.png、stream_invalid_parameter.png、stream_batch_recovered.png。
完整 SSE 斷線、batch互斥、close例外、非有限速率等由 AsyncHTTP fixture tests 覆蓋；沒有把 fixture 當成實體採集。背景 live 的樣本檔只作操作紀錄，不作 sealed 研究預測。
