# 回覆張老師：故障配置分類、未知故障與資料切分

Lineage 專題研究｜工作版本 2026-10-05，交付核對 2026-10-06（Asia/Taipei）｜研究分支 research-improvements-20260920

老師您好，我們依您的兩項建議，已實際完成「healthy＋5 個已知 faulty 配置，保留 4 個 faulty 配置作 unknown」及其他 N 的研究。程式現在不是只輸出正常／故障二元結果，而是先分類已知配置，再判斷是否拒絕為未知。現有跨馬達結果仍偏弱，沒有把程序完成寫成可靠模型完成。

這份回覆將兩個問題分開回答。問題一的類別配置與實測已完成，但可信辨識仍未達標。問題二的切分依據、樣本用途與來源限制已文件化；共同選模型及 validation/calibration 共用已在後續固定方法協定中排除，真正獨立採集與未曝光 final test 尚未證明。

閱讀導引：第 1–3 節回答故障配置與實測；第 4–6 節回答切分依據、已修問題與未確認來源；第 7 節整理研究限制；第 8 節提供完成度與證據入口。Word 使用可編輯文字與表格，不是整頁圖片。版面渲染驗收狀態另見交付索引。

## 1. 現有資料可以辨識什麼

正式資料共有 90 份 CSV、28,910 筆有限值 105 維特徵。T1 有 9,759 筆、T2 有 9,857 筆、T3 有 9,294 筆。文件明確支持三者是不同馬達個體，T1 為新機、T2／T3 為老機；沒有實體序號或使用時數，不代表完全沒有馬達身分依據。新舊狀態與個體差異混雜，不能將三者串成同一馬達的生命週期。

8screws 為 healthy；其餘九個標籤表示螺絲數量／位置配置。同一鬆動機制的不同配置可以做監督式分類，但不能直接改名為九種已獨立確認的物理故障原因，也不能由螺絲數量推定損壞百分比。

| 資料層次 | 可支持的說法 | 目前不能支持的說法 |
|---|---|---|
| 標籤 | 已知／未知螺絲配置辨識 | 九種獨立物理故障機制 |
| T-code | 文件支持的三顆馬達識別 | 同一顆馬達三次退化追蹤 |
| 特徵 | 既有清理後 105 維比較 | 完整未刪點、同步原始時序 |
| 計分 | 現有三馬達探索性跨馬達結果 | 部署可靠性、RUL、固定誤報保證 |

馬達身分依據為固定版本 [Experiments_Guide 第218行及230–231行](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/afcfcc419dab3103a86a8f95601d3af85890eb38/docs/Experiments_Guide.md#L218)。資料 fingerprint 為 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d，本次唯讀重算一致。

<!-- PAGE_BREAK -->

## 2. 問題一：healthy＋5 known／4 unknown 已怎麼做

我們沒有因為物理故障原因尚未確證，就拒絕做您提出的類別配置。歷史 Protocol A 的 N=5 已跑全部 C(9,5)=126 組。每組保留 healthy，再選五個 faulty 配置作已知，另四個作 unknown；三個 motor folds 與 Mahalanobis-LW／k-NN 共 756 次 detector 評估。兩個 detector 共用分類器，因此已知分類成績相同是合理行為，不代表偵測器重複實作。

其他 N=1–8 的配置 sweep 及 N=9 closed-set baseline 也有實測，共 1,014 次；其中不含已另外完整執行的 N=5。這些 N 使用登錄的配置數量，不宣稱每個 N 都跑全部組合。Protocol B 另完成 720 次：它將保留配置區分為 unknown-validation 與 unknown-test，作既有研究診斷；未知配置仍不得進入分類器、scaler、協方差或鄰居參考擬合，也不得參與本輪固定門檻的選擇。

| 歷史工作 | 實際完成 | 範圍 |
|---|---:|---|
| A，N=5 | 756 | 全126組×3 folds×2 detectors |
| A，其他 N 與 N=9 | 1,014 | 已保存 manifest 的 sweep／closed-set |
| B，N=5 | 720 | 已保存的 B 配置與角色輪換 |
| 合計 | 2,490 | 既有執行，這次沒有重跑 |

最近固定方法研究沿用一組確切 N=5 manifest：known 為 8screws、1screws、2screws、3_14screws、3screws、4screws；unknown 為 4_146screws、5screws、6screws、7screws。healthy 是六個 known labels 之一，不能將「五個 known faulty」誤寫為總共只有五類。

這一組用於有界方法比較與失敗分析，沒有重新執行所有126組。模型弱與研究資格不足是不同問題：能實作分類不代表已辨識可信，缺採集證據也不等於分類程式不存在。

<!-- PAGE_BREAK -->

## 3. 問題一的實測結果：目前仍未達可信辨識

歷史 A／N=5 的126組平均已知分類 accuracy 為 25.744%，balanced accuracy 為 25.805%，macro-F1 為 0.2022。unknown-positive AUROC 為 Mahalanobis 0.5277／k-NN 0.5245；unknown recall 為 14.995%／7.943%。這是歷史不同配置平均，不能直接和下表單一配置的固定方法平均當作純演算法差異。

下表來自後續保存摘要，使用固定 seed0、三 motor 等權描述平均。known accuracy 含 healthy；fault accuracy 與 conditional fault F1 僅 true known faulty。unknown recall 以真 unknown 為分母；healthy 完整誤報包含被分為 known faulty 或 unknown。完整開集 F1 另含 healthy／unknown 假陽性，不能以 conditional F1 代替。

| 方法 | known accuracy | fault accuracy | conditional fault F1 | unknown recall | healthy完整誤報 |
|---|---:|---:|---:|---:|---:|
| C02：振動75／線性＋LW | 34.15% | 26.61% | 0.2404 | 18.44% | 26.87% |
| C17：harmonic69／LDA＋LW | 39.29% | 30.43% | 0.2852 | 8.44% | 14.13% |
| C24：75／分RPM LDA＋LW | 32.17% | 30.91% | 0.2866 | 21.07% | 63.41% |
| D01：C17分類／C02拒絕 | 39.29% | 30.43% | 0.2852 | 18.44% | 14.13% |
| M13：有限特徵自挑戰 | 37.29% | 31.25% | 0.2666 | 18.44% | 30.46% |

D01 相對 C02 的 known accuracy 提高約5.13個百分點、fault accuracy 提高約3.82個百分點，但 unknown recall 不變，T1 仍為0%。M13 相對 C24 的 fault accuracy 只提高約0.34個百分點，且 F1 不及 C17、健康誤報增加；因此不能稱全面改善。

原 #22 hard600 outer 已在 E02／E04 實測，配對 fault accuracy 下降約3.507／3.655個百分點。最後 M 批216組、24方法全部未通過事先固定的可靠性契約；沒有只取最好 seed 或放寬門檻宣稱成功。

<!-- PAGE_BREAK -->

## 4. 問題二：切分不是隨意洗牌

切分有兩層依據：類別層決定 known／unknown；motor 層決定 train／calibration／test。後續 no-selection 協定固定以下方向，整顆馬達保持在單一用途，不將同一顆馬達的視窗隨機混進本折訓練與測試。

| Fold | Train | Calibration | Test | Test known／unknown |
|---|---|---|---|---:|
| 0 | T1 | T2 | T3 | 5,604／3,690 |
| 1 | T2 | T3 | T1 | 5,935／3,824 |
| 2 | T3 | T1 | T2 | 6,007／3,850 |

Train 只含該 motor 的 healthy＋known faulty，用於表示法、scaler、分類器及 detector reference 的擬合。Calibration 只含另一 motor 的同組 known labels，用於已固定 detector 的校準，不進 covariance／prototype／neighbor reference。第三 motor 保留全部 healthy、known faulty、unknown faulty 作 test。開發 motor 的 unknown rows 不為湊數放進 train 或 calibration。

Validation 與 selection sample IDs 明確為空，selection_policy=none。所有方法、參數、seed及方向在本批評估前鎖定，沒有跨折共同 winner；方法清單本來就受歷史結果啟發，仍屬探索性，不是新的盲測。

三折相同 sample 可以輪流作不同用途，固定方法的跨折輪換不是自動洩漏；若用另一折 test 所在樣本的 validation 成績選共同方法，再評估該 test，則有選擇依賴。三個 seeds 描述演算法敏感度，不是三顆新馬達、三次獨立採集或新的 test。

這個做法支持 documented leave-one-motor-out 的現有三馬達比較，但不保證所有原始錄製／視窗獨立。依賴資料應按照欲宣稱的泛化群組切分，而非以大量視窗取代獨立群組；參考 [Roberts等，2017，Ecography](https://doi.org/10.1111/ecog.02881)。

<!-- PAGE_BREAK -->

## 5. 「測試資料切分不完整」到底指什麼

我們將 INCOMPLETE 拆成可以驗證的不同原因，不再用一個字混稱全部問題。

| 問題層次 | 目前狀態 | 已處理／仍不足 |
|---|---|---|
| 單折樣本用途交集 | VERIFIED | train／cal／test IDs與motor角色隔離；unknown不fit／cal |
| 跨折共同選模型 | 後續已排除 | 原共同validation選擇仍是歷史依賴，不洗掉紀錄 |
| validation/cal共用 | 後續已排除 | 取消選參，保留專用motor校準；不是新增第四motor |
| 類別／RPM覆蓋 | 可按manifest查核 | 新比較只一組N=5，不能宣稱多組穩健性已通過 |
| 每類獨立test groups | INCOMPLETE | 每折只有一顆test motor，未滿既有至少兩群要求 |
| 原始採集／視窗來源 | UNKNOWN | 缺session、recording、raw intervals、清理mask |
| 未曝光final test | INCOMPLETE | 全28,910筆均已有歷史test曝露 |

歷史共同表示法選擇中，17,546筆 known validation 同時屬於其他折 test；歷史三折 validation/calibration 共用分別為6,007、5,604、5,935筆。當時單折 ID 交集為零，不能抵銷跨折共同選擇依賴。後續固定 no-selection 協定修正用途，但不能回頭把既有結果變成未曝露資料。

本輪另外核對完全相同檔案、完全相同特徵向量與12位有效數字指紋皆無重複的既有稽核證據。這只能排除已檢查的副本，不能證明原始視窗沒有重疊。同資料換seed、另存CSV或改路徑，都不使它成為fresh final。

參考 [Wheat等，2024，IEEE Access](https://doi.org/10.1109/ACCESS.2024.3497716) 的軸承訊號切分研究；它是避免洩漏的研究依據，不是直接套用該文成績到我們資料的證明。

<!-- PAGE_BREAK -->

## 6. 能恢復的來源，以及不能補造的資訊

既有來源追查已盤點兩個本機根目錄與 nested ZIP。三個階段壓縮檔的副本 SHA 相同；450個處理後通道成員／根目錄可以追溯。已恢復28,910筆 clean rows到processed ordinals：Stage1／3共19,053筆，Stage2共9,857筆。這是清理後位置對照，不是未切窗、未刪點 DAQ 的真實時間區間。

105維計算核對發現九份來源腳本的統計／FFT AST一致；30份Stage2數值重建與六個事前固定Stage1／3健康RPM抽查通過。但實際通道寬度不同，歷史公式與file-level清理仍有限制；計算式一致不等於感測器單位、方向、校正、安裝及負載跨階段一致。

| 事實 | 證據等級 | 不推論的部分 |
|---|---|---|
| T1／T2／T3不同個體 | 文件支持＋檔案T-code對照 | serial、精確使用時數、老化百分比 |
| 10,000Hz與三RPM設定 | 程式／文件設定 | 每次實際fs、轉速穩定、時鐘同步 |
| 清理後行位置 | 可恢復processed ordinal | raw開始／結束時間、stride、刪點mask |
| 105維公式 | 程式與限定數值抽查 | 原始物理量一致性、未記錄的設備變動 |

目前沒有實體馬達可重新採集，這不是本輪文件與工程工作停止的理由。我們不要求不存在的硬體，也不把推估欄位填成事實。只要現有紀錄沒有明確支持，session/run、時間、負載及單位就保留UNKNOWN。

若未來取得真正未曝露、來源可驗證的錄製，再依已有 ingest／exposure／final-test guard檢查。眼前沒有合格fresh資料，因此final validation未完成；這是資料資格的缺口，不是「程式能跑」可以修復的缺口。

<!-- PAGE_BREAK -->

## 7. 為什麼目前分數弱，以及能支持的結論

T1未知召回0%不是只靠總平均能發現的問題。保存診斷已核對真值、score方向、有限值與拒絕條件；部分方法的unknown分數全部低於固定門檻，部分方法排序也很弱。僅降低門檻可能增加健康誤報，不能用看過T1 test後的最有利threshold包裝成新成績。

得到支持的是跨motor表現不一致、部分配置高度混淆、校準轉移不足以及單一平均遮蔽弱群組。motor domain shift與特徵重疊是合理假說，但缺raw/session/單位證據，不能確定由老化、感測方向或某一次安裝造成。沒有時間戳與順序就不報每小時誤報或警報延遲；沒有退化真值就不報損壞比例或RUL。

Ledoit–Wolf是改善共變異數估計的來源，不是保證跨motor分類或未知排序的方法；本站逐類reference與另一motor的known-only分位數校準是專案適配。k-NN factory使用逐類平均鄰居距離，也不是把深層神經近鄰論文逐步照抄。參考 [Ledoit與Wolf，2004](https://doi.org/10.1016/S0047-259X(03)00096-4) 與 [Sun等，2022，ICML](https://proceedings.mlr.press/v162/sun22d.html)。

本輪結論是「現有三顆馬達有局部改善訊號，但未找到通過固定契約的方法」。所有資料已有test歷史，多組配置重複使用同一批samples，不能把126組或三seeds視為獨立受試個體，也不以逐窗IID窄信賴區間宣稱motor母體保證。

正式105維／linear／Mahalanobis-LW、PolarMap基礎及可切換factory k-NN未變。報告保留失敗方法、無效版本、未完成格子與未執行計畫；不因文獻提到一種方法，就將它列為已在本站實測。

<!-- PAGE_BREAK -->

## 8. 老師建議完成度與可重現證據

| 老師建議 | 判斷 | 已完成的證據 | 仍未完成 |
|---|---|---|---|
| healthy＋5known／4unknown | 完成類別配置與實測 | A／N=5全126組756評估；後續固定一組比較 | 可靠辨識未達標 |
| 隨機healthy＋N faulty驗證 | 已執行既有scope | N=1–8 sweep、N=9closed及B，總2490評估 | 後續新方法未重跑全N／全組合 |
| 群組切分有所依循 | 程序完成、資格部分完成 | documented motor角色、IDs、SHA、fit/cal audits | 原始採集／視窗及足夠test groups |
| 詳述「不完整」 | 文件完成 | 第5節逐項區分洩漏、覆蓋、來源與曝露 | 不以文書更正升級PASS |
| 可信fault type／unknown | 未通過 | 弱類別、T1unknown0%、健康誤報均保留 | 未找到符合固定契約方法 |

可閱讀的證據位於同一GitHub研究分支：[完整研究報告](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/research_closeout_20261005/final_report.md)、[文獻稽核與更正](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/research-improvements-20260920/reports/citation_audit_20261005)、[hard600原待辦核對](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/issue_delivery_20261005/hard600_closeout.md)。

既有歷史摘要入口：output/fault_type_matrix/2026-09-30-19-05-42、19-37-27、19-37-39；最後M摘要：output/fault_type_self_challenging_report/2026-10-05-22-17-39/summary.json.gz。大型封存另有D槽whole/member SHA與CRC恢復索引，不把同D槽備份稱異地備份。

本次重現核對命令：`.venv310/Scripts/python.exe -m experiments.fault_type_citation_audit --refs reports/citation_audit_20261005/refs.json --verify-existing`。它重算正式catalog與核對既有seals，不訓練、不更新正式資料。指紋、來源SHA與引用限制均保存在新版本交付索引。

我們目前能交付的是可重現的跨馬達比較、明確的失敗結果與切分效度說明，不能交付已可靠部署的模型。來源缺口仍由issue #9追蹤；本次老師回覆文件完成，不表示研究資格或模型可靠性已全部完成。
