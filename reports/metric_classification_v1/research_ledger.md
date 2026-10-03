# 接續盤點與來源帳冊

2026-10-03，Asia/Taipei。研究分支起點 `6d8a88b6411b6e0448aee377b63948ef3febf549`。工作樹為 `C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree`，origin 為組織 Lineage，保留282個無關 tracked deletions。

已完整閱讀本機 AGENT.md 與 GitHub main 新規定（blob `8f35a6bf14fa4747d63add1d6bc852b65bcb4784`），並讀指定寫作文章。新手冊採未使用的 exp13，補齊三個索引。main 的目錄搬移不代表本分支也已搬移；不覆寫舊健康模組或封存文件。一般產物走 logs/output；依本次使用者要求，這個獨立 reports 目錄只存研究決策與交付索引，不存大型預測。全部新敘述使用繁體中文，英文識別碼與書目輔助。

## 基線與全域嘗試索引

歷史試驗採既有索引連結，保存所有狀態，不重跑未變動的數百格。

| 批次 | 已有證據與狀態 | 入口 |
|---|---|---|
| 原始類別矩陣 | 2,490執行；此回合不重訓，切分來源仍有缺口 | `reports/fault_type_openset/final_findings.md` |
| accuracy | 198評估；不是198份獨立資料 | `reports/fault_type_accuracy_study/result_index.json` |
| literature | 630格中624完成、6缺 predicted-class 校準群；24分類 pipeline 與22分數候選 | `reports/literature_expansion/result_index.json` |
| mechanism v2 | 81格；全部安全契約未通過；包含分類／偵測解耦、RPM pooling、block geometry | `reports/mechanism_research_v2/result_index.json` |
| Q | 72格中60完成、12未收斂；Q07 fault accuracy 33.92%，完整健康誤報29.14%，未通過 | `reports/continuous_research/result_index.json` |
| solver | 27 train-only 診斷；hard150/smooth150/hard600 收斂3/5/9；沒有新 accuracy | `reports/continuous_research/solver_result_index.json` |
| exp13 | 本次新12方法、108格；鎖定前未執行 formal outer | `docs/experiments/exp13_metric_classification.md` |

方法／模型分開：C02/M 是 base75＋balanced線性分類器＋factory LW；C17/M 是 harmonic69＋uniform shrinkage LDA＋該空間 factory LW；C24 是 per-RPM 完整 pipeline；D01 為 C17分類器＋C02/M detector。exp13 E01/E03 重建 Q01/Q03 的固定 identity 參考，E02/E04 換已收斂權重，未改 motor/calibration。

資料28910筆、90 CSV、105維，fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。三顆不同馬達的文件依據保留；raw session、window、IQR mask、單位、安裝、負載仍 UNKNOWN。全部樣本已 test 曝露。原105/LW/PolarMap、factory k-NN預設保留。

## 搜尋矩陣與閱讀深度

搜尋日期2026-10-03，工具為網頁學術查詢；搜尋引擎未提供可靠總命中數，結果數記 UNKNOWN，不能把顯示條數當全資料庫數量。只由一手來源支援方法；無關搜尋結果不列成採用文獻。本輪還未涵蓋所有主題／語言組合。

| 語言／題目 | 實際 query／來源 | 目前結果 |
|---|---|---|
| 英文／metric | `site.jmlr.org weinberger 2009 energy based classification equation 15` | LMNN 原式§3.5；PDF221頁已渲染核對 |
| 英文／prototype／反證 | `site.proceedings.neurips.cc prototypical networks few shot learning 2017 squared Euclidean Bregman`；`site.proceedings.neurips.cc On Episodes Prototypical Networks few-shot learning 2021 negative` | 平均中心 Eq.1–2、episodes 的負面證據；只採分類構件 |
| 法文／metric | `méthode distance apprentissage métrique LMNN classification énergie` | CORIA2015 原作者文；暫讀摘要／搜尋段落，未採其網頁分類資料 |
| 德文／metric | `metrisches Lernen LMNN Klassifikation Energie Weinberger Saul` | 回到同一原文，去重；沒有新增已驗證方法 |
| 日文／motor | `site.jstage.jst.go.jp 故障診断 距離 学習 モータ`；`site.jstage.jst.go.jp モータ 故障診断 振動 特徴量 少数` | 1998 wavelet 與2017運轉條件診斷；只讀出版摘要，raw 路徑未合格 |
| 韓文／metric | `site.kci.go.kr 모터 고장 진단 메트릭 러닝` | 索引回傳無關結果；沒有假造候選，待改詞 |
| 葡文／covariance | `site.scielo.br classificação falhas motor distância Mahalanobis` | 回傳化學計量／其他領域，未取得新 motor 方法 |
| 西文／motor | `site.doi.org diagnóstico fallas motor aprendizaje métricas prototipos` | DYNA2007 DSP負序電流；出版摘要，缺本站三相同步電流，未測 |
| 俄文／metric | `site.elibrary.ru диагностика неисправностей двигателя метрическое обучение` | 未取得可用原文；UNKNOWN，不宣稱窮盡 |
| 繁體中文／motor | `site.airitilibrary.com 馬達 故障診斷 原型 度量學習` | 成大原型網路馬達論文：機構目錄可讀，未逐頁讀全文，不引用其分數為本站成績 |

簡體中文查詢與其餘未涵蓋題目暫列待查；本次使用者要求不產出簡體文字。跨語言搜尋不是已完成全球文獻普查。

## 原始來源卡、假說與改編

1. Weinberger／Saul（2009），JMLR10:207–244，*Distance Metric Learning for Large Margin Nearest Neighbor Classification*，[原文](https://jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。原 PSD metric、hinge、target 鄰居與 Eq.15 energy。核對§3.5全文與公式圖片；未完整再讀38頁。原法不需測試集真值，query 逐假定已知類別評分；本站只讀 train reference。改編為對角非負權重、ridge與正規化訓練損失，energy 保留原式求和與三項。H13a/b 與固定消融見 exp13手冊。若只改善 train 而跨motor class collapse持續，假說受反證。
2. Snell／Swersky／Zemel（2017），NIPS30，*Prototypical Networks for Few-shot Learning*，[原文](https://papers.nips.cc/paper/2017/file/cb8da6767461f2812ae4290eac7cbc42-Paper.pdf)。核對 Eq.1–2與模型段落；原始深embedding／episodes／few-shot novelclass測試。本站不複製深網，採固定 harmonic69 下 train類平均、接相同 detector，不能以原few-shot成績保證本站跨馬達。
3. Laenen／Bertinetto（2021），NeurIPS34，*On Episodes, Prototypical Networks, and Few-Shot Learning*，[原文](https://proceedings.neurips.cc/paper_files/paper/2021/file/cdfa4c42f465a5a66871587c69fcfa34-Paper.pdf)。已讀摘要、引言與結論，未完整讀消融表；指出 episodes 的距離利用不足與設定敏感。提供負面範圍依據，不能推出本站 NCA 一定有效。本站先前九次 NCA已收斂，不能把其弱成績歸因未收斂。
4. 土屋雅弘／高木亨之（1998），日本機械學會論文集C64:465–472，wavelet旋轉機械診斷，[出版頁](https://doi.org/10.1299/kikaic.64.465)。摘要閱讀；需要真正 vibration waveform與時間頻率，不以105個欄位偽造訊號；保留 raw 阻擋理由，非「演算法無效」。
5. Villada Duque／Velásquez／Cadavid（2007），DYNA74(153):215–222，induction motor DSP診斷，[出版頁](https://revistas.unal.edu.co/index.php/dyna/article/view/979)。摘要閱讀；負序電流／逆序阻抗與定子故障，非本站螺絲配置。缺完整三相同步量，不實作冒稱同方法。

舊 P01–P31 來源見 literature帳冊，保留未測 OpenMax、DeepSVDD、CORAL 的資料／工具理由。未下載作者陌生程式、未安裝依賴、未上傳資料。使用已安裝 NumPy／SciPy／sklearn，科學 runtime3.10.19；相容性 runtime3.14.6，不交叉載入 joblib。

## 驚訝結果與接續狀態

初始 Q 的不足包含有限求解預算；hard600九份已收斂，不能據此推論分類改善。exp13先檢驗這個可反駁差異，再依保存的預測診斷 class collapse、calibration transfer。暫無 exp13實測，不填預期分數。不因本批榜單完成停止全部研究；後續須新假說、新有限協定與來源，不進行 test 最佳係數搜尋。

目前 stage=implementation，batch=exp13_metric_classification_v1，上一個正式成功cell=hard600_fixed-fold2_seed2；pending=unit／synthetic／protocol lock／commit／fit／commit／evaluate／reinfer／report。raw/fresh阻擋不影響本批現有資料實測。local起點與上輪remote SHA皆6d8a88b；本輪提交後另記實際SHA。
