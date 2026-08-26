# Capstone Project — 馬達故障診斷與持續學習系統

**冷啟動 PHM（Cold-start Prognostics and Health Management）**：只用「健康」資料起步的馬達未知故障即時偵測、健康量尺自動擴張與持續學習。

---

## 研究動機

企業導入 PHM 系統時有一個雞生蛋問題：

> 故障診斷模型需要故障資料才能訓練，但設備在導入初期是新的、不會故障——
> **收集資料的階段，PHM 系統的產值等於零。**

本專題把這個順序反過來：**系統從第一天就只用健康資料建立基準**，之後的一切
（發現未知故障、為故障命名、擴張診斷能力、判別故障發生模式）都在運轉過程中自己長出來。

原始論文（見 [與 legacy 的關係](#與-legacy-的關係)）假設一開始就認識 5 類故障；
本專題問的是：**如果一開始只認識健康呢？**

### 核心構想

1. **單錨點量尺**：只要有健康分布，「樣本到健康分布的馬氏距離」本身就是健康度量尺——
   距離小 = 健康、慢慢變大 = 退化中、突然跳大 = 出事了。不需要等第一筆故障才有產值。
2. **星狀幾何**：在特徵空間中，健康群是中心，每種故障模式是一條射線——
   **距離 = 嚴重程度、方向 = 故障種類**。新異常「更遠」不代表「同一種病更嚴重」，
   可能是另一種病；因此用 HDBSCAN 對未知樣本分群來「發現新方向」。
3. **量尺隨確認擴張**：未知樣本累積成穩定叢集 → 操作員確認 → 納入已知類別、
   整組重新擬合 → 之後同種故障直接被認出（開放集 + 持續學習）。
4. **發生模式判別**：正常磨損是慢速漂移（8 顆螺絲 → 慢慢鬆），外力損傷是跳變
   （撞擊 → 8 顆直接變 4 顆）；監控異常密度的時間序列即可區分兩者。

### 系統成熟度三階段

```
階段 0（只有健康資料）：105 維特徵 + 單類馬氏距離   → 能報「異常了」（day-1 可用）
階段 1（第一種故障確認）：量尺有了第二個刻度         → 能報「哪一種、多接近」
階段 N（多種故障累積）：逐類馬氏 + 新方向發現        → 完整開放集診斷，持續擴張
```

---

## 三個實驗

三個實驗各自是獨立模組（`experiments/`），可單獨批次執行產出論文數據；
Web 即時展示（`web/`）呼叫同一份模組邏輯，兩邊數字一致。

### 實驗一：冷啟動偵測能力（`exp1_cold_start`）

**問題**：只用 8screws（Healthy）擬合健康基準，能多準地偵測九種從未見過的故障？

**方法**：Mahalanobis–Taguchi 式單類監測——RobustScaler + Ledoit–Wolf 收縮共變異數，
以獨立校準集（calibration split）的第 95 百分位距離為閾值，正規化分數 > 1 判為未知。

```bash
venv/bin/python -m experiments.exp1_cold_start --motor T1 --rpm 8000rpm
```

**實測結果**（T1/8000rpm，seed=42）：

| 注入配置 | 樣本數 | 偵測率 | AUROC | 分數中位數 |
|---|---:|---:|---:|---:|
| 8screws（健康保留集）| 64 | 10.9%（誤報）| — | 0.86 |
| 7screws | 322 | 100% | 1.0000 | 37.84 |
| 6screws | 314 | 100% | 1.0000 | 50.18 |
| 5screws | 212 | 100% | 1.0000 | 83.93 |
| 4screws | 287 | 100% | 1.0000 | 86.98 |
| 3screws | 241 | 100% | 1.0000 | 78.30 |
| 2screws | 288 | 100% | 1.0000 | 69.47 |
| 1screws | 349 | 100% | 1.0000 | 115.23 |
| 3_14screws | 351 | 100% | 1.0000 | 45.62 |
| 4_146screws | 372 | 100% | 1.0000 | 13.21 |

> 兩個值得寫進討論的觀察：① 健康誤報率 10.9% 高於名目值 5%，來源是校準集僅 62 筆的
> 有限樣本效應；② 分數中位數大致隨鬆動嚴重度上升（7→1 screws），支持「距離 ≈ 嚴重度」
> 的量尺假設，但 4_146（複合鬆動）距離明顯偏低——複合故障不在均勻鬆動的射線上。

### 實驗二：量尺擴張（`exp2_scale_growth`）

**問題**：未知故障陸續出現時，系統能否自動發現、命名並納入，同時保住既有能力？

**方法**：未知樣本進隔離區 → 累積 ≥ 25 筆後以 HDBSCAN（min_cluster_size=25,
min_samples=3）找穩定叢集 → 產生「候選新故障」→ 操作員確認（此時才揭示真實標籤，
偵測與分群全程不用標籤）→ 納入已知、整組重擬合。

```bash
venv/bin/python -m experiments.exp2_scale_growth --motor T1 --rpm 8000rpm
# 或指定注入順序：
venv/bin/python -m experiments.exp2_scale_growth --sequence 5screws 3_14screws 2screws
```

**實測結果**（依鬆動由輕到重全序列注入，T1/8000rpm，seed=42）：

| 注入配置 | 發現延遲（筆）| 叢集大小 | 純度 | 自類 holdout 準確率 | 健康保持率 | 已知類別數 |
|---|---:|---:|---:|---:|---:|---:|
| 7screws | 195 | 56 | 100% | 100% | 95.3% | 2 |
| 6screws | 595 | 307 | 100% | 100% | 93.8% | 3 |
| 5screws | 295 | 45 | 100% | 93.0% | 93.8% | 4 |
| 4screws | 365 | 72 | 100% | 96.6% | 92.2% | 5 |
| 3screws | 505 | 310 | 100% | 85.7% | 92.2% | 6 |
| 2screws | 215 | 132 | 100% | 84.7% | 93.8% | 7 |
| 1screws | 75 | 32 | 100% | 90.1% | 92.2% | 8 |
| 3_14screws | （自身階段 600 筆內未成叢）| — | — | — | — | — |
| 4_146screws 階段 | 25 | 600 | 100% | 85.9% | 90.6% | 9（學到的是累積的 3_14）|

> 三個發現：① 所有成功發現的叢集純度都是 100%——HDBSCAN 沒有把不同故障混成一群；
> ② 已知類別越多，逐類閾值越擠，自類準確率從 100% 緩降到 ~85%，是量尺擴張的代價；
> ③ 3_14（複合鬆動）在特徵空間過於發散，需累積遠超 25 筆才能成叢——複合故障的
> 「新方向發現」比單純鬆動難。

### 實驗三：漸進磨損 vs 突發事件判別（`exp3_trend`）

**問題**：能否從異常出現的「時間模式」判別故障是慢速磨損還是外力損傷？

**方法**：對開集分數做逐樣本旗標（>1 = 異常），以 EWMA 平滑成異常密度；
密度越過 0.5 觸發警報，同時回看警報前的軌跡，計算密度停留在「中間帶」[0.2, 0.5)
的時間——漸進退化會在中間帶徘徊很久，突發跳變只是快速穿過（≤ 12 筆判突發）。
另計 CUSUM（Page, 1954）作為偏移能量的展示統計量。

兩個劇本（`SCENARIOS`，Web 介面共用同一份定義）：

- **劇本 A（漸進磨損）**：健康 → 25% 混入 7screws → 70% → 6screws → 5screws
  （模擬螺絲逐漸鬆脫的早期間歇性症狀與惡化）
- **劇本 B（突發外力）**：健康 → 直接切換 4screws（模擬異物撞擊的狀態跳變）

```bash
venv/bin/python -m experiments.exp3_trend --motor T1 --rpm 8000rpm --trials 40
```

**實測結果**（40 次隨機重複，T1/8000rpm）：

| 劇本 | 警報率 | 判別正確率 | 平均警報延遲 | 平均中間帶停留 |
|---|---:|---:|---:|---:|
| A：漸進磨損 | 100% | 98% | 49.8 筆 | 37.9 筆 |
| B：突發外力 | 100% | 98% | 7.7 筆 | 6.7 筆 |

> 中間帶停留時間的兩個分布（B：5–13 筆、A：12–60 筆）僅在 12–14 有少量重疊，
> 98% 的判別正確率反映的是真實的分布交界，非參數硬湊。

---

## 即時展示介面（Web）

發表用的即時儀表板：把資料集當成「感測器串流」逐筆播放，現場演示三個實驗的完整劇情。

```bash
./run_web.sh                      # 預設 T1/8000rpm、http://localhost:8600
./run_web.sh --port 8600 --motor T1 --rpm 8000rpm --rate 4
```

功能：

- **開集分數串流圖**：每點一筆樣本，虛線 = 未知判定線（1.0），顏色 = 系統判定
  （綠 健康／藍 已知故障／紅 未知），事件以垂直色線標記
- **即時狀態卡**：實際注入（僅展示者可見）vs 系統判定、開集分數、健康度儀表
- **未知故障處理流程 stepper**：監測 → 異常隔離累積（n/25）→ HDBSCAN 分群 →
  操作員確認 → 擴張重訓，跟著真實狀態亮燈
- **候選卡**：叢集大小／純度／揭示真實身分，「✔ 操作員確認」一鍵納入重訓（亞秒完成）
- **健康量尺**：已知類別 chips，隨確認即時長大
- **變化點分析卡**：EWMA 異常密度、CUSUM、漸進／突發判別結果
- **PCA 特徵空間投影**：已知類別中心（✕）與最近樣本的即時散佈
- **控制**：注入來源下拉（十種螺絲配置）、劇本 A／B 一鍵播放、速率 1–10 筆/秒、
  資料集切換（九組 motor×rpm）、重置回階段 0

**發表演示腳本建議**：

```
1. 開場：階段 0，只認識健康 → 串流健康資料，分數貼地
2. 注入 5screws → 分數暴衝、判定「未知」、變化點警報
3. 隔離區累積到 25+ → HDBSCAN 候選出現 → 按「操作員確認」
4. 量尺擴張為 2 類 → 再注入 5screws → 系統直接認出（藍色）
5. 劇本 A 完整播放 → 警報判「漸進退化」
6. 重置 → 劇本 B → 警報判「突發事件」，對比收尾
```

---

## 目錄結構

```
Lineage/
├── core/                        # 共用零件
│   ├── data.py                  #   資料池載入、60/20/20 切分、循環抽樣
│   ├── mahalanobis.py           #   開集馬氏偵測器（複製自論文版程式碼，含來源註記）
│   ├── monitor.py               #   OpenSetMonitor：健康冷啟動 + add_class 量尺擴張
│   ├── trend.py                 #   TrendMonitor：EWMA 異常密度 + CUSUM + 漸進/突發判別
│   ├── logger.py                #   loguru 執行期日誌 + logs/ + output/ 慣例
│   └── runner.py                #   實驗 CLI 共用參數與 JSON 儲存
├── experiments/                 # 三個實驗：各自可獨立執行（python -m experiments.expN_*）
│   ├── exp1_cold_start.py       #   實驗一：冷啟動偵測能力
│   ├── exp2_scale_growth.py     #   實驗二：量尺擴張（含 ScaleGrowthSession 狀態機）
│   └── exp3_trend.py            #   實驗三：漸進 vs 突發（含 SCENARIOS 劇本定義）
├── web/                         # 即時展示（只做編排與視覺化，不含實驗邏輯）
│   ├── live.py                  #   LiveDemo：把三個實驗模組串成互動串流
│   ├── server.py                #   Tornado + WebSocket 伺服器
│   └── static/index.html        #   單檔儀表板（原生 JS，無外部依賴）
├── data/                        # 特徵資料（由論文版管線產出，本專案唯讀；git 忽略）
│   └── Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv
├── logs/                        # 每次執行的 loguru 日誌（納入版控）
├── output/                      # 每次執行的結果檔與圖表（納入版控）
├── run_web.sh                   # 啟動展示伺服器
├── build_uv.sh / build_uv_mac.sh# 建立 venv（--legacy 可加裝論文版管線依賴）
└── pyproject.toml               # 依賴定義（Python 3.10.19）
```

---

## 環境與執行

```bash
./build_uv.sh              # 建立 venv 並安裝本專案依賴（無 TensorFlow、不需 GPU）
./build_uv.sh --legacy     # 需要重跑論文版管線（Ancestor）時使用（加裝 TF/CUDA、Jupyter 等）
```

所有指令都在**專案根目錄**執行，直接用 `venv/bin/python`，不需 activate：

```bash
venv/bin/python -m experiments.exp1_cold_start --motor T1 --rpm 8000rpm
venv/bin/python -m experiments.exp2_scale_growth
venv/bin/python -m experiments.exp3_trend --trials 40
./run_web.sh
```

### 日誌與輸出慣例（沿用論文版專案習慣，改以 loguru 實作）

每次執行自動建立、以程式名與時間戳隔離，皆納入版控：

```
logs/{program}/{YYYY-MM-DD-HH-MM-SS}.log      # 完整執行日誌
output/{program}/{YYYY-MM-DD-HH-MM-SS}/       # results.csv / summary.json / *.png
```

---

## 資料集

沿用學長論文的實驗資料：以**拆除馬達固定螺絲**模擬不同程度的機械鬆動故障，
感測三軸振動、電流與溫差，每筆樣本為 1 秒訊號（10 kHz）萃取的 **105 維特徵向量**
（15 統計量 × 5 通道 + 三軸各 10 個轉頻諧波能量；由論文版 Step 1–2 管線產出）。

| 螺絲配置 | 本專題角色 |
|---|---|
| 8screws | **健康基準**（唯一的初始已知）|
| 7 → 1 screws | 未知故障（鬆動由輕到重，天然的嚴重度階梯）|
| 3_14 / 4_146 screws | 未知故障（複合不均勻鬆動，「不同方向」的壞法）|

本專案只讀 `*_Group_feature_data_clean.csv`（逐列 IQR scale=1.5 過濾版，
與論文 Step 4/5 相同輸入）。已知類別以 60/20/20 切為訓練／校準／保留集；
校準集只用已知資料決定閾值，未知資料絕不參與擬合。

---

## 方法與引用文獻

| 模組 / 環節 | 方法 | 主要文獻 |
|---|---|---|
| PHM 總體框架 | 條件監測 → 診斷 → 預後的分層流程 | ISO 13374；Jardine, Lin & Banjevic (2006) *MSSP*；Lee et al. (2014) *MSSP*；Lei et al. (2018) *MSSP* |
| 階段 0 健康基準 | 健康分布 + 馬氏距離的單類監測 | Taguchi & Jugulum (2002) *The Mahalanobis–Taguchi Strategy*；綜述：Pimentel et al. (2014) *Signal Processing*；對照法：Schölkopf et al. (2001) OC-SVM、Tax & Duin (2004) SVDD |
| 開集判定 | 逐類高斯 + 馬氏距離、校準分位數閾值 | 學長論文（本資料集與基礎流程）；K. Lee et al. (2018) *NeurIPS*（深度特徵逐類馬氏）；開集理論：Scheirer et al. (2013) *TPAMI*、Bendale & Boult (2016) *CVPR* OpenMax |
| 共變異數估計 | Ledoit–Wolf 收縮（高維小樣本可逆、良態）| Ledoit & Wolf (2004) *J. Multivariate Analysis*；替代：Chen et al. (2010) OAS |
| 新故障分群 | HDBSCAN（自動叢集數、雜訊點標記）| Campello, Moulavi & Sander (2013) |
| 變化點偵測 | EWMA 管制圖 + CUSUM | Roberts (1959) *Technometrics*；Page (1954) *Biometrika* |
| 持續學習 | 全資料重擬合（= 完整 rehearsal，迴避災難性遺忘）| Kirkpatrick et al. (2017) *PNAS* EWC；Rebuffi et al. (2017) *CVPR* iCaRL |
| 衰退外插（未來工作）| 退化軌跡模板比對、隨機退化過程 | Gebraeel et al. (2005) *IIE Trans.*；Wang et al. (2008) *PHM Conf.*；Ye & Xie (2015) |

---

## 與 legacy 的關係

論文版程式碼（Step 1–6 管線、128 個 notebook、scripts、docs、執行紀錄與論文全文）
已整批移回 [Ancestor](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor)
repo 保存——issue 討論串（#1–#60，缺陷成因與修正驗證）也在該處；
本 repo 的 git 歷史仍完整保留搬移前的所有版本，可隨時回溯。

- 本專案**繼承**：資料集與 105 維特徵工程（直接讀論文版管線產出的 clean CSV）、
  逐類 Ledoit–Wolf 馬氏開集偵測器（Ancestor `docs/Mahalanobis_Improvement.md` 的採用結論）、
  HDBSCAN 參數、logs/output 慣例。
- 本專案**翻轉**：起點從「已知 5 類」改為「只知健康」；HDBSCAN 從「判定器」
  改為「新方向發現器」；判定粒度從叢集改為逐樣本。
- **規範**：新程式碼一律不依賴論文版程式碼——需要的零件以「複製 + 來源註記」帶入
  （見 `core/mahalanobis.py` 檔頭）。

---

## 限制與未來工作

1. **螺絲數是離散的故障代理**：真實磨損是連續過程，量尺結論外推需保留。
2. **「前期資料保證健康」的實務前提**：需要 burn-in 期；不同轉速的健康基準需分開建
   （本專案依 motor×rpm 分資料集正是為此）。
3. **健康誤報率受校準集大小影響**（實測 10.9% vs 名目 5%）：可用更多健康資料或
   conformal 校準改善。
4. **複合故障（3_14/4_146）發散難成叢**：新方向發現對非均勻故障需要更長累積或
   自適應的 min_cluster_size。
5. **衰退曲線外插未實作**：T1/T2/T3 三個壽命期資料可作為 run-to-failure 模板
   （similarity-based prognostics），為下一步方向。
6. **單一測試台、單一故障機制**：結論外推到其他 PHM 任務需再驗證。
