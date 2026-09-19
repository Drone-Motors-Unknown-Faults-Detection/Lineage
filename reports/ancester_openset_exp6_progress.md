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

## P2 — `Ancestor` 正式來源核對

使用者已提供並確認正式來源 URL：

`https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor`

雖然任務文字曾使用拼字 `ancester`，本次以使用者提供的完整 URL 為準，不再猜測其他 repository。

| 項目 | 已核對結果 |
|---|---|
| repository | `Drone-Motors-Unknown-Faults-Detection/Ancestor` |
| visibility | private；目前 GitHub 帳號可讀取 |
| default branch | `main` |
| source commit | `1ef4a891ae02dc95910f747a5163bb2edd608f28` |
| latest commit | `文件整理` |
| repository description | `未知故障預測核心程式碼` |
| license | GitHub metadata 未提供 license |
| Git LFS | `.gitattributes` 不存在；`git lfs ls-files` 無輸出 |
| releases / tags | 無 release、無 tag |
| tree 中實際資料檔 | 0 個 CSV、ZIP、NPY/NPZ、HDF5、Parquet 或 checkpoint |
| history 中實際資料檔 | 未找到上述資料檔路徑 |
| manifest / checksum | repository 未提供 |

### 文件所描述的正式資料格式

Ancestor 的 README 與 Step 1/2/4 文件一致描述正式資料應位於：

```text
data/Step-{1|2|3}/myfeature/{Motor}/{RPM}/{Screws}/
└── {Motor}_Group_feature_data_clean.csv
```

文件可核對出的 9 個正式工況為：

```text
T1/6000rpm, T1/8000rpm, T1/11000rpm
T2/6000rpm, T2/8000rpm, T2/11000rpm
T3/6000rpm, T3/8000rpm, T3/11000rpm
```

class mapping 為 10 類：

```text
0: 8screws      Healthy（known）
1: 1screw       Faulty 1（known）
2: 2screws      Faulty 2（known）
3: 3screws      Faulty 3（known）
4: 4screws      Faulty 4（known）
5: 5screws      New Faulty 1（unknown）
6: 6screws      New Faulty 2（unknown）
7: 7screws      New Faulty 3（unknown）
8: 3_14screws   New Faulty 4（unknown）
9: 4_146screws  New Faulty 5（unknown）
```

文件也指定：105 維特徵、`*_Group_feature_data_clean.csv` 為 IQR scale=1.5 逐列過濾版本，Step 4/5 使用 clean CSV；但這些都是 provenance/documentation，並不是目前已取得的資料物件。

### P2 驗收結論

- source repository、owner、URL、branch、source commit 已唯一確認。
- 文件格式、9 工況、class mapping、known/unknown 語意已確認。
- 實際正式資料本體沒有在 Ancestor Git tree、歷史、release 或 LFS 中；目前 workspace 與常用使用者資料目錄也沒有對應的 clean CSV 或 `data.zip`。
- 因缺少正式資料檔、manifest/checksum 與每工況樣本數，dataset fingerprint、split 樣本數、資料完整性與 P3 loader 初始化尚不能驗證。

P2 的 repository provenance 已完成，但「正式資料取得」是 P3 的必要前置，不能用 synthetic/demo data 代替，也不能宣稱 54 個正式 runs 已完成。

## 後續解除 P3 阻塞所需資訊

請提供以下任一項：

1. Ancestor 正式資料的實際資料根目錄（包含 `data/Step-*/myfeature/.../*_Group_feature_data_clean.csv`）；或
2. `data.zip`、`階段1.zip`、`階段2.zip`、`階段3.zip` 的受控下載位置；或
3. 可讀取該資料的 Git LFS／雲端／共享資料權限與下載方式。

取得資料後，才會進入 P3，建立 fingerprint、逐工況列樣本數、驗證 loader、split 互斥性，再逐階段修正程式並執行正式實驗。

## 2026-09-19：本機正式資料搜尋重新開工

使用者指定的唯讀資料根目錄 `D:\schoolshit\fcu\專題\馬達研究` 已確認存在並可讀取。本次沒有修改該目錄；完整 P1 inventory 已放在 [reports/raw_data_audit/](raw_data_audit/)。

| 階段 | 狀態 | 證據 | Commit | 下一步 |
|---|---|---|---|---|
| Raw data inventory | completed | 154 files、2 directories、4.598 GiB、3 outer ZIP、796 archive entries | pending P1 commit | 解析 raw／feature metadata |
| Data validation | pending | 已確認九個 condition archive；尚未完成 row／label／shape validation | — | 完成 P2 |
| Lineage data integration | blocked pending validation | T1/T3 有 105-feature clean CSV；T2 目前只有 raw CSV | — | 決定 T2 conversion |
| Credibility issue 1 | not started | 需先閱讀 Albert／exp6 證據 | — | 找出可重現問題 |
| Credibility issue 2 | not started | 需先閱讀 Albert／exp6 證據 | — | 找出可重現問題 |
| Credibility issue 3 | not started | 需先閱讀 Albert／exp6 證據 | — | 找出可重現問題 |
| exp6 factory integration | pending | feature branch 沒有 exp6；`origin/main` 有 `experiments/exp6_osr_benchmark.py` | — | 以 main 的 exp6 做整合前基線 |
| Mahalanobis default | verified | `core.openset.create_openset_detector()` 預設 `mahalanobis`；11 tests passed | — | 保持回歸測試 |
| PolarMap base | pending | 只存在 `origin/main` 的 `core/geometry.py`／exp4 | — | 讀取 main 版本並驗證 |
| k-NN method | verified | factory、CLI、comparison tests；11 tests passed | existing feature commits | 不改變既有介面 |
| Experiment runner | pending | feature branch 沒有正式 exp6 matrix runner | — | 先完成資料與 factory |
| Seed 1 runs | blocked | 正式資料尚未完成 contract validation | — | — |
| Seed 2 runs | blocked | 正式資料尚未完成 contract validation | — | — |
| Seed 3 runs | blocked | 正式資料尚未完成 contract validation | — | — |
| Aggregate report | blocked | 不得以歷史 output 或 synthetic data 冒充正式 runs | — | — |

P1 原則：raw ZIP 保持在來源目錄；所有 inventory、驗證摘要與後續轉換輸出只放在 Lineage 的受版控報告或 ignored data/cache 路徑。未完成 P2/P3 前，不宣稱正式資料已可直接跑 exp6，也不執行 54-run 矩陣。
