# P5 Field Scenarios

# P5 Field Scenarios

## 已實作的 replay scenarios

`experiments.field_scenarios` 不修改 detector training data，固定使用 P1 immutable test／arrival manifest，並把 ground truth 只留在離線評估：

1. mixed unknown stream（3screws + 4screws 交錯）：HDBSCAN、purity、ARI、NMI、noise、fragmentation/merging。
2. mild→severe、severe→mild、random fault arrival order。
3. healthy condition shift：T3 的 6000/8000/11000 RPM。
4. healthy initialization contamination：0%、1%、5%、10%。
5. sensor anomaly：missing、dropout、saturation、offset/drift、flatline channel、timestamp gap。
6. transient single spike vs persistent event，比較 single 與 consecutive alarm。

執行：

```powershell
venv\Scripts\python.exe -m experiments.field_scenarios `
  --data-root data/formal_local `
  --output-root reports/research_improvements/field_scenarios
```

## Formal replay 結果

結果在 `field_scenarios/summary.json`：

- mixed unknown 共 200 筆，Open Set unknown recall `1.0`；HDBSCAN 2 clusters，purity `1.0`、ARI `1.0`、NMI `1.0`、noise `0`。這只支持目前兩類選定樣本的離線 replay，不代表所有未知故障都能完美分群。
- arrival order 首次未知索引：mild→severe `590`、severe→mild `0`、random `1`；順序差異很大，不能把單一順序的延遲當成部署保證。
- healthy condition shift 的 healthy FPR：T3/6000 `0.0`、T3/11000 `0.0`、T3/8000 `0.007353`。
- contamination 0/1/5/10% 的 unknown recall 約 `1.0/1.0/0.999847/0.997399`；但跨 Stage-3 healthy 的 baseline FPR 已是 `1.0`，顯示目前資料的 stage/domain shift 大於 contamination 效果，不能只用這組資料宣稱 robustness。
- single spike 以 single alarm 產生 1 個 false event、約 36.36 false alarms/hour；consecutive=2 將單點 spike 壓成 0 false event。persistent event 的 event recall `1.0`，平均 delay `1` sample。
- sensor gate 對 missing/dropout、saturation、flatline、timestamp gap 回傳 `sensor_warning`，不應直接當成 motor fault。

所有數字都標為 `simulation_replay_formal_data`。真實設備工況切換、事件邊界、sensor quality 與未知故障 cluster ground truth 仍待 P7 現場收集。
