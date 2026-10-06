# 導覽資料契約

新增experiments/navigation_data_contract.py，僅唯讀載入／checksum／來源索引，不新增模型。run(dataset, seed=42)與main CLI；setup_run("navigation_data_contract")保存摘要。load_pools沿用105維與有限值過濾，所有可用池至少10筆（本展示入口約定，保留至少6 train／2 cal／2 holdout；不是模型可靠性標準）。不足時阻止建基準，不改核心split。

split證據從既有monitor.splits取得索引；來源ID用各配置CSV SHA清單＋concat後finite-row索引，明確不是raw-window ID。前端確認前只傳匿名來源代碼與SHA，不傳unknown配置路徑；本機log保留重現對照。

預期：missing healthy、空池、不足筆數被拒絕；預設與kNN核心分數保持一致。反證：任何fit／cal多出unknown、模式切換重fit或候選提前揭示truth都視為導覽失敗。採集獨立性不因契約通過而PASS。

來源：core/data.py既有make_split/load_pools；core/monitor.py與core/openset.py。沿用方法文獻見exp1/exp2手冊，本模組checksum／匿名呈現是專案操作約定。

影響：新增experiments/navigation_data_contract.py、web/guide.py、web/static/guide.*與tests/test_navigation_guide.py；讀取web/live.py、web/server.py，不修改Albert PR #36檔案。

CLI：python -m experiments.navigation_data_contract --data-root data/formal_local --motor T1 --rpm 8000rpm。
