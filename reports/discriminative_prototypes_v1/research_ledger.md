# 實驗15來源、假說與接續紀錄

2026-10-03，Asia/Taipei。最新研究HEAD／remote `11a548d77cf2a2e58f7ca56098a5633422b24a47`；exp13交付 `0cd05288a204da39a4aac64cd89b91efaf7a481f`。AGENT main blob仍 `8f35a6bf14fa4747d63add1d6bc852b65bcb4784`。282個無關刪除保留。exp15先前未使用，本手冊先於新程式。正式105/LW/PolarMap未改；只有有限候選，不假造最佳演算法。

已完成global ledger入口：`reports/metric_classification_v1/result_index.json`、`reports/local_fisher_v1/result_index.json`；其父研究與未測方法沿舊帳冊。exp13108格全完成、12方法契約FAILED；exp14 144格全完成、16方法FAILED。exp14PCA10/5NN fault accuracy seed0為33.420%、C17為30.431%，healthy完整誤報18.947%，不是可靠通過。所有結果28910unique rows，多records不增加motor數。

## 本批搜尋與閱讀

| query／語言 | 原始來源／範圍 | 篩選 |
|---|---|---|
| 英文 `Sato Yamada A Generalized Learning Vector Quantization Algorithm 1995 original paper PDF` | NIPS1995原文七頁、公式圖片 | 實作相對距離原型loss；年份1995會議／1996卷去重 |
| 日文 `site.ieice.org 佐藤敦 一般化学習ベクトル量子化` | NEC原作者書目，IEICE部分頁cache miss | 原文方法交叉核對；不假裝取得1999全文 |
| 德文 `Generalisierte Lernende Vektorquantisierung Original Sato Yamada` | 重複回到GLVQ原文及無關資料 | 去重，不湊新方法數 |
| 英文 `site.esann.org GLVQ regularization prototypes` | ESANN2021 AGLVQ全文method／資料／結果／限制 | 找到context、代表性與collapse反例；不是本批anchor來源 |
| 英文 `site.hammer-lab.techfak.uni-bielefeld.de GLVQ rejection robustness` | 作者出版清單／拒絕研究線索 | 待精讀；不由清單冒稱方法已實測 |
| 英文 `Hammer Villmann Generalized relevance learning vector quantization 2002 original author paper` | 原作者書目／PubMed摘要、DOI10.1016/S0893-6080(02)00079-5 | GRLVQ全文尚未取得，未實作其relevance更新 |

查詢日期2026-10-03，可靠總命中數UNKNOWN；只有上述閱讀範圍，未窮盡語言×主題。各來源、公式、限制、code mapping及改編見exp15手冊。GLVQ不取用outer真值，推論最近原型另一類的margin不需true label。本站不使用context適配／target features；後續context候選需新protocol。

## 工具與相容性

SciPy minimize只用現有版本：原型變數是有限6或18×69陣列，解析梯度，無GPU。sklearn-lvq1.1.0官方模組BSD3僅閱讀，不安裝／不複製。作者AGLVQ repo MIT、README Python3.6／Keras2.3.1／TF2.1，與目前環境不直接相容；未讀完整setup／未執行，因此暫不安裝。作者2002relevance與2021context各有新機制但本批不冒稱重現。

compatibility：formal105→封存harmonic69(train)→identity／hard600(train subset)→static／GLVQ原型(train初始化與子集loss)→closest class；拒絕支線C02/M或predicted-class relative margin→known calibration95%→fixed decision。label與motor code不作數值輸入，calibration只定門檻。每個支線保存實際IDs及sourceSHA，未知不fit／cal。

## 驚訝結果與反證 queue

exp13 hard600九份已收斂卻分類弱；static mean的seed2偶有高值但seed0弱。exp14局部Fisher比PCA的跨motor平均更差；降低T1健康誤報時fault recall亦減少。支持下一步檢驗判別邊界原型移動，不能宣稱GLVQ一定修復。H15a/b/c及配對static、λ0、λ.01、1／3中心、identity／metric事前固定。原型高confidence遠端未知是競爭解釋；模糊拒絕支線屬低支持探索，占一半detector支線但不作主候選保證。

stage=manual_before_implementation；pending=core／unit／synthetic／protocol commit／fit／source verify commit／216評估／verify／report／backup。raw/session/window／fresh缺口UNKNOWN／INCOMPLETE，不阻擋現有合法方法。
