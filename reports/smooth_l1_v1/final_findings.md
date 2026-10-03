# 實驗16：平滑L1配對結果與失敗分析

2026-10-03，Asia/Taipei。108格實際完成、0缺失，全部重推與指標重算通過；12種方法皆FAILED，尚未找到通過完整可靠提升契約的方法。production正式105／linear／LW、k-NN factory選項與PolarMap均未改。

## 實測範圍

90CSV、28,910 unique rows／105維，fingerprint維持`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。12分類器×3motor folds×seeds0/1/2=108格，1,040,760 prediction records，重推不是新增獨立試驗。9個models bundles包含108分類器；108皆成功收斂，最高550iterations。每格含三RPM，唯一test motor計數仍3，未增加採集session。

| fold | train | calibration | test | test rows |
|---|---|---|---|---:|
| 0 | T1 | T2 | T3 | 9,294 |
| 1 | T2 | T3 | T1 | 9,759 |
| 2 | T3 | T1 | T2 | 9,857 |

known為healthy=8screws及1screws／2screws／3_14screws／3screws／4screws；unknown為4_146screws／5screws／6screws／7screws。validation／selection空，cal只既有known閾值，無共同winner。所有rows有歷史test曝光；這次事前lock不消除歷史選擇偏差。原window／session／刪點／安裝來源UNKNOWN，fresh guard INCOMPLETE。

## 全方法與基線

下表分類、完整健康誤報與unknown為seed0三motor平均；conditional F1僅true known faulty，不能代替包含healthy／unknown錯分的完整final F1。fault acc三欄保留全部seeds，不挑最好seed。H01–H12的unknown branch固定C02/M，均18.437%；T1均0%。歷史C24/M的unknown為21.071%，不混成相同pipeline。原始classifier accuracy未把reject混入分母。

| 方法 | 幾何／距離／更新 | known acc% | fault acc% seed0／1／2 | conditional F1 | healthy total% |
|---|---|---:|---|---:|---:|
| C02/M | vibration75歷史控制 | 34.153 | 26.613／26.613／26.613 | .240401 | 26.870 |
| D01 | C17 classifier＋C02/M | 39.286 | 30.431／30.431／30.431 | .285191 | 14.126 |
| C24/M | 原完整pipeline | 32.168 | 30.909／30.909／30.909 | .286643 | 63.407 |
| H01 | identity／Q／static | 34.284 | 29.909／29.909／29.909 | .267139 | 42.529 |
| H02 | identity／Q／GLVQ | 35.986 | 27.028／30.579／30.913 | .232251 | 16.958 |
| H03 | identity／Q／anchor | 37.416 | 28.847／31.781／32.425 | .247166 | 17.599 |
| H04 | identity／S／static | 33.933 | 29.502／29.502／29.502 | .261913 | 42.598 |
| H05 | identity／S／GLVQ | 36.500 | 27.836／29.877／34.099 | .243121 | 18.015 |
| H06 | identity／S／anchor | 36.499 | 27.951／32.293／33.215 | .243162 | 18.645 |
| H07 | metric／Q／static | 37.490 | 31.224／32.902／31.676 | .246308 | 30.233 |
| H08 | metric／Q／GLVQ | 36.671 | 26.214／27.929／23.963 | .219031 | 8.924 |
| H09 | metric／Q／anchor | 38.101 | 27.932／25.592／33.563 | .241128 | 8.924 |
| H10 | metric／S／static | 35.666 | 29.261／32.863／29.862 | .239295 | 31.433 |
| H11 | metric／S／GLVQ | 35.329 | 24.972／25.479／29.253 | .216885 | 10.843 |
| H12 | metric／S／anchor | 35.160 | 24.756／25.539／29.288 | .215744 | 10.768 |

H07比匹配G13的fault acc三seed差值為+5.720／+1.591／−5.434百分點：距離更換的效果受train-only metric子集／seed影響，不能只報seed0提升。相對較強D01，H07 seed0僅+0.793百分點，conditional F1下降.038883，完整健康誤報增加16.107百分點，未達契約。

H05 seed2的fault acc34.099%是局部值；seed0只有27.836%，沒有共同選winner。H08/H09三motor平均健康8.924%看似低於10%，但T2／11000rpm健康完整誤報100%，不能用平均掩蓋最差組。H02最差RPM為90.909%，其餘大多100%。全部12方法最差motor/class recall=0、T1 unknown recall=0；拒絕branch未改，因此沒有未知排序的新收益。

完整final fault F1（seed0 pooled全28,910 rows，五個known faults）：H01–H12依序.220618／.171510／.176589／.218148／.171787／.167542／.209999／.157306／.177393／.194411／.156830／.157391；D01=.220229。分母含healthy與unknown錯分，與conditional F1不同；完整motor/seed、RPM、class、confusion與AUROC/AUPR均在封存summary，不只保存平均。

## 機制與結論分級

VERIFIED：Q/S公式及解析梯度、source SHA／actual train-cal重建、108格逐樣本reinfer、truth mutation、756組方法/fold/seed配對與saved metrics重算。unknown不fit/cal/select，正式資料前後SHA相同。

FAILED：12方法完整主screen全部失敗；平滑L1降低平方距離對大偏差的權重，確實改變分類邊界，但沒有證據支持跨motor可靠改善。anchor僅限制prototype位移，未保護所有類別或健康最差工況。H07在T1的fault acc41.222%與healthy誤報0%不能外推至T2：T2 fault32.082%、healthy60%，2screws仍零召回；T3 fault20.369%、healthy30.700%。這是資料內描述，不是motor/老化因果推論。

UNKNOWN／INCOMPLETE：來源群組／時間／刪點與physical fault mechanism仍未知，未見fresh test；目前只一known subset，沒有R2多subset與壓力證明。T1/T2/T3不同個體不能串成生命週期；不能給RUL、退化百分比或每小時誤報。

下一批已於看本批outer結果前先行提交exp17手冊：工況相關原型，從RPM對原型的影響研究classification，不再只換距離。它仍固定C02拒絕，不預期單獨解決T1未知零召回；未知判別／校準是後續另一個機制問題。沒有因本批失敗降低CONTRACT或改production。

## 文獻與改編位置

Lange／Zühlke／Holz／Villmann，ESANN2014:271–276，*Applications of lp-Norms and their Smooth Approximations for Gradient Based Learning Vector Quantization*，[原始六頁PDF](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-153.pdf)：使用Eq.11–13的Q/S與α20，保留Q非零對角常數；本站固定幾何、mean初始化、單中心GLVQ、批次optimizer與anchor，沒有復現原GMLVQ或移植其數據成績。

Sato／Yamada，NIPS8:423–429，1995會議／1996卷出版，*Generalized Learning Vector Quantization*，[原始PDF](https://proceedings.neurips.cc/paper_files/paper/1995/file/9c3b1830513cc3b8fc4b76635d32e692-Paper.pdf)：本站固定平均sigmoid(4mu)、epsilon、L-BFGS-B與anchor。原式、改式、參數與反證詳見exp16手冊，code為`core/fault_type_smooth_l1.py`及`experiments/fault_type_smooth_l1.py`；正式factory無改編。

## 老師建議與交付

| 建議 | 本批完成度 | 證據／限制 |
|---|---|---|
| healthy＋5known／4unknown | 主配置完成 | 108格；9配置均有標籤與三RPM。不是9種獨立物理故障原因 |
| 隨機N／N5全部126組 | 本批未重跑；歷史已完成 | 保留原研究索引，不由runner支援宣稱新實驗完成 |
| 切分依據／用途洩漏 | 固定用途已驗證 | documented跨motor三折、unknown禁止fit、選參空、專用cal |
| 來源與獨立final test | 未完成 | 原視窗/session UNKNOWN、每類test groups不足、全資料歷史曝光；標準不降低 |
| 可信fault type與unknown | 部分完成 | 能公平重算，仍有零召回與健康最差組失敗，沒有可靠模型完成 |

H工程驗收為兩環境各472項完整通過；後續加入exp17核心時另各483項通過，不能回填H事前驗收。最新含exp17 runner/source用途測試的雙環境各492項通過，0失敗；pip check與37既有CLI exit0，exp16／17的help/smoke另記。

D資料包6ZIP／252members，整檔SHA、CRC、member SHA皆PASS，未刪資料；不是離機備份。完整結果、models、predictions在`D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/smooth_l1_v1/`；Git追蹤精簡GZIP、lock、來源驗證、備份索引與本報告。精確路徑、file SHA與semantic seal見result_index.json及execution_log.md。
