# #26 第一階段：環境工程交付

Related #26；本 PR 不關閉 #26，不擴大到 Albert PR #36 的待決檔案。

## 實際修改

- 正式 Python 範圍由單一 patch 改為 3.10.x；八個直接依賴加入上下限。
- 單一 `runtime-constraints.txt` 固定直接／傳遞／建置版本；不另維護 uv.lock。
- Windows PowerShell 7 與 POSIX 安裝入口建立新目錄、拒絕覆寫，既有環境保留。
- `setup_run()` 保存 `environment.json`；Python、OS、套件版本、commit／dirty 與 constraints SHA 可回讀，沒有 token、環境變數或使用者絕對路徑。
- 本階段未修改資料、模型、參數、Mahalanobis／LW 預設、k-NN factory、PolarMap 或待決 Web 檔案。

事前契約 commit `49fec06168bfb4eb2d921a0f37b50b812fc0d75d`；程式 commit `815a548e29ee427387b33c14229feb1fe32efdb0`，皆已 push 並核對遠端 SHA。

## 實際驗證

新環境 Python 3.10.19 已有 [179 項完整測試](../../output/branch_integration/2026-10-09-12-12-10/validation.json)，0 failed/error/skipped；pip check 與四個 CLI help 成功。[17 個新增 fixture／鎖版核對](../../output/runtime_policy_evidence/2026-10-09-12-12-05/evidence.json) 無版本差異。測試使用 synthetic／暫存 fixture，資料清冊為 0，不讀 ignored data。guard 的 [11 項與 8 組](../../output/monitor_guard_evidence/2026-10-09-12-12-44/evidence.json) score／PCA 差值 0。

第一次 cp950 安裝失敗、pip 私有測試 API 失敗、cloudpickle 傳遞依賴更正都保存於 [契約與實測區](../runtime_policy.md)，不刪除失敗或既有 venv。上述測試 HEAD 為 `815a548`，另有 `.gitignore` 與對應 fixture 的小幅 working-tree 更正，沒有科學程式差異。最終全新鎖版安裝仍須完成並追加證據。

## 未完成與關單條件

三支 health CLI 尚未統一 setup_run；直接 `run()` API 也沒有每次初始化保證。#24／PR #36 定案後才能補齊每個入口的環境紀錄。正式安裝只驗 Windows／3.10.19；Linux／macOS 尚待 CI，3.14 不在本輪正式宣告。legacy extras 未完整鎖版。#26 仍 OPEN。

本 PR 提供可獨立使用的工程基礎；沒有新準確率結果、fresh final 或可靠性改善主張。接續 #27 必須用這份 constraints 實際執行 CI 紅燈／綠燈測試，不能由本機測試推論 GitHub Actions 已存在。

Co-authored-by: Codex <codex@openai.com>

### 最終 constraints 的全新安裝

以新目錄 `D:/schoolshit/專題/src/tmp/lineage_clean310_20261009_locked` 執行 [最終安裝](../../output/runtime_policy_evidence/2026-10-09-12-08-35/evidence.json)，命令全部 exit 0，完整固定版本核對 0 差異，pip check 成功；沒有沿用第一次失敗環境或第二次探索安裝。安裝後 [環境 sidecar](../../output/environment_install/2026-10-09-12-14-19/environment.json) 的實際 HEAD 與來源狀態另存，不把外層安裝 runner 的版本當成新 venv 版本。

該最終環境實際執行 [179 項完整 fixture](../../output/branch_integration/2026-10-09-12-15-20/validation.json)，0 failed/error/skipped，pip check、四個 CLI help 與 [全部固定版本核對](../../output/runtime_policy_evidence/2026-10-09-12-15-16/evidence.json) 成功。擴大至七份文件時，[第一次文件檢查](../../output/project_closeout_evidence/2026-10-09-12-15-57/evidence.json) 發現 sidecar 連結秒數筆誤，已改為實際存在的 `12-14-19`，[重驗104目標／0失效](../../output/project_closeout_evidence/2026-10-09-12-16-11/evidence.json)。失敗產物保留，沒有降低檢查標準。
