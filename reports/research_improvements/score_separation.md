# P3 Score Separation

# P3 Score Separation

## 三種分數

- `health_deviation_score`：固定 healthy-only Ledoit–Wolf reference 的偏離，回答「離健康基準多遠」。reference 預設 immutable，版本是 `healthy-reference-v1`。
- `unknown_score`：目前 Open Set detector 分數轉成 `[0,1]` 的未知程度，回答「模型是否認識」。學會新類別後可以下降。
- `direction_familiarity`：固定健康白化空間中，與已知故障方向 cosine 的熟悉程度；另輸出 `nearest_known_direction`。它不是嚴重度。

三者不再共用一個 damage percentage；`estimated_rul` 仍因沒有 run-to-failure 資料維持 `null`。

## Formal replay regression

命令：

```powershell
venv\Scripts\python.exe -m experiments.score_separation `
  --data-root data/formal_local `
  --output-root reports/research_improvements/score_separation
```

固定同一批 100 筆新類別到達樣本，在學會前與以 50 筆 arrival samples 更新後各推論一次。結果位於 `score_separation/summary.json`：

- `health_deviation_score` 平均值前後皆 `0.7177268679`，最大絕對差 `0.0`。
- `unknown_score` 平均由 `0.7177268679` 降至 `0.5581918338`。
- 更新後可出現 `5screws`，未學會前保持 `unknown`；這是同一資料的 known/unknown 角色改變，不是馬達恢復健康。
- `direction_familiarity` 平均由 `0.0` 變成 `0.9988533611`，表示方向資訊新增，不代表健康度變好。

這是 formal data 的 simulated arrival replay；沒有真實時間、人工確認時間或現場部署延遲，因此不宣稱 longitudinal health improvement。
