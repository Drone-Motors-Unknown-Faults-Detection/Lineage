# 最佳化失敗診斷：27個train-only fits

2026-10-02開始，Asia/Taipei。先写手冊、鎖協定，再於commit38d3833推送後執行。這一批没有新增test預測，也沒有用calibration或test挑τ、預算或seed。Q02/Q04原12格INCOMPLETE留在原結果中。

## 修改了什麼

基礎是Q的LMNN啟發對角metric：fixed target k3、harmonic69、train class×RPM各20row、pull/push各.5、identity ridge.01、非負weights。原論文：[Weinberger與Saul，JMLR2009](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。原論文學完整PSD metric；本地已改為diagonal/mean/ridge/L-BFGS-B，不能稱完整LMNN復現。

三版本只改一個因素：hard150是完整原函數/原budget對照；smooth150把max(0,u)换成 .1*log(1+exp(u/.1))；hard600保留原函數，只把maxiter150→600、maxfun500→2000。其他ftol1e-9、gtol1e-6、maxls50與每fit120秒不變。

平滑函數來源：[Rennie與Srebro，ICML2005，Fast Maximum Margin Matrix Factorization for Collaborative Prediction](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf)，DOI10.1145/1102351.1102441，§3.3 Eq9 shifted generalized logistic。这里只移用scalar函數到triplet，不實作MMMF，也不把作者另一個smooth-hinge函數混為一談。τ=.1是本地預登錄unit-margin/10，不是原論文對本資料的最佳係數。解析gradient、穩定logaddexp/expit及差值界≤.5τlog2有單元測試。

## 實測

| train motor | seed | hard150 iter | smooth150 iter | hard600 iter |
|---|---:|---:|---:|---:|
| T1 |0|81|62|81|
| T1 |1|74|77|74|
| T1 |2|78|74|78|
| T2 |0|150未收斂|133|160|
| T2 |1|150未收斂|148|178|
| T2 |2|150未收斂|150未收斂|179|
| T3 |0|150未收斂|150未收斂|159|
| T3 |1|150未收斂|150未收斂|180|
| T3 |2|150未收斂|150未收斂|200|

收斂3/9→5/9→9/9。27個fits全完成，不等於全27收斂：10格的nonconvergence也保存weights、loss、gradient與停止理由。原Q failed fits的末權重沒有保存，不能把本次重新fit得到的權重說成當時原始產物。

diagnosis耗時241.820秒（run()內，不含前置CLI/import/parent檢查）；process peak1,988,169,728 bytes。seeds只改同train資料的class×RPM subset，不改三motor角色，也不是三次新增採集。training loss只有本fold本subset可比。

hard600僅需159–200iter便讓先前6格停止條件成功，支持原150上限不足。平滑150仍有4格未收斂，不能認為移除折點就解决所有問題。hinge折點／數值尺度可能共同影響速度，但没有單獨確證。所有成功格按ftol相對loss變化停止；projected gradient仍可能高於gtol（例如T3 seed1約2.37e-4），所以success不等於精確stationarity或泛化保證。

T3 seed2 hard loss .03604515→.03603580，只降約9.35e-6；其他failed→hard600差更小。loss差小不保證分類不變，亦不保證變好，需要新的完整outer protocol實測。不能用converged把Q缺格回填，也不調τ找更好的test分數。

## 驗證與未完成邊界

逐cell来源、config、seed、parent SHA、train IDs与weights SHA封存；source前後正式CSV unchanged。report程式只load train rows，重算27組saved loss與gradient，核對原Q三個已成功的hard150權重；實際終態與seal見solver_result_index.json及execution_log。所有cal/test/selection input IDs均空。

report數值重算PASS，三個原Q成功weights exact match。Python3.10.19／3.14.6各396tests、37CLI help與pip check PASS；9結果ZIP、190members的whole/member SHA及CRC PASS。交付跨至2026-10-03；備份以研究起始日2026-10-02分類，沒有覆蓋Q的8包或其他歷史備份。

已完成工程驗收與本次訓練診斷；沒有新的outer accuracy、unknown recall或健康誤報成績。下一步應為新的hard600 subset/all-train kNN兩完整方法、固定C02/M detector的配對outer比較；smooth150未通過9/9數值覆蓋，不挑成功seeds形成主成績。下一批仍需先寫手冊、鎖完整pipeline與提交後再執行，不能引用本頁宣稱已測完。

production105/linear/Mahalanobis-LW、kNN factory與PolarMap未改；可靠性contract未放寬。原資料全部曝光、session/raw-window證據UNKNOWN、fresh final與test group數INCOMPLETE。本輪没有新增馬達或時間序列，不能報RUL、老化百分比或廣泛部署保證。
