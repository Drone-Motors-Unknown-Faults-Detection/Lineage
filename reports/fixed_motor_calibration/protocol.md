# P1：固定方法、專用馬達校準

P0 `08aa1d5529a1764ddf93c50f2f10376bdb0c583f` 已 push，remote SHA 相符。

新版本 `fixed_methods_motor_calibration_v1` 不執行模型／表示法／超參數選擇。fold 0 T1 train / T2 calibration / T3 test；fold 1 T2 / T3 / T1；fold 2 T3 / T1 / T2。validation 及 selection IDs 明列空清單，不是第四顆馬達。

沿用第一組歷史 N=5 manifest：healthy=8screws；known faulty=1screws、2screws、3screws、3_14screws、4screws；unknown=4_146screws、5screws、6screws、7screws。開發馬達 unknown 不使用。後續入口可接收同格式既有 N/class manifests，本輪只執行這組，不重跑126組或N sweep。

固定 baseline105 / vibration75 × Mahalanobis-LW / factory kNN，3 folds × seeds 0/1/2：36 detector evaluations，共享18次分類器擬合。seed 不改馬達角色、樣本順序或切分。RobustScaler 實值、LogisticRegression 完整 resolved params、C=1、balanced、lbfgs、1000 iter、tol=1e-4、confidence=.95、k=5 都封存在 protocol JSON；兩表示法都沒有 PCA。原分類器 random_state=None，lbfgs 不使用隨機性；seed記錄不製造新資料。

每類模型/reference 僅 fit train；每類另一馬達 calibration 距離 .95 分位數，只決定既定門檻。score=min(raw distance / max(class threshold, float epsilon))，score>1 拒絕。不同類門檻不同，診斷保存逐類 raw distance/threshold，不能把最小 raw distance 當成正式正規化 score。

9個可觀測組合是3 motor × 3 RPM（6000、8000、11000），不是9種負載或9種物理故障。每折 test 只有一motor的3 RPM，每RPM 10種螺絲配置；其他motor/RPM對該折屬train/cal/unused，非缺失或新增獨立test。

這是執行前鎖定的探索性比較：方法清單已受歷史結果影響，全部資料早已曝光，不是盲測。取消 selector 只消除此次共同選模型依賴；無法洗掉歷史曝光、未知session/raw overlap、整檔IQR前處理或個體/老化混雜。至少兩test groups的舊guard不放寬。資料資格依舊 INCOMPLETE。

核心矩陣封存後再診斷T1，不回寫threshold/k/features；不擴展六種馬達方向，不計RUL/退化百分比/每小時誤報。摘要只列固定方法及描述性motor範圍，不產生deployment winner。
