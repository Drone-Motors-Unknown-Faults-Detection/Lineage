# synchronized_raw_schema.json 的用途

2026-10-02 依 [schema](synchronized_raw_schema.json)、[parser](../core/synchronized_raw.py) 與 [feature extractor](../core/synchronized_features.py) 核對。

它是「原始錄製設定的填寫規格」，採 JSON Schema Draft 2020-12。原始訊號另存 CSV/TSV，使用者提供自己的 JSON config；schema 本身沒有波形、不會訓練模型，也不是完成採集的證明。

## 各欄位管什麼

| 欄位 | 用途 |
|---|---|
| recording_id / motor_id / session_id / run_id | 識別錄製、馬達與採集群組；必填字串，不能把沒有來源的假 ID 當獨立性證據 |
| raw_sample_count | 原始資料列數，parser 會與實讀列數比對 |
| sample_rate_hz | 取樣率；schema 允許 null 以保留未知，FFT 特徵生成仍需要正值，fresh qualification 另需證據 |
| parser | 明確 CSV/Tab 分隔、零起算 header row、完整 expected_columns 與通道對照 |
| quality | 固定物理界限／飽和／窗平均偏移規則；空物件可做不加這些界限的預覽，不代表感測器品質已通過 |
| windows.length / stride | 窗長與步長，單位是樣本數；stride 小於 length 會重疊，schema 沒有禁止，fresh guard 另查 raw intervals |
| windows.gap_rule / bad_point_rule | 現行僅接受 reject：缺點或壞點所在整窗排除，不刪點後拼接時間軸 |
| synthetic | 明確標示合成工程資料，不能作真實模型成績 |

通道固定為 current、x、y、z、delta_t。delta_t 可以直接讀欄位，或用同一列 motor_temp−room_temp 算出。所有通道必須來自同一檔案的共享列；分檔且沒有 clock bridge 的同步不支援。時間欄位若有提供，其語意須明確為 relative_seconds，程式不假設 X_Value 就是時間。

## 誰真正做檢查

目前 `experiments/synchronized_raw.py` 與 `synchronized_features.py` 直接讀 `--config`，再呼叫 Python parser；沒有自動載入此 schema，也沒有把 JSON Schema validator 當 runtime gate。

這份 schema 只描述部分結構：delta_t 或雙溫度的替代要求、完整 quality 限制、rpm、物理證據等未全部編成 schema 關鍵字。實際欄位與值的檢查分布在 parser、timebase audit、feature generator 與 fresh guard。只通過 JSON 結構驗證仍可能被程式拒絕。

## 使用入口

[raw_config.template.json](../examples/raw_config.template.json) 是填寫起點；其中 null 與 documented nominal fs 必須依真實檔案／來源核對，模板本身不能直接代表有效錄製。

在 repo 根目錄，用已確認的檔案及設定：

```powershell
.\.venv310\Scripts\python.exe -m experiments.synchronized_raw --raw-file incoming/raw.csv --config incoming/raw_config.json
.\.venv310\Scripts\python.exe -m experiments.synchronized_features --raw-file incoming/raw.csv --config incoming/raw_config.json --incoming-root . --variant aligned_only
```

這裡的 incoming 路徑為使用者輸入範例，不宣稱已存在資料。程式另產出 logs/output：raw audit、features.csv、manifest、raw_window_audit 與 version_registry，保留 raw SHA、原始區間與拒絕理由，不覆寫 formal data。詳見 [raw 手冊](experiments/synchronized_raw.md)、[features 手冊](experiments/synchronized_features.md)。

## 它不能證明什麼

文件支持的 nominal 10,000 Hz 不等於這次錄製的實測 fs。即使各通道同列且有 attestation，程式也不能獨立認證 DAQ 硬體。序號、使用時數、單位、方向、校正、安裝、負載與採集時間缺證據就保留未知；fresh-data gate 會繼續檢查來源、曝露、群組與覆蓋，不能因欄位齊全改成 PASS。
