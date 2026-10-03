# RPM原型拒絕：來源卡與閱讀邊界

2026-10-03，Asia/Taipei。這批沿用已讀原始來源，沒有把重讀文章或增加參數版本計成新的論文家族。

Fischer／Hammer／Wersing（2015），Neurocomputing169:334–342，*Efficient Rejection Strategies for Prototype-based Classification*，DOI10.1016/j.neucom.2014.10.092，[作者合法稿](https://www.honda-ri.de/pubs/pdf/2814.pdf)。先前已讀25頁全文、渲染Eq.8查核；本次再次開啟原稿Eq.7／9／10–11，讀到outlier／ambiguity與原Comb的窮舉threshold。2014會議稿與2015延伸已去重。原文ARC是accepted subset accuracy/coverage，不是本站完整unknown與安全成績，不能移植headline accuracy。

本站取nearest squared distance與1−RelSim（epsilon保護），加入既有RPM工況原型，以known-cal固定q95而非原Comb threshold grid；本站OR用RelSim＋nearest-distance，不用Eq.8 Dist，避免把印刷公式與幾何距離混稱。q95、linear interpolation、normalized signed excess及零threshold是本案操作約定。不是原作者Comb完整重現。公式／手算／ties／q0／overflow測試可直接反駁實作。

Graeber等（2021），ESANN557–562，DOI10.14428/esann/2021.ES2021-40，[全文](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)及MIT作者code的閱讀與改編界線繼承reports/context_prototypes_v1/sources.md。分類器一律引用I01–12已封存版本，不看I成績挑較好的degree／seed／geometry，不新增分類器fit。

本批沒有執行作者程式、安裝新工具／依賴或上傳資料。英文期刊與德國研究單位原稿可取得；本批沒有新增可用日文原始拒絕方法，語言coverage限制保留。這不是對全語言、全故障診斷文獻的窮盡結論。後續原始paper／適配工具queue仍需逐篇核對方法與資料前提。
