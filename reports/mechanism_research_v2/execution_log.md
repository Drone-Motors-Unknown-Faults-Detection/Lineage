# 執行紀錄

2026-10-02 Asia/Taipei。P0：完整讀 AGENT、附件、literature五份說明/結果索引、accuracy及fixed-calibration索引，閱讀實際representation/classifier/score/fit/cal/verify/feature讀取與metric程式。起點791ee5b，17 artifact SHA、9 model SHA、234 audit與formal SHA scan PASS。847原dirty entries/282 deletions保留。psutil不可用，使用stdlib作業系統記憶體介面；無新增系統安裝。未重訓或改指標舊檔。

原科學限制維持：全部舊資料曝光、三顆不同motor、age與individual混雜、raw/session未知、test群組不足。各阶段commit與push實際核對後追加，不預寫成功。

P0 commit af380efe78ef3b51bc1d0c6dbda4f505c8b1ac2c 已 push，remote ref 與 local 一致。
P1：13 個 metric v2 cases PASS。624 組 / 6,013,647 records / 28,910 unique 的舊預測重算 exit 0；未訓練/重推模型。2026-10-02-12-51-52 的 metric seal 19c1dd6b5a27d5de6c3ec8898f24123cbb68252f2e774a19141586fabf6ae59b。舊 healthy unknown-FPR 與新互斥項相符，新增完整健康誤報揭露 C17 T1/8000 =100%。無門檻調整。保留 R17 六格不足與舊報告。

P1 commit def53146e3881eb284a52c1f650e7886108a6f07 已 push，remote exact。
P2 只讀診斷 exit0；3 個 seed0 parent models，formal source 前後一致，無 fit/threshold 修改。兩圖檢視，2screws train=100%/test=0%；R17 真實 cal 各類足量但 predicted routes 空。形成 H-D/H-P/H-G，未知採集事實不補造。
