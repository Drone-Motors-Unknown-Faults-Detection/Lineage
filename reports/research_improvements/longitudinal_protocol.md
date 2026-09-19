# P8 同一顆馬達長期退化 protocol

README 已指出 T1/T2/T3 是不同馬達個體；本任務不把三者拼成一條生命週期。`health.longitudinal.LongitudinalObservation` 強制保存 motor/session、timestamp、累積運轉時間、工況、三種分數、inspection、maintenance、part replacement 與 failure endpoint。

先做：

- 每顆馬達各自的 trend stability、change point、event-level false alarm、degradation rate、early-warning lead time。
- 事件與維修前後要有明確 timestamp；資料不足時只輸出 descriptive trend。

只有同一顆馬達具備多次長期紀錄、明確 failure endpoint、足夠 run-to-failure trajectories 後才可研究 RUL。現在 formal data 沒有這些資料，`estimated_rul` 必須是 `null`；health distance 不能叫 remaining-life percentage。
