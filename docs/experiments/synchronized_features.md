# synchronized_features 技術手冊

2026-10-02 補寫既有同步 pipeline，不重新產出 formal data。

## 方法、參數与 CLI

先經 synchronized_raw parser/audit/quality/windows，再在同一原始五通道窗口抽取105維。Current15/X25/Y25/Z25/Delta_T15；FFT=2|FFT|/n、無 detrending/window function、前 n//2 bins、三振動軸10諧波 maxima。無隨機訓練／資料切分；length/stride/quality/fs/rpm 必須來自 config，extractor code/settings/numpy/scipy 綁 pipeline ID。

variant 必填：historical105 保留歷史式，aligned_only 保留式但共享窗，corrected_formulas 更正 crest/clearance/degenerate convention，exact_nominal_rpm 用設定 RPM/60；最後一項不等於實測 order tracking。historical105 要求設定10kHz，其他 variant 也需正 fs。schema 允許 null 的 parser preview 不代表能計算 FFT。

```powershell
.\.venv310\Scripts\python.exe -m experiments.synchronized_features --raw-file incoming/raw.csv --config incoming/raw_config.json --incoming-root . --variant aligned_only
```

raw 與 setup_run 的 output 必須都在 incoming-root 內，輸入範例需自行確認。新 CSV/manifest/window audit/version registry 寫 logs/output，refuse overwrite；每 row 保留 rawSHA、[start,end)、品質與 evidence。讀 [重現說明](../../reports/synchronized_pipeline/reproduction.md)與 [schema](../synchronized_raw_schema.md)。

## 出處

105維歷史式由 `core/fault_type_feature_contract.py` 對 Ancestor Step2 稽核，不 import legacy。變體分拆、shared intervals、拒絕非有限值與版本封存是本地操作約定；未將 corrected formula 寫成已有文獻驗證的性能改善。數值運算依 [NumPy FFT 官方文件](https://numpy.org/doc/stable/reference/routines.fft.html)。

## 預期／反駁與已知限制

預期不同 variant 可追溯且正式 CSV 不變。若 window/rawSHA 不可重算、通道不同区間、實際設定不綁版本，工程驗收失敗。方法只有在來源可驗證且相同 split/模型配對時才能比較；synthetic 通過與新 features 生成不能算真實準確率。fresh guard 仍需物理來源與未曝光資格，尚無合格 real final。

## 程式範圍

`experiments/synchronized_features.py`、`core/synchronized_features.py`、`core/synchronized_raw.py`、`core/fault_type_feature_contract.py`、`core/formal_data.py`、`core/fault_type_final_guard.py`。本次只補文件，沒有更動這些程式或數據。
