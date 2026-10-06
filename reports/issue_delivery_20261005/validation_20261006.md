# 交付工具最後驗證

2026-10-06 18:40–18:41，Asia/Taipei。

兩環境各執行同一條命令（Python路徑分別為`.venv310/Scripts/python.exe`與`venv/Scripts/python.exe`）：

```powershell
python -m unittest tests.test_fault_type_citation_audit tests.test_fault_type_archive tests.test_fault_type_issue_triage -v
```

| Python | passed | failed | skipped | 範圍 |
|---|---:|---:|---:|---|
| 3.10.19 | 24 | 0 | 0 | 18引用／文書、1備份、5稽核入口 |
| 3.14.6 | 24 | 0 | 0 | 相同測試 |

稽核入口測試覆蓋：未選取的頂層程式不執行、缺指定函數拒絕、GH物件與列表分頁、固定main反例與Stage2寫入stub。對應main歷史Git物件必須已可讀；此測試不宣稱網路API在線可用或所有惡意archive安全。

兩Python另各實際執行`-m experiments.fault_type_issue_triage`，完成的logs與JSON為18-37-06／18-37-13。網路盤點只在18-34-48執行一次。相同函數來源SHA與反例一致，run目錄路徑不同。docs/README.md的30個相對檔案目標都存在，不宣稱外站連結或段落錨點全數有效。

兩份Word實際render在18-27-42均exit1：bundled soffice.exe缺失，沒有頁面PNG。表格內容／SHA／ZIP CRC通過與LAYOUT_UNVERIFIED並列，不能互相替代。正式模型與資料沒有修改；本輪沒有重跑完整ML套件或2490歷史矩陣。

老師Markdown的生成output使用LF（SHA a3bc39b68d348354701ac9b4bf600af2cd106aa32bf56f7e5040b4685e23aff0）；Git工作樹checkout使用CRLF（SHA 6e00788476f68fe8f2f7cf2ce5dbeec5fc36339aa8ff4d17158eb2259439b7ed）。Git正規化blob均為5a17558e6224d15357cbadc2054a8bbbad76cd3a，沒有內容diff。兩者不當成相同bytes；Word二進位SHA與QA完全一致。
