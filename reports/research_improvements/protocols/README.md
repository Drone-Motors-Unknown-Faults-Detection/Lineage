# Immutable split protocol

`formal_seed42/` 是目前正式資料的 P1 protocol artifact：

- `Step-1` 的 8screws → `initial_known_train`。
- `Step-2` 的 8screws → `healthy_calibration`；7screws → `validation`；6/5screws → `discovery_stream`。
- `Step-3` 的 6/5screws → `human_confirmed_update_pool`。
- `Step-3` 的 8/7/4/3/2/1/3_14/4_146screws → `immutable_test`。

每個 raw-derived CSV 都是不可切開的 group；同一檔案的 windows 不會跨 split。正式 CSV 沒有可信的 `session_id`、timestamp 或 motor 個體 metadata，因此 protocol 只宣稱「source-file group disjoint」，不宣稱已完成真正的同一馬達時間切分。這是資料限制，不是被忽略的警告。

執行：

```powershell
venv\Scripts\python.exe -m core.continual_protocol `
  --data-root data/formal_local `
  --output-root reports/research_improvements/protocols/formal_seed42 `
  --seed 42
```

`split_fingerprints.json` 固定 immutable test 的 sample/file IDs；`split_manifest.json` 保存 source hash、group、split 與 artifact 指標；`sample_fingerprints.json.gz` 保存完整 sample fingerprint sidecar；`split_summary.json` 保存 class/condition/count 統計。變更 update budget 不會改這些 split artifacts。
