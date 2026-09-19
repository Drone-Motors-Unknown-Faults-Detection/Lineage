# P9 Product Features

## 已建立的可攜 schema

- `health.product.FaultEvent`：event ID、時間、motor/condition、最大健康偏離、最小 conformal p、unknown、代表樣本、sensor quality、人工 disposition、model version。
- `HumanAnnotation`：confirm/reject/merge/split/comment，包含 annotator、時間、原因與備註；不把 dataset ground truth 偷塞進 real mode。
- `ModelVersion` + `RollbackGuard`：父版本、sample IDs/replay fingerprint、calibration/reference version、before/after metrics、artifact checksum、rollback pointer；超過 old-class forgetting/FPR guardrail 時不允許部署。
- `ExperimentReport`：split fingerprint、seed、commit、parameters、feature type、metrics、status/error。
- `health.sensor_quality.assess_sensor_window`：diagnosis 前先產生 sensor warning。
- `health.stream.CsvReplayAdapter`：CSV replay 與未來 live adapter 共用 `StreamPacket`，統計 dropped/out-of-order。

## 尚待接到 UI／真實串流

目前 schema、guardrail 與 replay adapter 已有 unit tests；Web UI 的 event card、annotation 操作、rollback 按鈕與真正設備 socket 尚未接線。部署前仍需量測 end-to-end latency、throughput、backpressure、dropped/out-of-order recovery，並把每次 update 的 artifact checksum 寫入正式 model registry。
