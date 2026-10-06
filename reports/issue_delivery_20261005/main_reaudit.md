# 最新 main 的17項唯讀重驗

基線64cb71d84663e1745ec54db74abad68def67e8e6；原發現及R1–R10讀自80bdf54fdf43d466ea19549fb7c0b4e391394799。不是對研究分支新guard的重驗。原CSV的ARCH-002／TEST-002列部分欄位移位，保留原JSON；判讀Evidence及實際程式，不直接繼承錯位欄位。

來源檔SHA、每個函數行範圍與合成fixture結果見output/fault_type_issue_triage/2026-10-06-18-34-48/main_review.json。CLI抽取已讀main函數，不import未合併研究修補；正式data與models都沒讀寫。fixture只有工程反例，沒有模型成績。

| ID | 原／目前位置及固定main行 | 判定 | 本輪查證／界線 | 分工 |
|---|---|---|---|---|
| EXP-002 | exp6_matrix.py _is_complete 77–100 | 仍成立 | 缺results.csv及run.log，只有合法summary仍回True；不是正式run遺失宣稱 | R1 |
| DATA-001 | core/data.py discover54–65、load68–88 | 仍成立 | 僅healthy、任意欄名105維fixture仍載入；沒有exact CONFIGS／FEATURE_NAMES檢查 | R2 |
| DATA-002 | formal_data _convert_condition314–393 | 仍成立 | min(widths)仍截短；stub fixture通道2／3窗成功取2，manifest沒有原寬度／截斷欄 | R3 |
| DATA-003 | 原exp6_osr→目前exp6_formal_benchmark.py 68–92 | 仍成立 | 無manifest時same size／mtime的A→B不同bytes仍同fingerprint；新main已拆正式／廣度比較，不能查錯檔 | R4 |
| DATA-004 | core/formal_data.py materialize433–480，465–466 | 仍成立 | shared manifest仍str(source)／str(output) absolute；本輪只讀欄位，不重新materialize正式資料 | R4 |
| SEC-003 | core/formal_data.py314–393 | 仍成立，原越界程度部分未確認 | 任意config '..'被接受，stub寫入離開RPM子目錄；這個反例仍在output_root內，不能宣稱所有root逃逸已證實 | R3 |
| REPRO-001 | exp1 main120–154、exp2 283–322、exp3 146–177 | 仍成立 | 保存dataset／seed等，未統一fingerprint、commit、packages；PR36會改exp1／3，不接手 | R4 |
| ARCH-001 | core/runner18–59；formal exp6 main300–331 | 仍成立 | 共用dataset／openset參數與另一套formal parser、schema2並存，無共用resolved-config物件；預設相同不等於契約統一 | R7 |
| ARCH-002 | formal exp6 run147–277、matrix110–219、LiveDemo.tick197–286 | 仍成立，維護議題 | 131／110／90行多責任函數；未證明數值bug，先契約後抽helper，PR36同Web範圍 | R10 |
| TEST-002 | main tests16模組；tests/test_web_experiments.py | 部分已修，仍有缺口 | Web catalog／參數／序列化已有tests；無直接loader、WS Origin／dispatch及exp1–3輸出全契約；PR36新增iter_run未合併 | R5／#27 |
| AGG-001 | aggregate_exp6.py load56–100、aggregate103–163 | 仍成立 | summary fingerprint=fixture，manifest首筆=TAMPERED仍發布TAMPERED；沒有CSV／log檢查 | R1 |
| REPRO-002 | 原exp6_osr→formal exp6 return247–277 | 仍成立 | 已有schema2、commit／Python／config，不含packages、OS／hardware完整metadata | R4 |
| SEC-002 | web/server.py98、173、206、251 | 仍成立 | 直接broadcast／HTTP回exc!r，沒有client脫敏；只讀程式，不對外送攻擊 | R6／#28 |
| PERF-001 | data68–88、runner51–59、web/live.py | 結構仍成立，影響證據不足 | 仍read_csv／concat且無指紋cache；本輪沒有walltime／memory profiling，不宣稱主要瓶頸 | R8 |
| PERF-002 | core/openset.py108–110及逐類score | 結構仍成立，影響證據不足 | 每類kneighbors仍存在；舊0.013440／0.006262秒不當新main測量或必須優化證據 | R8 |
| DOC-001 | docs/README.md1–65 | 現行索引已修，歷史相對連結仍限 | 新／舊架構與固定歷史明列；30個本機相對連結目標在固定main皆存在，只核檔案，不核段落錨點或全部歷史內文連結 | R9 |
| DX-001 | README／build_uv.sh1–29／run_web.sh | 仍成立，部分文件已有PS | 主安裝與啟動仍POSIX、venv/bin；health手冊PS不等於全流程Windows驗收；沒有執行rm命令 | R9／#26 |

## 不能由此推論的事

沒有以研究分支已補SHA／aliases宣稱main問題已修；沒有把未合併PR36的82 tests當main新結果。本輪有兩個Python的合成CLI檢查，不是重跑main全部測試或2490研究。

SEC-003要保留安全檢查需求，但單一'..'只離開工況子目錄，不足證明越過root；將原高風險主張細分，後續要測drive／UNC／absolute／深層路徑而不寫正式資料。PERF只有結構，真正瓶頸需另profiling。維護／效能問題不稱模型效度已失敗。

#30第一項已逐項核對；R1–R10只交草稿，不批次開程式issues。研究分支沒有main新增的docs/health_and_reports.md，不複製全檔造成其他相對連結失效；提供§2.2插入文字patch，尚未直接修改main。第二、三項未完成，#30保持OPEN。

Python3.10.19與3.14.6分別完成18-37-06／18-37-13的CLI合成檢查，兩份來源SHA、函數行號、連結目標與反例結果一致；路徑字串隨run目錄不同。正式資料讀取0、模型fit0。18-34-48另保存GitHub全分頁盤點與完成收據。全部結果以各自log及JSON為準。
