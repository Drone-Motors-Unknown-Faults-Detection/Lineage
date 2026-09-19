# P7 現場資料收集 protocol

目前沒有把未驗證硬體資料混入正式資料集。新資料先放 candidate quarantine，通過 metadata、checksum、duplicate、schema、split fingerprint 後才可成為新 protocol 的 train/calibration/discovery/update/test pool。

## 優先實驗

1. **Early micro-loosening**：停機後調整可量測的預緊扭矩，螺絲數量固定、至少多個 torque levels，每次記錄工具、位置、motor/session、拆裝次數。
2. **Same count, different position**：固定鬆動數量，只改鬆動位置並重複拆裝，區分程度和位置。
3. **Healthy operating changes**：RPM、load、cold-to-hot、voltage/power，先估 healthy FPR。
4. **Confirmed bearing defect**：只有安全確認 defect/severity 後才收錄。
5. **Controlled imbalance**：固定、防護測試台；不在飛行中用撞擊模擬。

## 每筆必填 metadata

`motor_id`、`session_id`、`timestamp`、`screw_position`、`measured_torque_nm`、`rpm`、`load`、`temperature_c`、`voltage_v`、`current_a`、`sensor_quality`、`operator`、`maintenance_action`、`source_file`。`core.field_data.FieldSampleMetadata` 會檢查 ISO timestamp、數值有限且 torque/RPM/load 非負；`write_field_manifest()` 會拒絕重複 identity。

## 安全與資料閘門

- 所有機械調整完全停機；旋轉件只在固定、防護測試台。
- 記錄停止條件、風險控制、操作員與維修動作。
- 新檔案先計 SHA-256；不能覆寫 raw archive，也不能直接複製進 `data/`。
- schema/checksum/duplicate/split manifest 完成前，candidate 只能用於離線資料品質檢查。

目前狀態：**規格與 metadata validator 已完成；真實微鬆動、位置變化、軸承／不平衡資料尚未取得**。因此本輪不宣稱任何現場故障嚴重度或 RUL 結論。
