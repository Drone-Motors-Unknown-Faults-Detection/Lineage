# fault_type_accuracy_study_v2_json_contract：事前固定有限消融

v1 registry完整保留。v2只修正JSON roundtrip的RobustScaler參數容器：封存為list、呼叫sklearn時還原tuple，值仍[25,75]。沒有修改研究arms、參數、預算、class roles或test可見範圍；checksum為8418b7539670a3b4fd952e4a087b83bc18cb1870fbc4ef5eb4f44530b9523e5a，真實fit前已於5082df46fd2b605ec2d6aa56c331be943c94b4e5推送。

P0 3737fc216f002cc98ef1155967db46bae2ab8f08 已push並核remote一致。正式90CSV/28910rows指紋不變；原baseline不重fit。

第一組 A0–A8 完全照使用者配置：A0使用已封存75維／混合RPM基線；A1 RPM分層；A2去冗餘66混合；A3 66分RPM；A4 signed-log66分RPM；A5 ExtraTrees、A6 HGB、A7 shrinkage LDA、A8 RBF SVM皆75分RPM。A5–A8與A1共用scaler／references／thresholds，不再fit相同detector。

第二組 B1–B6一律以A1為底座，不挑A组優勝者：B1逐類LW＋global min-raw校準，B2 pooled within-class LW＋逐類門檻，B3 pooled LW＋global門檻，B4原kNN＋global門檻，B5/B6逐RPM逐類conditional conformal。完整公式、ties、零值、解析度與resolved參數由registry封存。

新邏輯評估：144 A組＋54 B組＝198。正常資料完整時，198新增分類器fit，180 factory detector/reference fit，加27 pooled residual covariance fit。這是內部子模型數，不是198個獨立馬達。A0另18個結果重用；105 baseline僅脈絡。每RPM已知六類齊全才執行，缺類保留NA不借樣本。

motor角色沿原三方向、seeds0/1/2。未知開發rows不用，validation/selection皆空，校準僅校準。不使用test batch均值／covariance／健康子集／pseudo labels。全部曝光、三motor及原採集UNKNOWN未解除，guard維持INCOMPLETE。

Signed-log與固定刪冗餘／RPM路由是本專案工程消融，不冒稱論文新演算法。ExtraTrees源自Geurts/Ernst/Wehenkel (2006)，SVM源自Cortes/Vapnik (1995)，boosting源自Friedman (2001)；HGB實作參數已核sklearn1.7官方文件。LDA只分類不投影；Conformal採class-conditional nonconformity、>= ties、alpha .05，不保證跨motor誤報5%。文獻與API連結詳registry。

不做global winner，不換正式105/linear/Maha-LW、PolarMap/binary。P6另立未來protocol，這輪不執行。
