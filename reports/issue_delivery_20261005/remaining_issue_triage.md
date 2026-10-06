# 剩餘 issue 分工與範圍

2026-10-06 18:35（Asia/Taipei）重新GET所有分頁：14項open issue，PR不計入；1項open PR。指定#22／#20已closed completed，#19仍open。固定main為64cb71d84663e1745ec54db74abad68def67e8e6；研究交付已push至e7ee971d2ed41d5ce80e3a56f912eb4dc1c038dc，未合併。

所有open issue沒有assignee；作者是JW-Albert不代表已完成或他必然接手。下表「保留程式工作」依使用者本輪分工界線及實際PR／檔案重疊，不作未經授權的指派。全body及全部comments、PR資料保存於output/fault_type_issue_triage/2026-10-06-18-34-48/github_snapshot.json。

| Issue | 要求與最新差異 | 分類／本輪處理 | 程式或資料下一步 |
|---|---|---|---|
| #9 | 獨立來源／fresh／可靠配置辨識；body部分落後comments | 外部資料資格及研究未通過；老師文件已說明不同motor與Python3.10後續完成 | 不關閉；不把processed ordinals當raw intervals，不要求不存在的硬體 |
| #13 | 實驗九非線性AE | 保留程式工作；主線仍無AE | core/detectors與新手冊；本輪不訓練 |
| #14 | 實驗十少量healthy遷移 | 保留程式工作；exp5直接搬移不等於適應 | 新協定、known-only目標適應；不偷看unknown |
| #15 | 實驗十一Ancestor配對比較 | 保留程式與新實驗 | known總類數及切分與本輪不同；+5pp天花板、balanced/F1事前定義 |
| #16 | 實驗十二confusion／t-SNE | 保留程式工作；#19補原t-SNE書目 | 報告既有表格不代表本issue完成 |
| #19 | 全引用存在與內容 | 本輪部分完成清冊／原文卡／勘誤，OPEN | 缺原參考表及未核合法全文；未核內容不得PASS |
| #24 | health CLI setup_run | 保留Albert實驗八工作；現main預設仍reports/exp8 | PR36修改health_monitor，同檔重疊，不改 |
| #25 | 實驗八跨seed彙總程式 | 保留程式工作；comments已改新exp8路徑 | 不用exp6 aggregator假裝已重算health |
| #26 | Python政策與依賴鎖 | 主線工程分工未明，保留 | 研究3.10／3.14通過不能代替主線clean install／lock政策 |
| #27 | CI及高風險測試 | 主線工程保留；main有Web catalog tests但不足 | CI、loader、WS、exp1–3仍有缺口 |
| #28 | Origin／bind／token | 保留安全程式；main仍放行，PR36同server檔 | 不把PR串流功能當security修補 |
| #29 | monitor fitted guard | 主線程式分工未明，保留 | 明確pre-fit失敗且分數regression；不改 |
| #30 | 17項歷史稽核 | 本輪接手唯讀重驗、R1–R10草稿；部分完成 | 發布新issue與main§2.2整合未執行，不關閉 |
| #35 | health_monitor未知配置健康索引 | Albert活躍PR36承認的既有bug；保留 | main與PR head區分，不能因iter_run存在就當已修 |

PR36作者JW-Albert，head544d4ed8c6516622e2f46c095351f9483a61635c，open；改Web、exp1／3／4、health_monitor、iter_run及相關文件，未合併。本輪不改它的檔案。PR8已merged（afcfcc4）；PR32已merged（1161f55），health移到experiments/health、reports清理已在main。本輪沒有恢復main已刪稽核目錄或建立重複repo。

#30精確重驗見main_reaudit.md；只發布這份有界稽核回報，不批次建立／指派R1–R10。沒有其他合適的非衝突程式工作，本輪文件交付後停止。
