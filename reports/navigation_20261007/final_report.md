# 實驗整理與逐步導覽交付

日期：2026-10-07，Asia/Taipei。本輪完成實驗七問、白話解釋、流程圖、操作契約與獨立導覽；沒有啟動新方法搜尋或調參。原105維、linear研究預設、Mahalanobis–Ledoit–Wolf與PolarMap未改，k-NN仍走原factory。

## 給老師的閱讀順序

1. [實驗總覽](../../docs/navigation/實驗總覽.md)：24個家族／協議列，每列實驗名稱加七個問題。
2. [結果白話解讀](../../docs/navigation/結果白話解讀.md)：結果、可能解釋、未確認推論與資料限制分開。
3. [研究流程圖](../../docs/navigation/研究流程圖.md)：[Mermaid原稿](../../docs/navigation/研究流程圖.mmd)與[SVG](../../docs/navigation/研究流程圖.svg)。
4. [UI操作腳本](../../docs/navigation/UI操作腳本.md)與[示範腳本](../../docs/navigation/示範腳本.md)：按實際狀態走完整個核心故事。

老師先前兩個問題的逐項回覆保留在[reply.md](../teacher_reply_20261005/reply.md)。研究導覽總入口是[README](../../docs/navigation/README.md)，來源與逐批分母在[來源索引](../../docs/navigation/來源索引.md)。

## 本輪做了什麼

盤點起點research 5be4c786、main 64cb71d：91個研究模組、24個main模組（包含工具，不是115次實驗）、16個結果索引、250項既有方法／分數清冊。新兩個導覽助手另列，不冒稱已重跑歷史矩陣。歷史2490評估、Q與E–M及負面／未完成結果保留；Group DRO仍未實作。

補核兩個容易混淆的歷史來源：exp3主要40次批次A/B各39/40＝97.5%，另10次批次各100%，分開列而未挑高分；早期18深層模型LW/OAS/MCD成績只標「文件回報」，不是本輪formal105逐筆重算，也不能把全部提升歸因單一共變異數估計。

先提交圖與操作契約，再新增web.guide及guide.html/js/css；重用LiveDemo、Hub、core.openset與exp2/3。判定、分群、校準沒有移到前端。三主入口共用session，研究模式只展開來源與七問表。未知來源匿名、候選只顯示ID／size；模擬confirm後才顯示配置代碼。既有後端truth快取及確認後完整標記池重擬合的限制可見。

## UI映射與實際驗收

| 腳本／元件 | API與計算來源 | 實際驗證／保留限制 |
|---|---|---|
| U0/U1 資料卡／inspect／build | WS inspect/build；navigation_data_contract、LiveDemo健康fit | T1/8000、seed42，健康313＝187train/62cal/64holdout；缺資料／小池拒絕由fixture測，不是正式成績 |
| U2/U3 分數圖／start／source | WS start/pause/source，core.openset＋ScaleGrowthSession | 健康無候選、匿名S03未知累積；>1拒絕、>2隔離不變；最近中心／raw距離未提供 |
| U4/U5 候選／confirm | 候選ID guard，既有confirm與模型snapshot | 實際候選→learned→兩known；不自動確認、不稱25筆保證。rejected_known分支沿用核心／工程測試，未宣稱本輪瀏覽器出現 |
| T1 劇本按鈕／EWMA | SCENARIOS＋TrendMonitor | 瀏覽器A260/B160完成自動暫停；只稱CSV劇本，不換算秒／壽命 |
| R/P/E/X 模式／暫停／重連／重設 | 前端呈現切換；GuideHub狀態與原LiveDemo | 切模式時t與模型不變；重連保留T1/8000、session1/epoch1/t391，沒有fit/start；重載不保留瀏覽器折線歷史或上一筆sample卡，不假裝重播 |
| busy／error／stale | GuideSocket用途guard、前一模型快照 | fixture覆蓋未fit、重複／過期確認、更新並行、串流error與session保留；不是實際硬體故障測試 |

桌面1280與窄屏390實看，窄屏卡片重排、表格局部捲動、鍵盤focus可見。最終重連的console error/warn查詢為空；server的favicon 404是未提供圖示，不是演算錯誤。沒有宣稱未量測的完整網路負載或無障礙認證。

## 計算一致性與效能差異

固定T1/8000、105維、seed42、q95，LW與kNN k5各595筆：健康40＋未知75＋更新後60＋A260＋B160。新GuideHub與原LiveDemo逐筆score/verdict/PCA/EWMA/CUSUM/隔離/attempts/phase相同，兩方法合計1190筆配對、mismatch 0。兩者未知75筆時形成51筆候選，confirm＝learned 5screws；使用完整212筆配置池重新切分擬合，沒有改成arrival-only。

| 方法 | A警報／中間帶／延遲（筆） | B警報／中間帶／延遲（筆） | 新舊判斷差 |
|---|---|---|---|
| Maha–LW | 99／43／59 | 48／6／8 | 0 |
| kNN | 100／33／60 | 49／6／9 | 0 |

這是工程配對，不是1190個獨立受試樣本，也不是準確率提升。跨馬達歷史known 29.63%→34.15%（+4.52百分點）、unknown 15.07%→18.44%及T1 unknown 0%仍是舊研究結果；本輪沒有改善或替換這些模型。

## 實際畫面與log

來源在output/navigation_qa/2026-10-07：01–03首次預演，04是修正文案前的開發畫面；05/06修正後A/B、07窄屏、08匿名候選、09更新後、10最終流程圖、11重連。保留舊圖作修補證據，不混成最終版本。

首次23-58-23 session：健康514、注入141、更新後354筆；畫面後段n350受15筆metrics節拍影響。00-03-06發現counter、劇本來源文字需修正；00-05-41完成A260/B160及結束metrics。00-12-33續跑被回合中止，只有健康基準與未知累積，沒有宣稱確認完成。

07-59-20 session實際224筆未知後確認47筆候選，畫面t391，後段接受163/167≈97.6%。Windows Ctrl-C留下CSV到t390（224未知＋166已知後，162接受），最後1筆沒有落盤；這份log標PARTIAL，不補造。以此發現暫停未flush的持久化缺口，新增只涉及新導覽的flush保護與3筆fixture測試；保留該舊session。

分群發現筆數依先播健康及抽樣器狀態改變：51筆候選／75筆到達是固定CLI回歸；47筆候選是此GUI session，不能互換。未知拒絕與已知接受率均非物理健康恢復或自身配置accuracy。

flush修補後08-03-40另走乾淨session：健康40筆，36/40接受、4/40拒絕，隔離0且無候選；匿名S03累積271筆後按確認，候選51筆；確認後256筆中250接受、6拒絕＝97.66%。暫停畫面t567，直接讀CSV末列亦t567＝40＋271＋256，未滿15筆的尾端正常落盤。GUI271是按確認的累積量，不稱算法直到271才發現；固定CLI仍75筆發現。12/13/14截圖為此修補後健康／候選／更新狀態。metrics沿既有15筆節拍，畫面當時後段n244，完整分母以CSV／重連完整metrics為準。

## 結論分級

VERIFIED：七問與來源索引、原稿與SVG、三入口／兩模式、答案遮蔽、固定計算一致、formal fingerprint不變、既有default未改。工程tests通過只限程式行為。

FAILED／INCOMPLETE：現有跨馬達可靠性契約仍未通過；T1未知零召回未解決，全部28,910筆曾曝光，沒有合格fresh final。原首頁整合尚未做：PR #36仍OPEN／未合併，head544d4ed8；未修改其server/index/experiments/exp1/3/4/health paths。

UNKNOWN：raw session/run／window interval／stride／刪點／時間／取樣率／安裝／單位／負載。三motor文件身分存在，但個體與老化混雜。本輪不要求不存在的硬體或用文字修正把UNKNOWN變PASS。

## 重現與交付

在研究checkout根目錄執行：

```powershell
.venv310/Scripts/python.exe -m web.guide --data-root data/formal_local --port 8601 --seed 42
.venv310/Scripts/python.exe -m experiments.navigation_regression --data-root data/formal_local
.venv310/Scripts/python.exe -m unittest discover -s tests
venv/Scripts/python.exe -m unittest discover -s tests
```

瀏覽器開http://127.0.0.1:8601；資料檢查與build必須明確按，不自動fit。兩完整Python版本、逐階段commit/push與最終flush補驗在[execution_log](execution_log.md)，機器索引在[result_index](result_index.json)。本輪不合併main、不關閉無關issue，D槽ZIP由既有archive工具驗CRC與SHA，舊備份不覆蓋。

最終Python3.10.19／3.14.6各671項PASS、0 failed（265.109／280.713秒）；相關19項PASS，兩pip check正常。flush修補01862fe已推送並核對遠端。截圖15為最終重連，後段分母256，session/epoch/t567及兩known保留；console error/warn查詢仍空。其餘逐階段交付與外部ZIP證據由後續交付索引記錄，不把尚未執行的備份先寫PASS。

導覽交付[issue #37](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/37)：五個已完成項已勾選；保留PR36後主線整合待辦，所以issue仍OPEN。這不等於其他研究issue已完成。
