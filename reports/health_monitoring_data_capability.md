# Health Monitoring 資料能力稽核

## 稽核範圍與結論

本報告只讀取使用者指定的唯讀資料根目錄：

```text
D:\schoolshit\fcu\專題\馬達研究
```

raw ZIP、notebook、checkpoint 與任何來源檔案均未修改、移動、重新命名或刪除。證據來自既有唯讀稽核成果：`reports/raw_data_audit/README.md`、`condition_summary.csv`、`raw_validation.csv`、`feature_validation.csv`、`formal_contract_mapping.md`，以及目前 Lineage 的 loader／Open Set／exp6 程式。

### 最高可支援 Level：Level A

目前資料可以可信支援：

- 健康基準與相對 `health_index`。
- `degradation_score = 1 - health_index`。
- Mahalanobis／k-NN Open Set score。
- unknown rejection。
- 在一個明確的串流 session 內做相對趨勢與告警狀態追蹤，但只能稱為「相對健康分數趨勢」。
- data-quality validation 與 uncertainty／abstention 欄位。

目前資料不能可信支援：

- 真實物理損壞百分比。
- 真實 supervised severity label 或 ordinal severity ground truth。
- bearing、winding、ESC 等真實故障原因 classifier。
- 同一實體馬達的長期劣化 trajectory。
- run-to-failure RUL、time-to-failure 或 survival model。
- 把 9 個 motor×RPM 工況的排序當成一顆馬達逐漸損壞。

因此本階段不建立假 severity label、假 fault-cause label，也不輸出數值 RUL。

## 已確認的資料事實

| 觀察 | 證據 | 判定 |
|---|---|---|
| 九個工況存在 | `condition_summary.csv`：T1/T2/T3 × 6000/8000/11000 RPM | 已確認 |
| 每工況 raw 覆蓋 | 每工況 50 檔 = 10 config × 5 channel；450/450 raw CSV 可讀 | 已確認 |
| Raw window | 每個 raw CSV 10,000 rows；採樣率文件為 10 kHz | 已確認 |
| Clean feature | T1/T3 各 30 個 105 維 clean CSV；T2 原始 CSV 完整但沒有原生 myfeature.zip | 已確認 |
| Label 來源 | `class_name` 來自資料夾：`8screws`、`1screws`…`7screws`、`3_14screws`、`4_146screws` | 已確認 |
| Known／unknown contract | `8screws` = healthy known；`1screws`–`4screws` = known fault；其餘五種 = unknown fault | 已確認為專案資料契約，不等於物理故障原因 |
| Raw channels | `Acceleration_X/Y/Z`、`Current`、`Delta_T`；T2/T3 有 X/Y/Z filename aliases | 已確認 |
| Feature order | 105 維欄位由既有 feature contract 定義 | 已確認 |
| Data root | raw source 是巢狀 ZIP，不是 loader 直接讀取的平面 `data/Step-*` | 已確認 |

## 資料能力表

| 能力 | 資料是否支援 | 證據 | 可實作功能 |
|---|---|---|---|
| Binary fault | 部分支援 | config directory 可區分 healthy／known／unknown contract | 保留原本 `is_fault` 0/1；不能當成一般化實體 fault label |
| Fault type | 不支援可靠原因 | 只有 screw configuration 與 known/unknown role，沒有 bearing／winding／ESC label | `fault_type=unknown` 或 `uncertain`；不可訓練原因 classifier |
| Severity | 不支援真實 severity | 沒有 severity 欄位、人工損傷百分比或 ordinal label | 只能輸出 calibrated relative stage |
| 時間順序 | 不足 | raw CSV 有固定 10,000 rows，但 header 是重複 channel 名稱，沒有 timestamp column | 只在明確 stream session 追蹤輸入順序；無法宣稱跨檔 chronology |
| 同一馬達長期追蹤 | 不支援 | T1/T2/T3 是資料路徑／階段代碼，沒有 physical motor unique ID | 必須要求使用者提供 motor_id 才能啟用 per-motor history |
| 同一 experiment session | 不支援 | 沒有 session_id 或連續實驗事件欄位 | 每次啟動建立新的 session；不可跨 session 拼接 |
| 健康到故障連續過程 | 不支援正式證據 | 9 工況是獨立 condition/config archive；目前沒有同一 motor 的健康→失效紀錄 | 可用 synthetic exp3 做方法 smoke，但不能稱為實際劣化驗證 |
| 只有獨立正常／故障樣本 | 目前主要是 | 每個 config 是獨立 raw archive／feature pool；沒有可靠 transition event | Level A 相對健康 baseline |
| 故障嚴重程度 | 不支援 ground truth | screw 數量可作資料條件名稱，但不是測得的物理損壞比例 | 以 health score threshold 產生 relative stage，明確標註非物理 severity |
| 故障原因 | 不支援 | 無 cause、maintenance、inspection 或 failure-mode metadata | taxonomy 只作待收集資料規格，不建立假 labels |
| 失效時刻 | 不支援 | 沒有 failure endpoint、run-to-failure 或 time-to-failure 欄位 | `estimated_rul=null`、`rul_available=false` |
| 維修／更換零件 | 不支援 | inventory／manifest 沒有 maintenance event | 未來資料收集欄位 |
| 負載、RPM、溫度、電壓 | 部分支援 | RPM 來自 condition path；Current 與 Delta_T 是 sensor channels；沒有 verified payload、voltage、ambient temperature metadata | condition-aware baseline 只先以 motor/RPM key 分組；不得把 RPM change 當 degradation |
| Vibration | 支援為訊號特徵來源 | Acceleration X/Y/Z raw channels 與 105 維 feature | health／Open Set score；不能直接命名故障原因 |
| ESC information | 不支援 | 無 ESC ID、firmware、telemetry 或 fault code | 未來資料收集欄位 |
| Remaining life | 不支援 | 缺 motor ID、longitudinal order、failure endpoint、多條 trajectories | 永遠輸出 null，直到資料契約滿足 RUL 條件 |

## 9 工況的正確解讀

9 個工況是 `motor code × RPM operating point` 的資料條件，config 是螺絲配置條件。它們不是已證明的同一顆馬達連續劣化時間軸。`1screws` 到 `8screws` 可以作為相對條件／偏離健康程度的研究變數，但不能直接解讀成「損壞 1% 到 8%」或按數字排序成真實時間。

因此：

1. `condition` 必須保留 motor／RPM context，避免把 operating-condition shift 當成 fault。
2. health baseline 至少按 `motor/RPM` 建立或驗證，不能直接混合九個分布。
3. trend history 必須以呼叫端提供的 `motor_id/session_id` 隔離；若缺少 ID，系統只能回傳 `insufficient_history`。
4. exp3 的 A/B 劇本是 synthetic stream 行為測試，不是 raw data 的 physical degradation ground truth。

## Fault taxonomy evidence

目前資料沒有足夠證據把以下候選類型對應到 label：bearing wear/damage、rotor/propeller imbalance、shaft misalignment、friction、winding、phase loss、insulation、ESC、overheating、overload、sensor drift、EMI 等。現階段 taxonomy 應只作資料收集表，不可拿來產生 classifier target。

若未來資料確認一筆樣本可能同時有多個故障原因，輸出設計應採 multi-label；在目前資料中則使用：

- `fault_type="unknown"`：Open Set 判定為未知。
- `fault_type="uncertain"`：不是 unknown，但沒有可靠原因 label 或 confidence 不足。
- 不輸出 `bearing_wear` 等未被資料支持的名稱。

## Health Monitoring 實作邊界

後續實作可以新增 Level A baseline：

- 使用現有 105 維 feature、RobustScaler 與已驗證的 Mahalanobis／k-NN detector。
- calibration 只使用 known train/calibration；test 不選 mapping 或 threshold。
- 輸出 calibrated relative health index，不宣稱 RUL／物理損傷百分比。
- 在 stream API 中以 `session_id` 隔離 history；缺 timestamp/motor_id 時明確回報 `insufficient_history`。
- unknown 時強制 `fault_type=unknown`，不讓 closed-set nearest class 覆蓋 Open Set rejection。

## 必須補收的資料

要升級到 Level B–E，至少需要：

- physical `motor_id`、motor model、propeller、ESC、battery/power supply。
- timestamp、cumulative operating time、session_id、完整 experiment ID。
- RPM、commanded throttle、payload/load、voltage、current、temperature、ambient temperature、vibration、acoustic（若有）。
- mounting configuration、maintenance/replacement event、fault injection／observed cause、severity、failure endpoint。
- 多顆馬達、健康到劣化的重複 longitudinal trajectories，以及獨立 motor-level train/validation/test split。

在這些欄位存在前，RUL、真實 severity 與 fault-cause diagnosis 都維持 disabled。
