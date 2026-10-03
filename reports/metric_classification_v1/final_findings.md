# 實驗13結果：收斂不代表跨馬達改善

2026-10-03，Asia/Taipei。108／108評估、0模型失敗，1,040,760筆預測、28,910個unique samples。九模型實際train/cal來源重建、全部逐樣本重推與truth mutation通過。90CSV指紋前後不變。這是已曝露三馬達資料的探索性比較，不是新盲測或部署保證。

## 固定seed0描述結果

下表是三motor平均，不是最佳seed。closed-set known包括healthy；fault accuracy僅真正known faulty；conditional F1亦僅該子集。完整分母final fault F1另外保存於summary，不把healthy／unknown假陽性排除後的F1冒稱最終F1。

| 方法 | known accuracy% | fault accuracy% | conditional fault F1 | unknown recall% | healthy完整誤報% |
|---|---:|---:|---:|---:|---:|
| C17原harmonic69／LDA | 39.286 | 30.431 | .285191 | 8.436 | 14.126 |
| E01 identity子集5NN／C02M | 36.751 | 28.475 | .263065 | 18.437 | 19.721 |
| E02 hard600子集5NN／C02M | 33.632 | 24.968 | .202385 | 18.437 | 21.494 |
| E03 identity全部5NN／C02M | 36.756 | 28.464 | .252466 | 18.437 | 19.654 |
| E04 hard600全部5NN／C02M | 33.496 | 24.809 | .193146 | 18.437 | 21.536 |
| E05 identity單中心／C02M | 34.600 | 30.366 | .260646 | 18.437 | 42.635 |
| E06 hard600單中心／C02M | 34.743 | 25.504 | .190424 | 18.437 | 17.272 |
| E07 hard600三中心／C02M | 34.832 | 26.657 | .216842 | 18.437 | 22.769 |
| E08原式energy分類／C02M | 31.110 | 26.025 | .235710 | 18.437 | 42.550 |
| E09 identity5NN／同空間LW | 36.756 | 28.464 | .252466 | 8.436 | 19.654 |
| E10 hard6005NN／同空間LW | 33.496 | 24.809 | .193146 | 5.650 | 21.536 |
| E11 identity5NN／同空間kNN | 36.756 | 28.464 | .252466 | 7.476 | 28.896 |
| E12 hard6005NN／同空間kNN | 33.496 | 24.809 | .193146 | 7.899 | 21.536 |

H13a：子集5NN下降3.507百分點、全部5NN下降3.655百分點；收斂後距離未帶來穩健分類改善。H13b：三中心相對同metric單中心提高1.153百分點；energy相對metric子集5NN提高1.057百分點，但都不及原C17與完整安全契約。H13c：LW unknown recall從8.436%降至5.650%；k-NN從7.476%到7.899%，僅+0.423百分點，未解決最弱motor。

## 所有seeds與驚訝結果

| 方法 | seeds0/1/2的fault accuracy% | seeds0/1/2的conditional F1 |
|---|---|---|
| E01 | 28.475／28.083／25.764 | .263065／.263672／.240020 |
| E02 | 24.968／25.866／26.279 | .202385／.210398／.232823 |
| E03 | 28.464／28.464／28.464 | .252466／.252466／.252466 |
| E04 | 24.809／26.860／25.590 | .193146／.221548／.224360 |
| E05 | 30.366／30.366／30.366 | .260646／.260646／.260646 |
| E06 | 25.504／31.312／37.111 | .190424／.274613／.318022 |
| E07 | 26.657／24.737／23.456 | .216842／.207596／.198489 |
| E08 | 26.025／22.285／26.155 | .235710／.196996／.231126 |

E09/E11分類實值同E03，E10/E12同E04，差別在detector。E06的seed2達37.111%，但seed0只有25.504%，不能改成只報seed2。seed改train子集與中心初始化，不是新motor／session；變異只能描述算法敏感度。所有方法仍有motor類別召回0%，12個main_screen全部FAILED；B只有一組known配置、C無fresh／每類兩test groups，均未完成。

## T1與原因判定

T1全部E方法unknown recall=0%，未修好。E06的T1 healthy完整誤報0%，但unknown仍全數漏掉；只降低誤報不等於開集改善。E05的T1 fault accuracy46.845%，healthy誤報63.673%，也不能當可靠分類勝出。

同T1 seed0，E09/E10的unknown AUROC=.503254／.451674，E11/E12=.675970／.535752。這支持部分排序退化，不能只歸因門檻偏高；E11排序有些訊息但固定門檻未產生召回，需分開描述排序與校準位置。封存後分數分布入口另見exp13診斷手冊，不依診斷掃threshold。

已支持：本站正規化對角LMNN在train子集收斂後，跨motor分類仍弱且seed敏感；原式energy三項並非漏寫，較原分類器仍無穩健增益。可能：同一配置的多群結構、motor domain shift、calibration transfer，以及unknown配置與已知配置特徵重疊。未確認：raw/session/window/IQR/單位/安裝/負載的實際一致性；不能由投影或新／老機文件量化老化因果。此實測不反證原論文在其原資料上的效果。

## 分層交付

- VERIFIED：相同IDs、sourceSHA、motor角色、known fit／cal隔離、108格完整輸出與逐筆重推、完整健康誤報和final F1分母、數值來源核對。正式105／LW／PolarMap與factory k-NN不改。
- FAILED／INCOMPLETE：所有12方法的可靠性main screen；T1 unknown、最弱類別、三組known配置穩健性、真正獨立final test。
- UNKNOWN：實體序號／使用時數、session／raw邊界／window／IQR mask／sensor單位與安裝負載來源。

老師healthy+5 known／4 unknown的本輪固定配置已實際測試；其他N與126組不在本批重跑，沿用歷史證據。群組依文件支持的三motor切分，用途分離已驗證；原始採集獨立性與群組數不足仍無法洗牌修復。

報告checksum `cc05eabc98cfce711dda0999032fec524d0ea3ac720d82cf285365a7fa4b277c`。完整每motor／RPM／配置／seed與錯誤理由在本批summary。加入有效診斷後已備份11ZIP、413成員全SHA/CRC PASS，不是離站備份；依賴的舊parent模型／manifest／solver仍參照原有封存包。

封存後有效診斷 `output/fault_type_metric_failure_diagnosis/2026-10-03-15-07-58/diagnosis.json` 列432組分布。T1 seed0 unknown分數最大值依序E09=.771471、E10=.615236、E11=.996801、E12=.712990，全低於固定門檻1；18組E01/Q01與E03/Q03歷史對照逐筆精確一致。五項診斷測試兩環境通過；完整測試兩環境各437通過。早先兩次診斷的程式綁定問題與修正見execution_log，不採其未核對版本作已驗證證據。

下一批LFDA已事前鎖定並在fit後來源核對，與PCA做固定秩比較；尚未把它或後續GLVQ候選列為有效方法。後續仍需逐批有界協定、實測與固定契約，不因本批失敗停止研究。
