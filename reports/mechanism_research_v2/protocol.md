# 已鎖定的單輪協定（評估前提交）

**目前執行版**：`output/fault_type_mechanism_registry/2026-10-02-17-49-29/protocol.json`，seal `ff6ddc29ca101f73c8a3ca6f818147dc4f6cd81032581966757b5f72087e1b91`。
僅修正resume總索引immutable保存，九arm公式/參數/角色/預算均未變。13:10版與17:46 pre-evaluation lock保留但不作正式新評估入口；沒有舊outer結果需要重跑。
新35相關測試（19 mechanisms）、另3 report cases PASS；最後完整acceptance會重新計數。

`mechanisms_v2_fixed_no_selection`，9 complete arms、81格，沒有selector或global winner。
seal `4db05bc722e49ecb6421beaa072f21216ab795d8b180c3fcb441d0d7fe230743`。
檔案 `output/fault_type_mechanism_registry/2026-10-02-13-10-15/protocol.json`。
來源HEAD b55a5b913d831dcbded263328d4771672c10764e＋逐檔實作SHA；fit lock另記實際commit。
資料指紋 `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。
原parent protocol bf98e897a1d984a8e72e521cb184636f3d1e2df6cd377b071ee2a1d99670f4ba；parent lock 48ba96ab8c3eb8b2a4a25e8a17a95b5083e2e6f6318aba6bdd6e08b1b9be44da。

| fold | train（fit所有零件） | cal（known固定門檻） | test（sealed後評估） |
|---|---|---|---|
| fixed-fold0 | T1 | T2 | T3 |
| fixed-fold1 | T2 | T3 | T1 |
| fixed-fold2 | T3 | T1 | T2 |

known：8screws healthy；1screws、2screws、3_14screws、3screws、4screws。
unknown：4_146screws、5screws、6screws、7screws。非九種確認物理故障原因。
未使用的開發馬達unknown保持unused；validation/selection=[]；cal僅門檻，沒有第四顆motor。
九工況=三motor×6000/8000/11000rpm。seed0/1/2不改角色；決定論版本如同分照報。
pipeline、fixed參數、parent scaler/classifier/factory設定實值全列 protocol；P/G公式見 adaptation cards。

健康total alarm 每格≤10%只是暫定研究安全篩選；若失敗不靠改門檻修飾。
先列安全、worst class/unknown，再trade-off；不以test挑部署winner。
對照重用metric v2中C02/C17/C24/C18/R18，paired IDs須相同；舊法不是本輪新fit。

工程測試：34個新增cases涵蓋checkpoint/SHA/小樣本/手算/端點/未知邊界；兩runtime全套各344 PASS、pip check PASS、27 CLI help PASS。
synthetic smoke兩runtime各9arms，NOT research、不跨sklearn載舊joblib。
科學環境Python3.10.19/sklearn1.7.2；兼容Python3.14.6只工程測試。
每bundle fit checkpoint、每method/fold/seed prediction checkpoint，明確action目錄resume且config/SHA一致；已seal檔不覆寫。
peak memory為程序累計peak（包含parent models），不是每arm額外RAM；共享推論時間不可當9次獨立timing。

限制不變：全部28910樣本已有test曝光，acquisition/raw/window/unit未知，每類test independent groups不足，final guard INCOMPLETE。不能因新lock恢復盲測或5%保證。
