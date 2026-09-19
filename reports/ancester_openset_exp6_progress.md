# `ancester` Open Set / exp6 任務進度

## P1 — Git 與 repository 基線

本報告由 P1 建立，記錄本任務開始時可重現的 Git 狀態與推送安全檢查。原始工作樹中的未提交檔案未被修改、覆蓋或加入本 commit。

| 項目 | 結果 |
|---|---|
| Lineage repository | `https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage.git` |
| local repository path | `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\Lineage` |
| 原始工作樹 branch | `feat/knn-openset-comparison` |
| 原始工作樹 HEAD | `a28763c0c968d317b15305a54f8a3ed4829d6fbe` |
| 原始工作樹 upstream | 未設定 |
| 原始工作樹 push remote | `origin`（Lineage organization repository） |
| 同名遠端 branch | `origin/feat/knn-openset-comparison`，HEAD `dd0190f7f4de7f3f624292cd32a98d12e413b4e1` |
| working tree | 不乾淨，但只有一個原有未追蹤檔案 |
| 原有未提交檔案 | `core/openset.py`（未加入本階段） |
| P1 隔離工作樹 | 由同名遠端 branch 建立；本報告在此工作樹提交 |
| 本任務候選 push 目標 | `origin feat/knn-openset-comparison`；先以遠端最新 HEAD 為基線，不覆蓋舊遠端內容 |

### P1 唯讀檢查

原始工作樹執行過：

```text
git status --short
git branch --show-current
git branch -vv
git remote -v
git rev-parse HEAD
git log --oneline --decorate -n 30
git diff
git diff --cached
git submodule status
git rev-parse --abbrev-ref --symbolic-full-name @{u}
```

結果重點：

- 原始 branch 沒有 upstream；不可把本地舊 HEAD 當成遠端最新狀態。
- `origin/feat/knn-openset-comparison` 比原始本地 HEAD 多 8 個 commit；原始本地 HEAD 是遠端 branch 的祖先。
- 原始工作樹的 `core/openset.py` 是使用者既有未提交檔案；同名遠端 branch 也已經有 tracked `core/openset.py`，因此沒有用 checkout、reset、clean 或 merge 去覆蓋該檔案。
- `git submodule status` 沒有列出有效 submodule；Git wrapper 在目前 Windows PATH 缺少 `basename`/`sed`/`git-sh-setup`，但不影響本次沒有 submodule 的判斷。
- `git diff` 與 `git diff --cached` 沒有 tracked/staged diff；未追蹤檔案內容未被 stage。

### Push dry-run

原始本地 HEAD 執行：

```text
git push --dry-run origin HEAD:refs/heads/feat/knn-openset-comparison
```

結果為 `non-fast-forward`，原因是本地 `a28763c` 落後遠端 `dd0190f`。因此本階段沒有從原始工作樹推送舊 HEAD；改用不含使用者未提交檔案的隔離工作樹，並在遠端最新 branch 上建立本 P1 commit，避免覆蓋遠端歷史。

## P2 前置搜尋結果與阻塞

依照任務規格搜尋 exact repository name `ancester`，沒有把它更正成 `ancestor`：

- `Drone-Motors-Unknown-Faults-Detection` organization API 目前只列出 `Ancestor`、`Lineage`、`GPU-Learning-PyTorch`、`GPU-Learning-Tensorflow`，沒有 `ancester`。
- 已登入帳號 `05zhi` 的可存取 repositories 沒有 exact `ancester`。
- Albert 帳號 `JW-Albert` 的公開 repositories 沒有 exact `ancester`。
- GitHub repository search 的 exact-name 候選是無關的公開專案，沒有與 Drone Motors organization 或 Lineage 資料格式相符者。
- Lineage 的 `AGENT.md`、`README.md` 與 Git 歷史只明確引用 `Ancestor`，不能據此把 `Ancestor` 假定為使用者指定的 `ancester`。

因此 P2 尚未通過。正式資料、9 個工況、dataset fingerprint、LFS objects 與資料 provenance 目前都不能安全確認；在取得 exact `ancester` URL/owner 與權限前，不執行正式資料恢復或 54-run 實驗，也不以 synthetic/demo data 代替。

## 後續解除阻塞所需資訊

請提供下列其中一項：

1. exact `ancester` repository URL（例如 `owner/ancester`），並確保目前 GitHub 帳號可讀取；或
2. 若 repository 是 private，授予目前 GitHub 帳號讀取權限；若正式資料在 repo 外，另提供資料根目錄或受控下載方式。

收到後才會進入 P2，逐檔核對 manifest、checksum、9 個正式工況、class mapping、split 與 Lineage loader。
