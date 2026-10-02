# Q 批：完成驗證，但未達可靠性目標

2026-10-02，Asia/Taipei。前一輪已封存模型與評估，本輪從checkpoint接續重推論、報告、雙runtime驗收與備份；沒有重訓Q，也沒有重跑歷史2,490格。

## 實際執行與結果

固定8方法×3motor folds×seeds0/1/2=72格；60完成、12 INCOMPLETE。Q02/Q04各只有T3 test的3格，不能拿局部結果與完整三馬達平均比較。原因是trainT2/T3的6個diagonal metric fit達150iter上限，原失敗權重/最後loss沒有保存，仍UNKNOWN。576,144筆預測涉及28,910 unique樣本，90份正式CSV指紋維持 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。

下表為seed0三motor等權平均；fault只計known faulty，不含healthy，沒有混入拒識。健康總誤報包含被分類為已知故障及被判unknown。完整逐seed/motor/RPM/class、混淆矩陣與配對差異在sealed summary；不選global winner。

| 方法 | known accuracy | fault accuracy | fault macro-F1 | unknown recall | 健康總誤報 |
|---|---:|---:|---:|---:|---:|
| C02：75維linear/LW，歷史 |34.15%|26.61%|.2404|18.44%|26.87%|
| C17：harmonic69 uniform LDA，歷史 |39.29%|30.43%|.2852|8.44%|14.13%|
| C24：perRPM harmonic LDA，歷史 |32.17%|30.91%|.2866|21.07%|63.41%|
| D01：C17 classifier+C02 detector，歷史 |39.29%|30.43%|.2852|18.44%|14.13%|
| Q01：identity subset kNN5+C02 |36.75%|28.48%|.2631|18.44%|19.72%|
| Q03：identity all-train kNN5+C02 |36.76%|28.46%|.2525|18.44%|19.65%|
| Q05：gain63 uniform LDA+self LW |36.01%|32.80%|.2826|7.57%|46.27%|
| Q06：gain66 uniform LDA+self LW |35.05%|30.99%|.2828|7.92%|43.53%|
| Q07：gain69 uniform LDA+self LW |39.82%|33.92%|.3041|8.71%|29.14%|
| Q08：gain66 LDA+C02 detector |35.05%|30.99%|.2828|18.44%|43.46%|

Q07相對C24 fault accuracy +3.01百分點，相對C17 known accuracy +.54百分點、fault macro-F1 +.01893；未达到預定+.02 F1門檻。相對D01，健康總誤報+15.02百分點、unknown recall−9.73百分點。這是tradeoff，不是全面改善。gain63/66/69為本地改編，公式、原來源與變更在既有source ledger及adaptation cards；subset/metric是LMNN啟發而非原論文完整復現。

| Q07 test motor | fault accuracy | unknown recall | 健康總誤報 | 2screws recall |
|---|---:|---:|---:|---:|
| T1 |27.99%|24.71%|64.98%|0%|
| T2 |44.88%|0%|15.56%|0%|
| T3 |28.89%|1.41%|6.88%|0%|

Q05/Q06/Q07的T1 unknown recall分別22.70%/21.34%/24.71%，因此「T1永遠無法離開0%」不成立。但健康誤報99.80%/64.48%/64.98%，未知召回改善伴隨嚴重副作用；T2 unknown仍0%。Q05–08的確定性流程三seed相同，不是三個新增馬達。各方法至少一motor/RPM健康總誤報100%，且完整方法均未通過既定contract。Q02/Q04為INCOMPLETE而非補零FAILED。

## 證據分級與老師問題

- VERIFIED：固定方法與三motor用途分離，selection IDs為空；未知不fit/cal；來源/model/predictions SHA、576,144筆逐筆重推論、真值mutation不影響推論、保存指標重算、paired相同test IDs完成。Python3.10.19及3.14.6各378 tests、34 CLI help、pip check皆PASS。
- FAILED：六個完整Q方法未達健康誤報、逐類／逐motor未知召回等可靠性要求；不能換production。INCOMPLETE：Q02/Q04缺12格，fresh final沒有合格資料、每類至少兩個獨立test groups guard仍未通過。
- UNKNOWN：raw recording/session、stride/window overlap、原file-level清理mask、感測器單位/安裝/負載等未補造。T1/T2/T3為文件支持的三顆不同馬達，不能串成退化生命週期。

老師healthy+5 known faulty/4 unknown的主要配置已完成本輪對照；其他N與126組是既有歷史成果，本輪沒有重跑。程式切分依據和selector/val-cal依賴已修正，不等於完整來源獨立性。全部資料歷史曝光，因此研究仍exploratory，不能支持廣泛部署或固定誤報保證。

## 封存與下一批

Q verification seal 9592116f9bcc9bb389dd13f7e9f80e6fd051e090f2f9ce6d5de15bfa60868112；report seal 88d34b9ef3e25a3e6e0376da6ede26e20dfdb399a38741704aa1001898e88ab9。8 ZIP/233原始產物members已驗whole SHA、每member SHA及CRC；原檔未刪，D槽同機備份不是offsite備份。models/predictions/full audits在包中，Git保留compact與索引。

下一批僅做train-only solver診斷：hard150、smooth150、hard600共27 fits，手冊先寫；訓練收斂不能宣稱準確率提升。舊Q protocol、models與失敗格不回填。正式105/linear/Mahalanobis-LW、kNN factory與PolarMap皆保留。
