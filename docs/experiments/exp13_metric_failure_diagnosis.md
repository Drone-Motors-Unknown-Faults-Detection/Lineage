# 實驗13：封存後失敗診斷

2026-10-03。本手冊先於診斷程式。僅讀取已封存／已重推核對的預測，禁止修改模型、參數或threshold。

方法：逐fold／seed／RPM／healthy、known faulty、unknown分組，列樣本數、已保存normalized score的0/25/50/75/95/100百分位、固定threshold拒絕率、分類器輸出分布。這是事後描述，不掃描最佳threshold。不同fold不做混合score排序；NaN或非有限值拒絕；空組N/A。classifier投票／energy輸出不冒稱detector nearest class。

以歷史Q01/Q03核對本批E01/E03：全部9折seed、逐樣本ID／真值／SHA／分類／分數／threshold應完全一致。核對過去有界協定／曝露聲明與原manifest，不清除曝露、不重新擬合、不將重推視為新獨立試驗。所有E結果與失敗理由保留。

## 程式碼與輸出

`experiments/fault_type_metric_failure_diagnosis.py`，run(...)／main()，使用既有predictions、check_rows、source seal。`tests/test_fault_type_metric_failure_diagnosis.py`。`logs/fault_type_metric_failure_diagnosis/`、`output/fault_type_metric_failure_diagnosis/`。不改core／factory、`experiments/health/`或`web/`，均N/A。算法來源／normalized score定義沿用exp13手冊；百分位是描述統計，不是新檢測器。
