# 導覽有界配對回歸

事前範圍：T1/8000rpm、seed42、105維；預設LW與kNN各一次。並行重播原LiveDemo與新GuideHub，健康40筆、5screws最多600筆直到候選、模擬確認、確認後60筆；另在重設後各播A260/B160筆。沒有調參、搜尋配置或資料篩選。

成功標準：相同逐筆score/verdict/PCA/EWMA/CUSUM/quarantine/attempts/phase；相同候選出現筆數與確認結果、已知配置、split與summary；來源SHA前後不變。沒有候選如實記false，不自動提高budget或降低閾值。這是計算／呈現回歸，不能當新的盲測可靠性成果。

CLI：python -m experiments.navigation_regression --data-root data/formal_local。run(dataset, seed=42)返回兩方法比較；main透過setup_run("navigation_regression")保存summary。來源是既有core/experiments/web.live計算，方法原始文獻見exp1–3／exp24。GuideHub引用僅為被測操作層；算法仍在core與既有experiments。

範圍：新增experiments/navigation_regression.py；唯讀web/guide.py、web/live.py與正式資料。
