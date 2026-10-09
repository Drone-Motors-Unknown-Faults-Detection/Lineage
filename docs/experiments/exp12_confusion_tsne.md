# 實驗十二：把錯分位置與特徵分布畫出來

總準確率看不出哪類被拒絕。這個實驗畫二元及開集多類混淆矩陣，再用t-SNE看特徵鄰近關係；圖片用來診斷，不訓練新的故障分類器或調整門檻。

## 三部分如何用資料

使用各工況105維clean特徵，來源／每列／單位／未去重與raw限制見[實驗一](exp1_cold_start.md#資料與載入)。沒有強制九工況；T1／T2／T3是不同馬達，不能把全域表當同顆馬達時間序列。

a：每工況healthy列按seed42切60/20/20，train fit RobustScaler與LW、cal定confidence0.95線；healthy holdout與fault全池score，≤1叫healthy、>1叫fault。各工況結果累加成2×2**原始筆數**矩陣，樣本多的工況權重較大。

b：重用[實驗十一](exp11_ancestor_comparison.md)build_ancestor_monitor，known為8／1／2／3／4，unknown為5／6／7／3_14／4_146交集，分別LW與legacy。known各holdout、unknown全池classify後合併unknown，1screw／1screws顯示名統一成1screw，形成固定六標籤矩陣。缺類不代表完整coverage；legacy label=-1使classify無法返回known，不能將全部拒絕解讀成單純協方差差異。unknown未進detector fit／cal。

c：每工況另建LW的A協定monitor，按default_rng(seed)每配置抽最多200列（不放回），**從完整池抽，包含known train／cal／holdout**。用該monitor的train-only scaler transform，再讓t-SNE在抽出的known＋unknown樣本上fit二維嵌入。unknown只參與事後視覺化、不回饋偵測器；這張圖不是獨立holdout準確率。

## t-SNE怎麼建立

TSNE(random_state=seed,init="pca")，perplexity預設30，effective_perplexity=min(要求值,max(5,抽樣總數//4))；其他參數沿uv.lock固定sklearn。它最佳化高／低維鄰近分布的KL差異，沒有本專案另設神經網路epoch／loss或用test挑圖。資料極少時這個cap仍可能不小於總樣本而失敗；不補造點。

顏色表示配置，圓點known_correct、叉known_wrong、三角unknown。unknown配置若被正確拒絕也畫三角，**三角不是錯誤標記**。各子圖各自fit，座標、群距與方向不能跨圖比較，沒有物理單位或損傷意義。PolarMap用馬氏白化幾何，不是把t-SNE或PCA座標直接當嚴重度量尺。

## 怎麼操作

repo根目錄依[uv環境政策](../runtime_policy.md)準備資料：

```bash
uv run --locked python -m experiments.exp12_confusion_tsne --help
uv run --locked python -m experiments.exp12_confusion_tsne --data-root data --seed 42 --confidence 0.95 --perplexity 30 --tsne-max-per-class 200
```

API run(data_root,seed=42,confidence=0.95,perplexity=30,tsne_max_per_class=200)回傳矩陣及內部_tsne_by_dataset。max_per_class只降低圖的成本，不改混淆矩陣樣本。沒有Web執行卡、逐筆串流、取消或續跑，重新執行會重fit；缺配置／105欄／資料太少先核對來源，不能調出最好看的seed作研究成績。

## 看輸出

main經setup_run寫logs/exp12_confusion_tsne/{ts}.log、output/exp12_confusion_tsne/{ts}/environment.json、summary.json、confusion_matrices.png及tsne_grid.png。summary含labels／matrix原始數字；t-SNE座標**不落地**，只留圖。網格固定3×3，超過九工況時圖片只呈前九格，不能以圖確認完整coverage。

混淆矩陣行是真值、列是預測。healthy→fault是健康誤報；fault→healthy是漏報；known→unknown是過度拒絕；unknown→known是未拒絕。要算每類recall須除該行總數，空行為不適用，不假填100%。全域筆數不能當各motor等權平均。

預期圖能揭露錯誤來源，低分／重疊也照留；沒有「圖上分群漂亮」成功門檻。t-SNE群聚不證明高維泛化或排序嚴重度，不能用它支持部署、fresh final或RUL。完整舊數字與圖查[固定實測包](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/1fa9431bb7b86959f29540d07b2b9290ab39ce42/output/exp12_confusion_tsne/2026-10-09-14-27-55)，不人工另抄完整表。

## 方法來源與程式碼

van der Maaten與Hinton（2008），*Visualizing Data using t-SNE*，JMLR9,2579–2605，[原文](https://jmlr.org/papers/v9/vandermaaten08a.html)。perplexity30與配置標記是Lineage設定，不是原文對此資料的保證。混淆矩陣為計數工具；LW／legacy來源見[實驗十一](exp11_ancestor_comparison.md#來源與程式碼)。

[exp12](../../experiments/exp12_confusion_tsne.py)負責取樣／矩陣／嵌入／writer；[exp11](../../experiments/exp11_ancestor_comparison.py)供known協定；[core/monitor](../../core/monitor.py)fit與classify；[test_exp12_confusion_tsne](../../tests/test_exp12_confusion_tsne.py)檢查形狀／行和／有限嵌入，不能證明視覺推論正確。
