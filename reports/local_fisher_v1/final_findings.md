# 實驗14結果：PCA有局部改善，LFDA未通過跨馬達契約

2026-10-03，Asia/Taipei。144／144評估完成，0缺失，1,387,680筆預測、28,910筆unique samples。36個projection及其分類器／reference／calibration已由known train與calibration重建；144格全部重推精確相符，truth mutation不影響推論。資料90CSV指紋前後不變。

## 方法、來源與改編

依Masashi Sugiyama（2007），*Dimensionality Reduction of Multimodal Labeled Data by Local Fisher Discriminant Analysis*，JMLR8:1027–1061，[原文](https://www.jmlr.org/papers/volume8/sugiyama07b/sugiyama07b.pdf) Eq.9–12自行實作。已核對§3.1–3.3、公式頁及§6，未宣稱逐頁閱讀全文。原法的局部類內幾何被保留；新增固定ridge、每類RPM20筆train子集、零尺度保護、10／20正特徵方向、固定sign，是本專案改編。PCA同一子集full SVD、whiten=false作無label對照。參數及方法在評估前commit，沒有事後選最好秩／seed。

上游harmonic69、三motor方向、N=5配置、seeds0/1/2與factory門檻.95沿用原manifest。分類使用全部known train；未知不fit／cal／選參。方法和參數已看過歷史資料才提出，故本批仍exploratory；本次事前封存不會清除歷史曝露。

## 全部固定方法

seed0為三motor平均，非最佳seed。fault accuracy／conditional F1僅true known faulty；healthy完整誤報包括healthy→known fault與healthy→unknown，兩者不重複。完整分母final fault F1另存summary，含healthy與unknown假陽性。

| 方法 | known accuracy% | fault accuracy% | conditional F1 | unknown recall% | healthy完整誤報% |
|---|---:|---:|---:|---:|---:|
| C17 harmonic69/LDA | 39.286 | 30.431 | .285191 | 8.436 | 14.126 |
| F01 PCA10/LDA/C02M | 34.336 | 28.438 | .218377 | 18.437 | 34.272 |
| F02 PCA10/5NN/C02M | 41.006 | 33.420 | .298515 | 18.437 | 18.947 |
| F03 PCA10/5NN/LW | 41.006 | 33.420 | .298515 | 6.237 | 18.947 |
| F04 PCA10/5NN/kNN | 41.006 | 33.420 | .298515 | 3.917 | 29.458 |
| F05 PCA20/LDA/C02M | 33.313 | 26.448 | .245171 | 18.437 | 30.286 |
| F06 PCA20/5NN/C02M | 37.126 | 28.912 | .255941 | 18.437 | 19.688 |
| F07 PCA20/5NN/LW | 37.126 | 28.912 | .255941 | 6.038 | 19.688 |
| F08 PCA20/5NN/kNN | 37.126 | 28.912 | .255941 | 6.152 | 24.873 |
| F09 LFDA10/LDA/C02M | 31.502 | 23.035 | .156792 | 18.437 | 24.762 |
| F10 LFDA10/5NN/C02M | 35.713 | 28.292 | .221458 | 18.437 | 26.086 |
| F11 LFDA10/5NN/LW | 35.713 | 28.292 | .221458 | 7.149 | 26.086 |
| F12 LFDA10/5NN/kNN | 35.713 | 28.292 | .221458 | 6.065 | 26.086 |
| F13 LFDA20/LDA/C02M | 32.632 | 23.852 | .208115 | 18.437 | 21.435 |
| F14 LFDA20/5NN/C02M | 35.747 | 28.231 | .220834 | 18.437 | 25.567 |
| F15 LFDA20/5NN/LW | 35.747 | 28.231 | .220834 | 6.562 | 25.567 |
| F16 LFDA20/5NN/kNN | 35.747 | 28.231 | .220834 | 6.057 | 25.567 |

F02相對C17 fault accuracy+2.989百分點、known accuracy+1.719百分點、conditional F1+.013324；F1未達固定+.02要求，healthy誤報+4.821百分點，最弱類別召回仍0%。同一PCA10/5NN接新LW，unknown recall從C02M的18.437%降至6.237%；接kNN更降至3.917%。分類／偵測必須分開判定。

## 種子、motor與失敗

| 分類方法 | seeds0/1/2 fault accuracy% |
|---|---|
| PCA10/LDA | 28.438／25.440／27.882 |
| PCA10/5NN | 33.420／34.013／33.359 |
| PCA20/LDA | 26.448／26.174／27.540 |
| PCA20/5NN | 28.912／28.795／28.234 |
| LFDA10/LDA | 23.035／25.635／28.962 |
| LFDA10/5NN | 28.292／28.353／32.941 |
| LFDA20/LDA | 23.852／28.477／24.595 |
| LFDA20/5NN | 28.231／28.627／33.119 |

同一表示法5NN的三detectors共用分類器，不算三個獨立分類試驗。seed影響train子集，不代表新motor／session。PCA10在本batch較好，仍不能事後當成selected winner。LFDA10相對PCA10的5NN fault accuracy seed0下降5.128百分點、F1下降.077057；相同已知局部結構未帶來可轉移的分類優勢。

T1 seed0：F02 fault accuracy44.883%、unknown0%、healthy誤報32.291%；F10 fault accuracy17.536%、unknown0%、healthy誤報7.871%。F14降低healthy誤報至6.660%，fault accuracy17.435%、unknown0%，不能只取誤報改善。F04／F08的T1 unknown召回僅.078%／.340%，不符合10%最低要求；其餘F方法T1為0%。

16方法main_screen全部FAILED，均有motor／類別召回0%。每motor／RPM／class／seed及失敗原因完整保存，不依已曝光T1挑feature或掃門檻。本輪不支持「LFDA處理了domain shift」；支持此有限改編在現有三motor跨折未得到穩健增益。calibration transfer、類別特徵重疊仍可疑，缺raw/session證據不能確認因果。

## 分層結論與老師建議

- VERIFIED：固定N=5 healthy+5 known／4 unknown已實際執行；每fold train/cal/test不同motor、無selector／空validation、known-only fit/cal、source SHA／逐樣本重算。Python3.10.19與3.14.6完整測試各437通過、pip check／原37CLI通過。新LFDA CLI另查help通過。
- FAILED／INCOMPLETE：16方法可靠性main screen；最弱motor／類別；僅一組known配置，不具三組子集穩健性；沒有fresh final test、每類兩test groups仍不足。老師其他N／126組不在本批重跑，不能以runner能接manifest當成已重跑。
- UNKNOWN：原始錄製、視窗、IQR刪點、單位、安裝、負載與獨立採集；T1新／T2T3老與個體混雜，不能串成生命週期。

正式105／linear／Mahalanobis-LW、PolarMap及factory k-NN可切換路徑全部保留。report SHA `7a5c3019d4eeefd2abf710c4c385c3fe9eecba4a426f61c71c30cc596da32731`。大型產物主目錄與備份見result_index；D槽單卷不等於離站備份。後續候選GLVQ需自己的手冊、固定協定、來源核對與實測，不能由本輪失敗推出其有效。
