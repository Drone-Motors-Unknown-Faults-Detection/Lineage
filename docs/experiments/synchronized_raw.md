# synchronized_raw 技術手冊

2026-10-02 補寫既有 parser 預覽；程式與採集事實未變。

## 方法與 CLI

單一 CSV/TSV 的 current/x/y/z/delta_t 共享原始列。delta_t 由原欄位或同列雙溫度差提供。依明確 header/delimiter/mapping 實讀，核對 raw_sample_count；檢查 sample index、時間倒轉／重複／jitter（相對容忍 .001），固定物理品質界限。窗長／stride 由 config 提供，不拼接刪點、不插值；壞點或缺點整窗 reject。不訓練模型，沒有 train/test split 或 seed 隨機抽樣。

```powershell
.\.venv310\Scripts\python.exe -m experiments.synchronized_raw --raw-file incoming/raw.csv --config incoming/raw_config.json
```

輸入路徑為自行準備的範例。setup_run 保存 raw_audit.json/log；詳見 [schema 用途](../synchronized_raw_schema.md)、[template](../../examples/raw_config.template.json)。

## 出處

解析欄位參考 Ancestor Step1 固定版 `1ef4a891`（程式檔頭），不 import legacy。共享列、reject-only、明確 evidence level 是本專案操作約定，沒有宣稱由特定論文提出。JSON Schema 結構參考 [官方 Draft2020-12](https://json-schema.org/draft/2020-12)。

## 預期與反駁

預期保存原 raw SHA/index/interval，格式錯誤拒絕，未知物理證據保持 INCOMPLETE；合成只能工程檢查。若通道錯位卻通過、刪點壓縮時間軸或無來源就宣稱硬體 verified，工程假設不成立。測試通過不代表 fault classification 可靠。

## 程式範圍

`experiments/synchronized_raw.py`、`core/synchronized_raw.py`、`core/logger.py`；讀取 `docs/synchronized_raw_schema.json` 作說明，runtime 不自動讀 schema。後續抽特徵另見 [synchronized_features](synchronized_features.md)。
