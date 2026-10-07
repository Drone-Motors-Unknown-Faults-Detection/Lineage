# 導覽整理與驗收紀錄

工作始於2026-10-06，跨午夜至2026-10-07，Asia/Taipei。研究checkout：
C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree。
分支research-improvements-20260920；起點5be4c7865a721afaab3404a5481377f39ded7abd。

| 階段 | 實際工作／驗證 | commit與push |
|---|---|---|
| 來源與分工 | 完整AGENT、最新main64cb71d、PR36 head544d4ed核對；91研究／24main模組、16結果索引、250方法清冊；無新訓練 | dc9607b，已推送 |
| 七問／白話 | 主表七問＋實驗名；18模型歷史結果另列，負面結果及UNKNOWN保留；兩項文件結構測試 | 9908276，已推送；後續補S14與40次primary另記最終文件commit |
| 圖與操作契約 | 先寫Mermaid/SVG與三流程腳本；瀏覽器完整看圖並修正回路穿字問題 | 12813de，已推送；圖不更動算法 |
| 獨立UI與配對 | 新web.guide與guide.*，不改PR36檔案；15→17相關測試，兩環境667→669完整測試；兩個595筆配對且來源不變 | 1e2a5b4，已推送 |
| 更新狀態保護 | 重任務使用前一模型快照，tick不讀半更新模型；新增專用測試 | ec446b8，已推送；此commit保存時全套仍在跑，完成後兩環境各670 PASS、18相關PASS；不把未結束當PASS |

指令（repo根目錄）：兩環境分別python -m unittest discover -s tests；相關python -m unittest discover -s tests -p "test_navigation*.py"；兩環境python -m pip check；python -m experiments.navigation_regression；python -m experiments.navigation_data_contract；git diff --check。沒有pytest的環境改用repo既有unittest，未安裝套件。

Python3.10.19完整670測試91.541秒；3.14.6完整670測試88.674秒；兩者0失敗。相關18項2.032秒。pip check皆No broken requirements。既有sklearn單類警告、近常數precision loss、SVC probability棄用與Matplotlib暫存cache警告保留，沒有用升級依賴掩蓋。測試故意invalid CLI產生usage/error是預期拒絕案例。

正式資料重新load_formal_catalog：28910筆，fingerprint仍c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。配對亦核T1/8000每個CSV SHA前後相同。未知沒有在健康fit/cal出現；confirm後按原完整配置池流程納入已知。

配對output/navigation_regression/2026-10-07-00-00-02與00-06-37各一次LW／kNN，兩次摘要結果一致。每個method595筆＝健康40＋未知75＋更新後60＋A260＋B160，mismatches0；不是1190獨立受試樣本。未重跑歷史2490、E–M或重調任何門檻。

GUI紀錄：首次預演output/web_guide/2026-10-06-23-58-23（514 healthy、141注入、後續354筆；metrics畫面350是15筆更新節拍）；中間版本2026-10-07-00-03-06揭示counter／劇本來源文案需修正；修正後00-05-41完成A260/B160，精確結束metrics。00-12-33載入ec446b8後回合中止，保存到未知累積，沒有確認完成證據；續回合以07-59-20乾淨session重新驗證。逐筆CSV、model及fit snapshots均保留，不用截圖取代樣本log。

舊40次趨勢以Git唯讀取得11-34-24的summary/trials.csv，A/B各39/40；13-17-09各10次100%分列。舊18模型LW來源doc SHA4ff098e17db65326f976b01cbed12c419c821de7b129e7032958e8e3aa69a77c，只標文件回報，沒冒稱本輪重算。

282個既有tracked deletions未stage／restore。原105／linear／LW預設、kNN factory、PolarMap未改；沒有修改data、封存protocol／預測、Albert PR36或main。

2026-10-07早上續回合：GitHub main仍64cb71d、AGENT blob8f35a6bf（與固定main一致）；PR36仍open、未合併、head544d4ed。07-59-20實際確認47筆候選，224未知後更新，畫面391筆；模式／重連保留T1/8000與session1/epoch1/t391，console error/warn=[]。Ctrl-C後CSV只到390，最後1筆未落盤，標PARTIAL並保存原檔。

先補手冊，GuideHub新增pause flush，不改LiveDemo或科學計算。新3筆短log fixture通過；相關19項5.752秒PASS。08-03-05再次兩方法各595筆配對，mismatch0且summary SHA與00-06-37完全相同7ef02cfc7b7cf217a50f0b164b96001a8717af54b9d3e08878aac3a76d76c081。正式catalog再次28910/c4145…不變。

08-03-40 GUI最終版本：健康40（36接受、4拒絕、無候選）→匿名S03未知271→51筆候選確認→已知後256（250接受／6拒絕）；暫停畫面t567且CSV實讀到567，尾筆正常落盤。CLI候選75到達與GUI271後才按確認分開；不是把等候／操作延遲當算法發現延遲。研究模式數值表每15筆更新，暫停畫面244分母不是後段全部256；重連送完整metrics，可查看完整分母。

flush最終驗證：Python3.10.19完整671項265.109秒、Python3.14.6完整671項280.713秒，兩者0 failed；相關19項5.752秒，文件2項0.002秒；pip check兩者PASS。正式資料與配對SHA仍不變。01862fefcc6368bf46ab5cc8dd9f8f60a97cb80a已commit＋push，ls-remote完全相同。

08-03-40最後重連保留T1/8000與session1/epoch1/t567，model無重fit，完整後段metrics250/256；console error/warn=[]。確認已暫停且CSV567後停止自己的QA server；舊07-59-20缺1筆及00-12-33中斷log不覆寫。

依AGENT建立導覽交付issue #37：https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/37。已完成項勾選，主線整合保持待辦；沒有關閉#19/#30或合併PR36。

7256aaea7a832238b6871c066c0a5f93a2addc71交付文件與15張截圖，已push且遠端一致。封存前CSV逐檔補核：23-58-23為1005而非畫面1009；00-03-06為255；00-05-41 A260／B150（B畫面160）；00-12-33中斷後背景仍累積到5040，未確認，不當有界預演成功。這些修補前資料標部分／中斷前綴；08-03-40最終567完整與CLI配對作計算驗收。CRC只保證檔案未損壞，不補上缺少筆數。
