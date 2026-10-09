# #37：獨立導覽驗收

2026-10-08，基線c003e63。main已提供獨立web.guide及README文件入口；原首頁尚無直接導覽按鈕，#37最後一項仍未完成。只補文件與配對追溯，不改`web/server.py`、`index.html`、`experiments.js`、health_monitor或串流。

## 本輪驗證條件

Python3.10.19，seed42，LW/q95與kNN5 factory。唯讀`D:/schoolshit/專題/src/Lineage/data`有T1/T3×6000/8000/11000rpm六工況60CSV，清冊指紋82534111c7901bfe0709637f4979976ce73445a54353e7c377e71e40b4cf2abd。互動與配對以T1/8000為準；六工況清冊不是六工況都完成同樣UI操作，更不是九工況研究。

```powershell
python -m web.guide --data-root D:/schoolshit/專題/src/Lineage/data --port 8613 --seed 42 --rate 10
python -m web.guide --data-root D:/schoolshit/專題/src/Lineage/data --port 8614 --seed 42 --rate 10 --openset-method knn
python -m experiments.navigation_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42
python -m tests.integration_evidence --phase candidate --data-root D:/schoolshit/專題/src/Lineage/data
```

瀏覽器為Codex In-app Browser（iab）。工具未提供引擎完整版本，DOM只讀環境的navigator存取失敗，因此版本保留UNKNOWN；不以安裝的Chrome／Edge版本冒充實際使用版本。URL為`http://127.0.0.1:8613/assets/guide.html`與8614同路徑。均只綁127.0.0.1，不公開服務。

## 瀏覽器實際操作

- 三入口切換可見冷啟動／未知學習／趨勢標題；研究模式展開七問及fit來源，返回展示模式不重訓。
- 馬達／RPM選單實列六工況，選T1/8000、確認來源後才建立健康基準。
- Maha session1/epoch1先重播健康164筆，切S03，候選確認前只顯示匿名來源；423筆暫停時隔離259、候選56筆、範圍[165,239]。候選索引是重播索引，不是raw時間。
- 確認後才顯示5screws，known由健康一類變成兩類，隔離清空；完整配置池重擬合為oracle模擬，不能稱只用到達候選學習。
- reload後session1/epoch1及423筆、兩known保留。重設操作曾遇瀏覽器工具逾時，後續log21:55:05及重新開頁一致顯示epoch2、0筆、只健康，證明重設最終完成；不掩飾工具操作延遲。
- kNN乾淨健康基準播放A，260筆後自動暫停，顯示gradual t100／中間帶33／延遲60筆。Maha重設後播放B，結果另見同目錄產物與下方落盤核對。這是兩方法的功能操作，不以不同方法A/B成績作相互勝負。

外部瀏覽器截圖在 [驗收附件](browser_screenshots)，包括anonymous、candidate、confirmed、reset_reconnected、trend_a與trend_b；原始模型／fit檔仍在`output/web_guide/2026-10-08-21-50-53`及`21-55-14`。終止前暫停，最後關閉client／server後核對CSV與model尾筆，詳見執行紀錄。截圖不包含未匿名化的確認前答案；截圖搬移沒有改模型或CSV。

## 逐筆跨入口配對

`output/navigation_regression/2026-10-08-21-52-04/summary.json`：Maha595筆、kNN595筆，各0 mismatch，兩方法均75筆fault arrival後找到候選。比較同方法LiveDemo CLI與GuideHub，而非把兩方法分數強迫相等。保存pair_id、epoch、實際draw特徵SHA、有限值列候選索引、雙邊t/score/verdict/PCA/EWMA/CUSUM/quarantine/attempts/phase；同值多列保存全部索引，沒有偽造唯一raw ID。fit/cal/holdout索引及來源CSV SHA另存，來源前後相同。

新增ledger測試第一輪因測試先取bound draw而繞過記錄wrapper，112 passed／1 failed；修成呼叫當下解析draw，不改實驗計算。保留失敗產物21-55-00，修正後完整測試結果記執行紀錄。

## 可發布但尚未發布的#37草稿

獨立導覽及文件入口已在main，這輪重新做真實可用T1/8000 browser QA及兩方法各595筆逐列配對，0差異；六工況60CSV清冊已保存。原首頁直接入口尚待與PR36重疊部分協調；完整瀏覽器引擎版本本工具無法取得。請保留最後checkbox未勾選，不關閉#37。health_monitor串流與#35未改；fresh仍INCOMPLETE，raw/session仍UNKNOWN。
