# 第一批假說與匹配消融（尚未執行）

H-L：C17 train2screws100%，跨motor0；非樣本完全缺失。固定大margin局部metric或許減少冗餘尺度，競爭解釋是train-only metric仍過擬合motor且故障配置本身不可分。
Q01 identity/subset kNN；Q02 diagonal LMNN-inspired/subset；Q03 identity/alltrain；Q04同Q02 metric/alltrain。皆harmonic69父train scaler+C02/M detector。Q01↔Q02/Q03↔Q04分離metric；Q01↔Q03/Q02↔Q04分離reference量；不能將subset random row稱獨立development。
J(w)=.5 mean_target d_w(i,j)+.5 mean_all_diffclass_triplets max(0,1+d_w(i,j)-d_w(i,l))+.01 mean_d(w_d-1)^2，w>=0。
原LMNN為full PSD/原sum且無identityridge；本地diagonal/mean/ridge為明確改編。初始Euclidean同類3target固定；20row/class/RPM subset上限360，seed0/1/2；不看test/cal選超參數。k5distanceweighted保持。
若optimizer不收斂：INCOMPLETE而非默默換算法；有限150iter/500eval/120sec。handcalc/finite difference/nonnegative/determinism測試。

H-R：幅值尺度與motor shift可能混雜；以per-row RMS比值保留形狀，競爭解釋幅值是重要故障signal。
Q05 dimensionless63：各軸11stats（RMS之外、移除冗餘9/12/13）+10harmonic proportions；dimensionful stats以該row RMS除。Q06加3log1p(sum abs harmonic maxima/RMS)relative amplitude=66；Q07再加3log1p(RMS/trainfloor)absolute amplitude=69；Q08 Q06clf+C02/M獨立detector。
Q05→Q06測relative幅值，Q06→Q07恢復absolute幅值；Q06↔Q08相同clf只換detector。均uniformprior LDA lsqr/shrinkageauto，factoryMhaLW/confidence.95，alltrain-onlyscaler/floor，knowncal-onlythreshold。
RMSfloor=max(train medianRMS*1e-6,1e-12)，harmonic proportions使用train harmonic floor；floor inactive的正gain不變性可測，不把floor-active當全域exact invariance。舊formal欄位與harmonic69不改，新維度獨立版本。
成功需固定CONTRACT，反例/seed/motor/RPM/worstclass/health/unknown全記；若未通過仍追下一個有新資訊的機制，不掃test係數。

