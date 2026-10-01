# 驗證層級與老師建議對照

本輪任何更高分都不能解除下列來源限制。工程VERIFIED和模型泛化可靠性是不同驗收。

馬達身分依據為固定commit的[Experiments_Guide L218](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/afcfcc419dab3103a86a8f95601d3af85890eb38/docs/Experiments_Guide.md#L218)及[L230–231](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/afcfcc419dab3103a86a8f95601d3af85890eb38/docs/Experiments_Guide.md#L230-L231)；文件支持個體代碼，不代替serial／獨立錄製／原始視窗來源链。

| 項目 | 判定／依據 |
|---|---|
| T1/T2/T3身分 | 固定版本Experiments_Guide支持三顆不同馬達，T1新、T2/T3老；可稱documented motor IDs，不是完全沒有身分依據 |
| 使用時數／序號／老化真值 | UNKNOWN；不能串成一顆馬達的生命週期，不能計RUL、損壞百分比或分离個體與老化效應 |
| train/cal/test角色 | 已固定三方向不同馬達；未知配置在開發兩顆馬達標unused，沒有進fit/cal |
| 共同selector依賴 | 已用none selection、空validation/selection IDs排除；跨折同樣本角色輪換本身不是global selector洩漏 |
| 校準與選參共用 | 本協定沒有選參，cal專用；不是造出第四顆獨立馬達，也不將舊shared-valcal結果改寫為無偏 |
| 原始recording/session/run／視窗邊界 | UNKNOWN；file/numeric duplicate查無重複不代表原始視窗獨立 |
| 時間、sample rate、stride、刪點mask、單位、安装、負載 | UNKNOWN；程式中的10,000Hz與RPM設定不能證明每次實際採集一致；不報每小時誤報或警報延遲 |
| 已處理105維 | 正式90CSV／28,910rows唯讀，fingerprint不變；train中公式冗餘可驗證，但物理尺度／跨階段設備一致性沒有因此被證明 |
| test groups數量 | 每fold一顆documented test motor，仍不符合歷史每類至少兩個test groups；INCOMPLETE，不降低門檻 |
| fresh final test | 全28,910rows已有歷史test曝光，換seed／檔名／備份不能變盲測；本輪固定候選亦由歷史問題導出，維持探索性 |
| Conformal可交換性 | 跨馬達分布與視窗依賴未證明，不保證5%健康誤報率或unknown recall |
| seed與統計 | 三seed只是演算法敏感度；三motor等權描述性平均／範圍，不報逐窗IID CI或以重複runs充當更多受試 |

## 老師問題1：healthy＋部分known faulty預測保留unknown

程式與主要N5實驗配置已落實：healthy=8screws；known faulty=1screws/2screws/3screws/3_14screws/4screws；unknown=4_146screws/5screws/6screws/7screws。本輪新增198評估只用這一組sealed class manifest。既有126組N5、N1–8 sweep及N9 closed-set歷史研究保留；本輪未重跑，不由runner支援宣稱完成新全量研究。

「可信fault type」僅部分完成：可驗證的是故障配置分類／未知配置拒絕，九種faulty label主要是同一鬆動機制的數量／位置配置，不是九種獨立確認物理原因。模型是否辨識成功依完整評估及最差motor/RPM／逐類結果判定，不因程式可跑就宣稱可靠。其他N已有歷史實驗，不等於本輪所有候選已在其他N驗證。

## 老師問題2：切分依循與何謂不完整

切分依循文件支持的不同motor，加同RPM routing作工況控制。程式用途與selector/calibration角色問題可修正；「不完整」仍包含：獨立test motor/session不足、原始採集與window來源未知、歷史曝光，以及需要按實際資料列出的class/RPM coverage缺格。本輪不靠重新洗牌或改metadata字句取得PASS。

因此：**切分規則與軟體驗證已完成，獨立來源資格／廣泛泛化仍部分完成或UNKNOWN**。目前只有現有馬達資料；不以不存在的硬體／重採作本輪必要條件。能支持的是現有三顆馬達資料下的受控跨馬達比較，不是廣泛部署、真实退化生命周期或故障確診。
