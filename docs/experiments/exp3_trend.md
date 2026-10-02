# 實驗三：漸進磨損與突發跳變

程式：`experiments/exp3_trend.py`。判別邏輯在 `core/trend.py` 的 `TrendMonitor`。劇本表 `SCENARIOS` 同時被 `web/live.py` 拿去播。

問題：開集分數的時間形狀能否分開「螺絲慢慢鬆」和「一下子換成另一種配置」。

## 實驗方法

1. 用實驗一的方式 `fit_initial()`，監測器停在只有健康類的階段 0。
2. 劇本 A，預期標籤 `gradual`。phase 是 `(配置, 故障混入比例, 筆數)`：
   - `8screws`，比例 0，40 筆
   - `7screws`，0.25，50 筆
   - `7screws`，0.70，50 筆
   - `6screws`，1.0，60 筆
   - `5screws`，1.0，60 筆
3. 劇本 B，預期標籤 `sudden`：健康 40 筆，接著 `4screws` 比例 1.0、120 筆。
4. 比例小於 1 時，其餘機率抽健康 holdout。故障樣本用 `CycleSampler` 在該配置全池上抽。故障開始時間 `onset` 等於第一段的 40 筆。
5. 每一筆呼叫 `TrendMonitor.update(score)`。第一次 `alarm_now` 記下 `kind`、警報時刻與 `transition`，該 trial 結束。
6. CLI `--trials` 預設 20。文件裡那次 40 次重複要自己加上 `--trials 40`。trial `k` 的 seed 是 `seed + 1000 * 劇本序 + k`。

```bash
venv/bin/python -m experiments.exp3_trend --motor T1 --rpm 8000rpm --trials 40
```

## 理論

`TrendMonitor` 不看單點分數的大小，看「分數 > 1」這個旗標的密度。EWMA 為

`ewma ← (1 - α) * ewma + α * 1{score > 1}`

預設 `α = 0.08`。`ewma` 升到 `alarm_frac = 0.5` 且已過 `warmup = 10` 筆才警報。

警報當下回看最近 `window = 120` 筆，數異常比例落在中間帶 `[onset_frac, alarm_frac) = [0.2, 0.5)` 的筆數，記成 `transition`。`transition ≤ sudden_max`（12）標 `sudden`，否則標 `gradual`。用停留時間，是為了不被健康期偶發超線拉長「從起點到警報」的距離。

CUSUM 累積 `(score - 1)` 的正偏移，欄位給展示看，不參與 `kind` 判定。這段判別規則是本專案的操作約定，門檻寫在 `TrendMonitor.__init__`。

## 參考論文

- S. W. Roberts (1959), “Control Chart Tests Based on Geometric Moving Averages,” *Technometrics*, 1(3), 239–250。DOI [10.1080/00401706.1959.10489860](https://doi.org/10.1080/00401706.1959.10489860)。
- E. S. Page (1954), “Continuous Inspection Schemes,” *Biometrika*, 41(1/2), 100–115。DOI [10.1093/biomet/41.1-2.100](https://doi.org/10.1093/biomet/41.1-2.100)。程式只把 CUSUM 當展示統計量。
- 中間帶 `[0.2, 0.5)`、`sudden_max = 12`、`α = 0.08`：本專案操作約定。`AGENT.md` 寫明這兩條線是照實驗一的誤報分數分布拉開的。

## 預期成果

兩個劇本的警報率都應接近 1。劇本 A 的 `kind` 應以 `gradual` 為主，劇本 B 以 `sudden` 為主。突發的警報延遲（`alarm_t - onset`）應短於漸進。若兩者的 `transition` 大量重疊，12 筆這條切線就沒有把兩種節奏分開。

## 已記錄的實測

[Experiments_Guide.md](../Experiments_Guide.md) 記載 T1/8000 rpm、40 次：兩劇本警報率皆 100%，判別正確率各 98%。突發平均 7.7 筆警報，漸進平均 49.8 筆。中間帶停留大致是突發 5–13 筆、漸進 12–60 筆。CLI 預設仍是 20 次，和這次紀錄的 40 次不同。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp3_trend.py` | `SCENARIOS`、`iter_stream`、`run`、`main` |
| `core/trend.py` | `TrendMonitor.update` |
| `core/monitor.py` | 階段 0 的開集分數 |
| `core/data.py` | `CycleSampler` |
| `web/live.py` | `from experiments.exp3_trend import SCENARIOS, KIND_DISPLAY`，逐筆 `trend.update` |

輸出：

- `logs/exp3_trend/{時間戳}.log`
- `output/exp3_trend/{時間戳}/trials.csv`
- `output/exp3_trend/{時間戳}/summary.json`

### 散在其他位置的相關檔案

- 測試：沒有專屬測試。
- Web：`web/live.py` 用 `TrendMonitor` 與 `SCENARIOS`；`web/static/index.html` 的「變化點分析（實驗三）」卡。
- 已提交紀錄：`logs/exp3_trend/`、`output/exp3_trend/`（3 次執行）。
- 另一套趨勢邏輯 `experiments/health/trajectory.py` 屬於實驗八，兩者差別見 [health_and_reports.md](../health_and_reports.md) 第 1.3 節。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 4 節。
- Web 實驗頁：頁首「實驗三」，`web/experiments.py` 的 `CATALOG` 項目 `exp3` 呼叫本程式的 `run()`，畫面在 `web/static/experiments.js` 的 `RENDER.exp3`；結果存到 `output/web_server/{ts}/experiments/exp3_{時間}.json`。
