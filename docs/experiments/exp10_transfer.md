# 實驗十：少量目標健康資料能不能幫助跨工況

來源工況的健康基準可能不適合另一馬達或RPM。本實驗比較直接搬用、以少量目標健康資料平移、只用這些資料重新建基準；它沒有更新正式預設，也沒有神經網路遷移訓練。

## 資料與配對順序

從data-root掃描單工況105維clean池，來源／單位／未去重與raw限制見[實驗一](exp1_cold_start.md#資料與載入)。工況數d以實際掃描為準，程式沒有強制九格；九格才有9×8＝72個有向src→dst配對。不同motor是不同個體，不是老化前後。

每src用healthy列洗牌60/20/20、seed42，RobustScaler／LW中心共變異數只fit src train，src cal定confidence0.95線。預設method=ledoit_wolf；legacy例外用train定線。沒有k-NN CLI選項。dst fault全池只評估，不用來選N或調shift。

| 策略 | 目標端用途 | 實際評估集合 |
|---|---|---|
| direct，N=0 | 不適應來源模型 | dst全部healthy與fault |
| adapted，N=10／25／50 | dst健康列洗牌取N筆support；shift=median(support)−median(src train) | 剩餘healthy及fault都減shift，仍用src模型／src門檻 |
| scratch，同N | support內再60/20/20；train fit scaler／LW、cal定線；support的holdout不用 | 與同N adapted相同的剩餘healthy、同fault全池 |

_draw_support的support／eval索引不交集。單一default_rng(seed)隨src、dst、N遞進；不同N的support**不是巢狀子集**。direct只跑N=0完整目標健康池，**沒有在每個N扣除support重新算direct**；不能宣稱它與adapted是逐樣本完全配對。adapted和scratch在同pair／N才共用eval。source fit只用健康，unknown不fit／cal／選參。

N=10的scratch為6train、2cal、2不用的holdout，估計不穩與門檻不確定須保留。相同dst在不同src重複出現，72pairs不能當72個獨立馬達或採集。

## 怎麼使用

在repo根目錄依[環境政策](../runtime_policy.md)準備uv與資料：

```bash
uv run --locked python -m experiments.exp10_transfer --help
uv run --locked python -m experiments.exp10_transfer --data-root data --seed 42 --confidence 0.95 --method ledoit_wolf --n-values 10,25,50
```

API run(data_root="data",seed=42,confidence=0.95,method="ledoit_wolf",n_values=(10,25,50))回傳dict。CLI的N為逗號分隔，沒有專用train motor或Web執行卡；不是實驗五按鈕會附帶跑。沒有串流、續跑或中途取消，重跑重新fit。

每N須足夠建立train／cal且小於dst健康池長度；程式未完整驗證N≤0、N≥池大小，可能空集合或NaN／AUROC失敗，不能當成功。資料缺healthy／fault或工況不足先核對coverage，不造資料。多pairs會重複fit scratch，成本高於單工況，避免為讀手冊重跑。

## 輸出怎麼讀

main經setup_run寫logs/exp10_transfer/{ts}.log及output/exp10_transfer/{ts}/environment.json、summary.json、transfer_curve.png。rows鍵src／dst／n／strategy，healthy_accept是健康score≤1比例、fault_detect是fault score>1比例，AUROC是兩者排序；非known配置分類率。每row先round4，再按strategy×N等pair平均，不按樣本加權；沒有SD或逐樣本ID。

圖只畫AUROC曲線，須同時看JSON健康接受率；AUROC高但誤報高代表排序好、原警戒線仍不適合，不能直接部署。預期同N下adapted比scratch有額外價值才支持搬用來源模型；若無優勢如實記錄，沒有事先通用成功數字。direct與N>0的健康eval不同，跨N差值含樣本組成變動。

完整舊結果見[固定實測包](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/1fa9431bb7b86959f29540d07b2b9290ab39ce42/output/exp10_transfer/2026-10-09-14-11-31)。本流程只支持現有工況的小樣本探索，不證明新session／廣泛motor泛化、固定5%誤報或RUL。

## 方法來源與程式碼

Sun、Feng、Saenko（2016），*Return of Frustratingly Easy Domain Adaptation*，AAAI30,2058–2065，[原文](https://arxiv.org/abs/1511.05547)提出CORAL二階相關對齊；本程式**只平移median，沒有共變異數白化／重著色，不是完整CORAL實作**，shift公式為Lineage操作約定。LW來源見[實驗一](exp1_cold_start.md#方法來源與程式定位)。

[exp10](../../experiments/exp10_transfer.py)管support／eval、策略、指標與writer；[monitor](../../core/monitor.py)建基準；[test_exp10_transfer](../../tests/test_exp10_transfer.py)檢查結構與索引不重疊。資料處理沿Ancestor特徵來源，方法整合在Lineage，不依賴Ancestor可執行碼。
