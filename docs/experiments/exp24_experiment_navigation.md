# exp24：獨立導覽的主線整合契約

## 方法與資料用途

本輪抽取研究分支 `b3d68f145cfa187e208e38cae74bf33f68d7c367` 已實作的獨立導覽，重用 main 的 `LiveDemo`、`ScaleGrowthSession`、`core.openset` 與趨勢流程，不替換 main 首頁、不改距離、切分、門檻、PolarMap 或確認後的模型更新規則。健康 train/cal/holdout 維持 60/20/20，未知配置不 fit。介面檢查來源 SHA 後由使用者明確建立基準；candidate 確認前不顯示未知配置答案。確認是既有完整配置池的模擬標註與重擬合，不是自由人工病因確認，也不是 arrival-only 增量學習。

原研究證據文件從固定 SHA 擷取，依 main 規則改為 `exp24_` 檔名；未帶入的報告與實驗連到固定研究提交，不能誤解為 main 已提供全部研究方法。三顆不同馬達與三 RPM 為九工況；螺絲配置不是獨立病因或退化生命週期。

## 來源

作者 05zhi 與 Codex；導覽原始提交 `1e2a5b4`、busy 快照 `ec446b8`、暫停落盤 `01862fe`、文件 `7256aae`。主線演算法文獻沿用 [exp1](exp1_cold_start.md)、[exp2](exp2_scale_growth.md)、[exp3](exp3_trend.md)、[exp7](exp7_compare_openset.md) 的作者、篇名與 DOI。本輪的匿名介面、SHA 契約及配對驗收為工程操作約定，沒有新演算法或研究成效主張。

## 評估前固定的驗收與反證

用 105 維 fixture 驗證未 fit、只健康 fit、匿名候選、重複／過期確認、busy、錯誤、session 保存、暫停落盤、來源切換與模式不 fit。用可用 T1/8000rpm 真實 CSV、seed42、LW/q95/kNN5 比較 main 原 LiveDemo 與導覽逐筆 score/verdict/PCA/EWMA/CUSUM/quarantine 等欄位，跑相同有界劇本，來源 SHA 前後一致才可標工程等價。任何新增不一致或未知答案外洩使該批次不能合入 main；缺歷史正式90檔不假裝全資料回歸已完成。沒有瀏覽器操作證據就不標 UI 驗收完成。這些測試不支持部署或 fresh final。

## 程式碼與輸出

2026-10-08事前驗收補充：僅在`navigation_regression`保存配對ledger，不改Web科學計算。每筆追蹤實際sampler.draw取得的特徵SHA及配置池有限值列索引（同值多列保留全部候選，不假裝唯一raw ID），比較兩入口相同seed的row IDs、分數與判定。所有fit/cal索引另存，未知配置只有確認後才能出現於fit。兩方法各自相等，方法之間不要求分數相同。本輪可用來源是T1/T3×三RPM共六工況60CSV；實際逐筆驗收以T1/8000為有界操作條件，不擴稱九工況。

| 用途 | 路徑 |
|---|---|
| 入口 | `experiments/navigation_data_contract.py`、`experiments/navigation_regression.py`（run/main/setup_run） |
| 共用不修改 | `core/data.py`、`core/monitor.py`、`core/openset.py`、`core/geometry.py`、`experiments/exp2_scale_growth.py`、`experiments/exp3_trend.py`、`web/live.py` |
| 編排／畫面 | `web/guide.py`、`web/static/guide.html`、`guide.js`、`guide.css` |
| 測試 | `tests/test_navigation_guide.py`、`tests/test_integration_navigation.py` |
| 文件 | `docs/navigation/exp24_*.md`、流程圖 `.mmd/.svg` |
| 紀錄／結果 | `logs/navigation_*`、`output/navigation_*`、`logs/web_guide`、`output/web_guide`；整合索引在 `docs/integration_20261008` |

```powershell
python -m web.guide --data-root D:/schoolshit/專題/src/Lineage/data --port 8611 --seed 42
python -m experiments.navigation_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42
```

原 `python -m web.server` 與主線實驗頁仍保留。導覽預設資料根為 `data`，可用 CLI 指向唯讀現有資料。實測結果另記整合報告，不回填成事前預期。
