# 補採與 ingest 契約（不是已完成採集）

目的：取得尚未曝光、來源可核對的新錄製。現有三ZIP/90CSV與其複製、unclean
衍生列不算新採集。新 session 可檢驗同一馬達跨錄製；新 motor 才能支持跨新個體
主張，兩者不能混稱。三顆馬達文件身分不必重證明，未知 facts 不猜測補齊。

## 實驗者最少要提供的事實

- 真實 motor ID（可為貼紙代碼，不强制公開 serial）、session ID、run ID；
  是否同一次連續錄製、何時停止重啟、是否拆裝、是否更换個體。
- timezone-aware 採集時間、原始未刪點未切窗的訊號檔、SHA、樣本數，
  時間欄位定義與實際 sample rate；原始 interval 使用 [start,end) sample index。
- channel單位、軸向／校正／感測器型號、安裝、負載、實測或設定 RPM、
  healthy及螺絲配置的操作確認。未知工時/老化程度可null，不能聲稱量化老化。
- 每row的raw recording SHA與interval、feature extractor版本/SHA、
  共同channel時間對齊證據、清理mask與window length/stride。
- 操作者的實際採集紀錄或attestation pointer。checksum只能驗證bytes，
  不能取代實驗者對「重新錄製／更换馬達」的真實確認。

建議known10配置各覆蓋6000/8000/11000RPM；final每類至少30個非重疊window
及2個符合主張的独立group是此研究門檻，不是power保證。若新motor主張需
2個新個體/類；若new_session主張需2個新session/類。不要用同一run拆檔充數。
train/validation/calibration/final應按實際group凍結。硬體成本可先限制主張，
但不可暗降已鎖定的完整度標準以換取PASS。

## 輸入 JSON 形狀

incoming root 保持唯讀，feature_files每個CSV須105 numeric columns。manifest：

```json
{
  "feature_version": "formal105_historical_v1_semantics_audited_20261001",
  "extractor_sha256": "ACTUAL_CODE_SHA256",
  "physical_contract": {"sensor_units": "...", "orientation": "...", "calibration": "...", "mounting": "...", "load": "..."},
  "acquisition_evidence": "operator-record/reference, not invented",
  "feature_files": [{"path": "features.csv", "sha256": "ACTUAL_FILE_SHA256", "windows": [{
    "row_index": 0, "motor_id": "ACTUAL_ID", "session_id": "ACTUAL_SESSION", "run_id": "ACTUAL_RUN",
    "label": "8screws", "rpm": "8000rpm", "acquisition_timestamp": "2026-10-01T10:00:00+08:00",
    "attestation": "actual acquisition record reference", "raw_source_file": "original_signal.csv",
    "raw_source_sha256": "ACTUAL_RAW_SHA256", "source_interval": [0, 10000],
    "raw_sample_count": 10000, "sample_rate_hz": 10000, "physical_time_alignment_verified": true
  }]}],
  "manifest_checksum": "computed by core.fault_type_final_guard.seal(manifest, 'manifest_checksum')"
}
```

上例只有一row，**不能通過正式final coverage**。不同row需要完整metadata；
不要把以上 placeholders、alignment=true 或日期直接當實際採集事實。
步驟：先由實際檔案建立JSON、用seal函式計算checksum，之後不可改內容不重簽。
工具阻擋原始或特徵SHA失配、metadata漏列、路徑越界、缺必要physical事實。

```powershell
.\venv\Scripts\python.exe -m experiments.fault_type_ingest --incoming-root 'D:/YOUR_VERIFIED_INCOMING_ROOT' --manifest 'D:/YOUR_VERIFIED_INCOMING_ROOT/manifest.json'
# 僅驗證ingest，不評估；locked/ledger/claim 三者齊全才啟動qualification gate
.\venv\Scripts\python.exe -m experiments.fault_type_ingest --incoming-root 'D:/YOUR_VERIFIED_INCOMING_ROOT' --manifest 'D:/YOUR_VERIFIED_INCOMING_ROOT/manifest.json' --ledger 'PATH/exposure_ledger.json.gz' --locked 'PATH/locked_config.json' --claim new_session
```

結果 ELIGIBLE_WITH_ATTESTED_PROVENANCE 仍非模型可靠性的PASS。舊資料 physical
contract未知，未來可能必須在新verified資料重新train/val/cal或有bridge calibration，
不能只靠incoming metadata就補證歷史物理相容性。原始DAQ samples的真實個數
與物理單位仍需來源格式解析/人工紀錄交叉核對，宣告欄位不等於測量證明。
