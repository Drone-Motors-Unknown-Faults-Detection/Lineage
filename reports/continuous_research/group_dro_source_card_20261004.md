# Group DRO 原始來源核對

2026-10-04，Asia/Taipei。此卡是下一條研究支線的閱讀證據；尚未實作、封存協定或產生正式成績，不修改 exp21。

## 來源與閱讀範圍

Shiori Sagawa、Pang Wei Koh、Tatsunori B. Hashimoto、Percy Liang（2020），*Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization*，ICLR。英語原文，[arXiv v2](https://arxiv.org/pdf/1911.08731) 與 [ICLR 正式稿](https://openreview.net/pdf?id=ryxGuJrFvS) 同篇去重。arXiv 19 頁、1,281 文字行全部讀取，包含證明、反例、補充實驗與資料／選模細節；正式稿目前僅搜尋核對，不重複計為另一篇完整閱讀。PDF 技能用於唯讀核對，未做完整圖像／版面 QA。

原式是已知群組風險的最大值。Algorithm 1 交替更新群組機率及模型；凸性、有界損失、參數範圍等條件下的平均 iterate 保證，不能直接當本站未限制 softmax 或固定最後 iterate 的保證。原文同時指出低訓練損失可能掩蓋最差群組泛化失敗，增加正則化並非所有資料都有效。作者用 validation 選部分係數及 epoch；本站 calibration 不可代替選模 validation。

## 作者程式

論文 Reproducibility 連到 [group_DRO](https://github.com/kohpangwei/group_DRO/tree/cbbc1c5b06844e46b87e264326b56056d2a437d1)。固定 commit `cbbc1c5b06844e46b87e264326b56056d2a437d1`；完整讀 README.md、MIT LICENSE、loss.py、train.py、run_expt.py、models.py。沒有讀完整 repo，沒有執行、安裝 PyTorch／CUDA、下載權重或資料。

`loss.py` 用逐群平均 CE 更新 `adv_probs *= exp(step_size * adjusted_loss)`，再正規化、以更新後機率加權原群組損失；step_size 預設 0.01。group adjustment 在所有 adj>0 時才加入 `adj/sqrt(group_counts)`，normalize_loss、btl 是額外分支，不能默默混入主方法。`compute_group_avg` 對空 minibatch group 以分母修正給零值；本案完整 training group 缺資料應列 INCOMPLETE，不能沿用零值假造覆蓋。

`train.py` 的影像訓練用 SGD momentum 0.9；best checkpoint 與可選 scheduler／automatic adjustment 依賴 validation。程式每 epoch 也評估 test。本站若有限改編，應只用已知 train 更新，封存後才評估 outer test，不複製此訓練期間 test 存取。`run_expt.py` 含可用線性模型入口，但仍有固定 CUDA 呼叫與舊依賴；不以直接執行此 repo 作為本案實作入口。

## 本案機制假說與反證

既有 REx 讓三 RPM 的平均已知訓練風險接近，沒有恢復最差類別召回。另一個可測假說是：以 RPM×已知類別的訓練群組，直接降低最差群組風險，並與同正則化、同資料的等群組 ERM 配對，可能改變被平均損失忽略的類別。這是待測假說，不是已有提升。

群組僅供已知 train 的 loss 使用；predict 不收 RPM、motor、路徑或真值。RPM×類別不是新馬達／session；只有一顆 training motor，群組重加權不能保證涵蓋新 motor 的條件分布。需保存每群筆數、權重歷程、梯度／式子測試與 train-only 校驗。unknown 不得出現在群組或參數選擇。只有原來源核對完成，尚無下一批係數、訓練預算或正式 method ID；先行手冊及協定提交後才能實測。

## 搜尋與未讀 queue

本回合查詢：英文 `site.openreview.net Distributionally Robust Neural Networks Group Shifts Sagawa 2020 regularization`；繁體中文 `Group DRO 分佈穩健 訓練 最差 群組 Sagawa ICLR 2020`、`Group DRO 最差群組 正則化 Sagawa ICLR 2020 原始`；日文 `グループ分布頑健最適化 Sagawa 正則化 ICLR 2020`；德文 `Group DRO schlimmste Gruppen Regularisierung Sagawa Original`；英文反證／機械支線 `Group DRO classification vibration fault diagnosis cross machine negative results`。索引未提供全域結果總數，result_count=UNKNOWN；二手摘要僅作線索。

待精讀：[Just Train Twice（Liu 等，ICML 2021）](https://proceedings.mlr.press/v139/liu21f.html)、[Improved Group Robustness via Classifier Retraining on Independent Splits](https://arxiv.org/abs/2204.09583)、[Selective Classification Can Magnify Disparities Across Groups 的作者程式](https://github.com/ejones313/worst-group-sc)、[Sagawa 等的過度參數化研究](https://proceedings.mlr.press/v119/sagawa20a.html)。目前只有首頁／metadata／搜尋線索，不把其全文結論或演算法報成已核實、已實作。沒有宣稱所有語言／文獻已窮盡。

新增反證 queue：[Zhai、Dan、Kolter、Ravikumar，Understanding Why Generalized Reweighting Does Not Improve Over ERM](https://arxiv.org/abs/2201.12293)，metadata 明示 ICLR2023、v4、40頁；本回合只讀 abstract／metadata，未讀完整證明。初查詢誤帶NeurIPS2021，依一手 metadata 更正，不引用匿名舊稿或作者 poster 的會議年份當正式出處。[Wang、Chatterji、Haque、Hashimoto，Is Importance Weighting Incompatible with Interpolating Classifiers?](https://neurips.cc/virtual/2021/35514) 是NeurIPS2021 DistShift workshop頁；僅abstract、未讀本文，不宣稱多項式尾損失已核對或已實測。兩者提供待核對的競爭機制，不用摘要替代公式來源。
