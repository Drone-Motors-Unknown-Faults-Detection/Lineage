# 可反駁假說（不由 test 選 winner）

| ID | 觀察／機制 | 競爭解釋／反證 | 新消融／預期 | 推翻標準／train-only proxy |
|---|---|---|---|---|
| H-D | C17 分類提高，M recall 反降；分類與拒絕表示可以解耦 | 判別排序弱、cal transfer 可能比表示更重要；健康分類錯誤不會由解耦自動修好 | C17/C24 classifier 固定，C02 M/K detector；分類不變，拒絕等於 C02；健康完整誤報一併查 | paired classifier/score 若不完全對應，先判工程失敗；若健康/最差 unknown 無取捨改善則機制不足。train-only 可驗證來源及相同推論，不能保證跨馬達增益 |
| H-P | 相同類 cross-RPM 和 cross-motor shift；完全分 RPM C24 健康很差 | 馬達 shift 不因 RPM pooling 消失；每RPM資料少或 amplitude 有真識別訊息 | train RPM centroid/within-cov 向 pooled 收縮，β=0/.5/1；固定 C02 detector。期待跨RPM穩定、2screws 恢復 | 若部分收縮不優於兩端點或舊類/health惡化，假說不支持。train可看 covariance與分離，無独立内層 acquisition，不選β |
| H-G | harmonic shape 的 logit 尺度大，amp 保留已有正面控制 | affine contribution 不是重要度，交叉塊相關可能有用；global covariance/背景假設可能弱 | 三塊分開 LW covariance、每維平衡，amplitude保留；min-class 與 signed background λ1；C17固定 vs block nearest classifier | 若最差類/unknown無改善或完整health超限，不能以平均上升接受。train可手算距離與SPD；不能從test真類挑尺度 |

上述預期都可失敗。預先限定三個機制、各三個完整 arms，共9×3 folds×3 seeds=81格。
沒有獨立 development acquisition；本輪不選參、不訓練 large neural、不做任意 augmentation。
R17 routing 問題證據已確認，但不是本輪要修補成 PASS 的歷史失敗；新方法有新 ID。
