來源：main/TODO.md（原建立commit5627ee6），工作分支 research-improvements-20260920；來源獨立性缺口見 #9。Codex執行；2026-10-02開始、10-03交付。

- [x] 完成 #11 分支總覽與同步raw schema說明，issue已關閉。
- [x] 補寫continuous手冊，後續新solver與report也先寫手冊、附原始出處、公式差異及CLI，再改碼。
- [x] 核對Q01–Q08：72planned/60completed/12INCOMPLETE；保留未收斂格。
- [x] 576,144筆重推論、source/model/prediction SHA與指標重算；相同IDs配對C02/C17/C24/D01。六完整方法均FAILED可靠性門檻；Q02/Q04 INCOMPLETE。
- [x] 雙Python最後各396tests、37CLI、pip check PASS；Q8ZIP/233members及solver9ZIP/190members SHA/CRC PASS，逐階段commit/push。
- [x] 依solver失敗證據登錄有限train-only改編：hard150、smooth150、hard600共27fits；收斂3/9、5/9、9/9。27loss/gradient重算，原Q三成功權重exact match。
- [ ] 下一批hard600 subset/all-train kNN完整outer pipeline配對比較：尚未實作/執行；不能把訓練收斂當準確率提升。持續研究issue維持OPEN。

Q07 known accuracy39.82%、fault accuracy33.92%、unknown recall8.71%、健康總誤報29.14%（seed0三motor等權）；相對C24 fault accuracy+3.01百分點，健康與未知tradeoff仍失敗。T1 unknown recall24.71%伴健康總誤報64.98%，T2 unknown0%；不選部署winner。

原來源：Weinberger與Saul（2009,JMLR）LMNN啟發本地diagonal/mean/ridge；Rennie與Srebro（2005,ICML）§3.3 Eq9 shifted generalized logistic只改scalar損失；hard600只增加optimizer預算，不是新發明演算法。

結果/來源/重現：
- reports/continuous_research/final_findings.md、result_index.json、reproduction.md。
- reports/continuous_research/solver_findings.md、solver_result_index.json、execution_log.md。
- docs/experiments/fault_type_solver_diagnosis.md、fault_type_solver_report.md。

formal105/linear/Mahalanobis-LW/PolarMap default保留，kNN factory可切換。舊28,910rows均歷史曝光；raw/session/window來源仍UNKNOWN，fresh final與每類兩個獨立test groups INCOMPLETE，不降低門檻、不填假證據。沒有模型可靠完成或廣泛部署主張。

Co-authored-by: Codex <codex@openai.com>
