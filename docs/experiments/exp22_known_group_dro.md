# 實驗22：已知 RPM×類別群組的穩健損失與正則化控制

2026-10-05 收尾註記：M 完整結果未支持可靠候選，依最新使用者要求封存本支線。以下保留當時的先行假說與預定操作；本批已規劃未實作，未進入訓練或測試，不列為演算法 FAILED。

2026-10-04，Asia/Taipei。先行手冊。exp21 尚在來源重建、outer 成績未讀；本批尚無程式、正式擬合或評估。假說來自 exp20 的低 train CE、跨 motor 失敗及原始文獻，不依 exp21 的結果挑係數。全部資料有歷史曝露，這仍是探索性研究。

## 來源與可反駁假說

Sagawa、Koh、Hashimoto、Liang（2020），*Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization*，ICLR，[原文](https://arxiv.org/pdf/1911.08731)。完整閱讀 arXiv v2 19 頁本文、證明、反例及補充。作者 [group_DRO 固定 cbbc1c5](https://github.com/kohpangwei/group_DRO/tree/cbbc1c5b06844e46b87e264326b56056d2a437d1) README、MIT LICENSE、loss.py、train.py、run_expt.py、models.py 已讀；不複製或執行，無新依賴。完整閱讀範圍、反證與搜尋見 [來源卡](../../reports/continuous_research/group_dro_source_card_20261004.md)。

H22a：exp20 平均 RPM risk 及其 variance 都很低，但部分測試類別仍零召回；直接重加權已知 train 的最差 RPM×class 群組，可能與等群組 ERM 產生不同分類邊界。H22b：重加權若仍記住單一 train motor，較強 ridge 可能減少這種記憶；因此必須與相同 ridge 的 ERM 比較，不將容量縮減算成 DRO 單獨收益。反證：群組 train risk／最差 train class 改善，但跨 motor／RPM 仍 FAILED；或高 ridge 同時破壞已知 fault 與健康辨識。

RPM×class 是訓練 loss 分組，不能當獨立 motor/session；本案 train 只有一顆 motor。Group DRO 的來源群組混合假設無法保證涵蓋 held-out motor 的條件分布。本文凸、有界／緊緻參數空間及平均 iterate 保證不能原樣套用未投影 softmax；本批不宣稱最適收斂或泛化保證。

## 事前固定公式與改編

formal105 唯讀；base75／harmonic69 及 train-only RobustScaler 沿用既有設定。六已知類包含 healthy；三 RPM×六類形成 18 個已知訓練群組。任一群組無樣本列 INCOMPLETE，不借 cal/test 補值。模型是六類線性 softmax，bias 不受 ridge。令 G=18、Z 為已知 train 表示法、A=[W;b]，每群 R_g(A) 是該群逐筆 CE 的普通平均。

每表示法固定兩種 objective × ridge λ∈{0.001,0.1}：

- uniform：q_g 固定 1/G，最小化等群組平均 CE＋λ/2||W||²。
- dro：q 初值 1/G；每一步用當前完整 train 群組風險，log q_g←log q_g＋0.01 R_g，再以 logsumexp 正規化。用更新後 q 加權群組 CE 梯度，加 λW 更新 A；q 更新 stop-gradient。

所有方法零初始化、500 個完整 full-batch 更新，不使用 warm、momentum、scheduler、best epoch 或 early stopping 選擇。保存更新後 A_1…A_500 的算術平均作 inference 係數；最後 iterate 另存診斷，不由 test 選平均或最後。種子固定 0／1／2，本流程無隨機抽樣，若相同就如實報告。

每個表示法／λ，兩 objective 用相同 η：

`η = 1 / [0.5 × max_g mean_(i∈g)(||Z_i||²+1) + λ]`。

這是固定群組混合 softmax Hessian 的保守 trace 上界，只從 known train 算；q 更新形成的整個 minimax 過程沒有因此取得收斂保證。加強 ridge 的兩個實值是有限數量級對照，不是 motor 資料最佳值；0.01 取作者 `robust_step_size` 預設，500 步是本案 CPU 預算約定。高低 ridge 都保留，不能用 outer 選有利係數。

原方法的單群組隨機更新／CNN／預訓練／validation 選參／作者 momentum 未移植；本批是固定手工特徵的 full-batch 有限改編。沒有 group adjustment、normalized loss、BTL／CVaR 或自動調整。使用 log q 避免直接 exponential overflow；需保存 q 歷程、群組 CE／accuracy／support、平均與最後係數 SHA、解析梯度、步長及完整 fit IDs。固定步數完成標 FIXED_HORIZON_COMPLETE，不偽稱 OPTIMIZER_CONVERGED。

推論只收完整 features，不收 RPM、motor、路徑、query label 或未知真值。未知只在封存後 outer 評估。另一顆 motor 的 known cal 僅設既有拒絕門檻，不進 q、representation、scaler、classifier 或參數選擇。

## 矩陣與判定

2表示法×2objective×2ridge×3detector×3fold×3seed＝216 detector 評估、72 新分類器擬合、9 共用 bundle。模型排序：base75／harmonic69，各按 ridge0.001 uniform／dro、ridge0.1 uniform／dro；每模型依 C02/Maha-LW、C02/k-NN、MSP 配成 N01–N24。前兩 detector 沿原 C02 base75 factory reference，隔離 classifier 改編；MSP 用既有 1−max softmax，known cal pooled linear q95、strict raw>q，零門檻不除零、不翻分數方向。

fold0=train/cal/test T1/T2/T3；fold1=T2/T3/T1；fold2=T3/T1/T2。沿固定 N=5 manifests、seeds0／1／2、RPM6000／8000／11000；known 8screws／1screws／2screws／3_14screws／3screws／4screws，unknown 4_146screws／5screws／6screws／7screws。validation、selection IDs 空，歷史曝光不清除。

固定 controls C02／C17／C24／D01，共96方法配對；每 DRO 對同表示法／ridge／detector 的 uniform 共12配對；高 ridge 對同表示法／objective／detector 的低 ridge 共12配對。120方法配對×三fold三seed＝1,080逐樣本配對。無 global winner；同資料與真值／來源 SHA 才可比較，不把三 detector 當三個不同 classifier fit。

完整健康總誤報、fault-only及全部 final decisions 的 F1、逐類 support、known rejection、unknown AUROC/AP／召回／precision、coverage與各 motor／RPM 結果全部保存。原 CONTRACT 不降低：全部 seeds 都須符合實質增益、最差類別、健康、unknown及 coverage 保護。只有一組 N=5 初篩，通過後仍要多 subset／壓力驗證才能談 R2；採集來源 UNKNOWN、每類兩個獨立 test groups及fresh guard INCOMPLETE。

## 程式範圍、測試與可直接續接的步驟

| 範圍 | 路徑 |
|---|---|
| 新公式／模型 | core/fault_type_group_dro.py |
| 新實驗雙入口 | experiments/fault_type_group_dro.py，run(...)／main() |
| 新測試 | tests/test_fault_type_group_dro.py、tests/test_fault_type_group_dro_runner.py |
| 唯讀共用 | LiteratureRepresentation／NoveltyReference、core.openset、原 C02 native models、exp21 封存／來源稽核及報告機制 |
| 狀態／結果 | reports/known_group_dro_v1/ |
| logs/output | core.logger.setup_run：logs/fault_type_group_dro_*/、output/fault_type_group_dro_*/ |
| 大型產物 | D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-04/known_group_dro_v1/workspace/output |

1. 本手冊、兩索引及狀態先 commit/push，之後才寫新公式。不要修改 sealed exp20／21 來源或舊模型。
2. 手算 equal-group weighting、log q 更新、加權 CE／bias gradient、trace η、平均 iterate；測 λ／objective／class／RPM 範圍、缺群組、有限值、未知用途、固定 seed、序列化與重封篡改。
3. core 小測試兩 native 通過後 commit/push；runner 共用原角色／SHA／alias guards，新增 actual known full refit、factory/MSP 重建、truth mutation、paired report及resume測試。
4. 兩 native 完整 tests、pip check、CLI help與synthetic smoke；synthetic 只能當工程驗證。通過後 commit/push，精確216條件 protocol 含 source SHA／runtime／參數／CONTRACT，提交後 fit。
5. native Python3.10／sklearn1.7.2 正式 fit；source-verify 只讀 known train/cal，重建完整 q／平均係數／門檻及 reference；lock與proof先 commit/push，才 evaluate／verify／report。不得跨 sklearn runtime 載入正式 joblib。
6. 全矩陣失敗也保留；D槽備份驗 whole/member SHA與CRC，不刪來源、不覆蓋 ZIP。每 action1800秒、C槽保留1GB，checkpoint用同config接續。

正式預設 formal105／linear／Maha-LW、k-NN切換與PolarMap均不改。282筆既有無關刪除不stage；不能因這份手冊出現，就聲稱程式或216評估已完成。
