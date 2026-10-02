# 持續研究盤點：2026-10-02 Asia/Taipei

實際checkout：`C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree`；branch research-improvements-20260920；啟動HEAD 758674bcf73942bbf7feb21971c39035bb70a448。282 tracked deletions保持未stage，其他歷史未追蹤產物不納入本輪。
盤點：output/fault_type_continuous_inventory/2026-10-02-18-33-25/inventory.json，seal 5b19032a7645f4e7dc87636facc981d3960540cfc0d1655b12f90b2e02833662。兩個result_index的41個artifact完整SHA、9個parent模型SHA、234 fit audits與資料來源核對；沒有refit/reinference。

正式資料90 CSV/28,910 rows/105維，fingerprint c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。
歷史2490研究、198 accuracy、literature 624/630（6 INCOMPLETE）、mechanism81已完成，不重跑不變模型。authoritative索引 reports/literature_expansion/result_index.json 與 reports/mechanism_research_v2/result_index.json。

歷史motor等權：C02/M fault accuracy26.61%、unknown recall18.44%、health alarm26.87%；C17/M known39.29%、fault30.43%、F1 .285、unknown8.44%、health14.13%；C24 fault30.91%；D01 C17clf+C02/M unknown18.44%，但T1未知0、2screws三motor0、最差健康100%。這是既有結果非新批次成績。

Python3.10.19/sklearn1.7.2/numpy2.2.6/scipy1.15.3為科学環境，Python3.14.6只native tests/CLI，不跨版本joblib。pipcheck正常；pipfreeze exit2，editable Git中文路徑WinError3。原失敗18:29:23保留，修正版本清單用piplist，dependencies.json保存原stderr與installed versions；不是環境可完整重建的lock。未安裝或升級套件。

