# fault_type_solver_report：train-only 損失重算與失敗分析

2026-10-02，先手冊再程式。此程式驗證27個已鎖定solver診斷，不新增outer推論、不調參。方法、原始來源與可反駁假說見 [diagnosis手冊](fault_type_solver_diagnosis.md)。

## 方法與資料

讀solver protocol/diagnosis seal及27 checkpoint SHA；沿用原Q parent的train-fit harmonic69。每fold/seed只load train feature rows，使用同一class×RPM20-row subset及target k3；重算保存weights的smooth/hard objective、projected gradient。maxiter150/600、maxfun500/2000、τ=.1、ridge=.01等固定。報告每motor/seed/solver收斂狀態、停止理由、time、hard loss與gradient，不把seed當獨立馬達。

另核對原Q lock來源/model SHA；原成功的3個metric weights須與hard150一致，原失敗的6個只有例外，仍沒有原失敗權重可比。報告smooth150與hard600的訓練差異，不能據此宣稱測試分數改善。calibration/test/selection input IDs空；不選部署winner。science Python3.10.19，任何SHA或角色不符即拒絕。

## 文獻與預期判準

Weinberger與Saul（2009），Distance Metric Learning for Large Margin Nearest Neighbor Classification，JMLR10:207–244，[原文](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。Rennie與Srebro（2005），Fast Maximum Margin Matrix Factorization for Collaborative Prediction，ICML，DOI10.1145/1102351.1102441，[作者原文](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf) §3.3 Eq9。此report是本地工程驗證；沒有改編新模型。

預期：來源與IDs完整，保存loss/gradient可重算、原成功hard150可重現；不一致就是工程FAILED。若smooth150較hard150提高收斂覆蓋，而hard600也改善，仍有預算與平滑的競爭解釋，不宣稱單一物理原因。資料獨立性/歷史曝露缺口不改PASS。實測寫在reports/continuous_research/solver_findings.md，不回填成預期。

## CLI與影響範圍

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_solver_report --protocol output/fault_type_solver_lock/2026-10-02-23-46-28/protocol.json --diagnosis output/fault_type_solver_fit/2026-10-02-23-51-52/diagnosis.json --q-lock output/fault_type_continuous_fit/2026-10-02-18-42-53/locked_study.json --data-root data/formal_local
```

run(pools,...)與main()，setup_run logs/output；新增 experiments/fault_type_solver_report.py 與 tests/test_fault_type_solver_report.py。唯讀 core/fault_type_smooth_margin.py、core/fault_type_continuous.py、experiments/fault_type_solver_diagnosis.py、experiments/fault_type_continuous_study.py、既有features及parent驗證器。原Q科學來源與新solver protocol已封存，不修改。
