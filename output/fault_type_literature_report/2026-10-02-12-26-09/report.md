# 文獻導向擴展與改編實測（2026-10-02）

實際完成 624/630 組，未完成 6 組；6,013,647 筆逐樣本預測（同28,910個樣本重複使用，不是新的獨立資料）。

只有現有三顆不同馬達資料；healthy＋5 known螺絲配置／4 unknown螺絲配置，不是9種確認物理故障原因。全部樣本歷史已曝光，本輪前鎖定不能消除曝光。以下最高分是多方法搜尋的描述性結果，不能直接宣稱可靠或部署winner。

## 全部分類方法

| ID | 表示法／RPM／分類器／變更係數 | fault-only accuracy% | fault-only BA% | fault-only macro-F1% | healthy+known accuracy% |
|---|---|---:|---:|---:|---:|
| C01 | base75 / mixed / lda / None | 16.25 | 16.47 | 14.25 | 22.98 |
| C02 | base75 / mixed / linear / None | 26.61 | 26.78 | 24.04 | 34.15 |
| C03 | base75 / mixed / extra / None | 23.86 | 23.51 | 20.41 | 33.95 |
| C04 | base75 / mixed / forest / None | 26.99 | 26.70 | 21.81 | 33.66 |
| C05 | base75 / mixed / boost / None | 26.81 | 27.00 | 20.19 | 33.74 |
| C06 | base75 / mixed / svm / None | 16.33 | 16.24 | 18.19 | 23.21 |
| C07 | base75 / mixed / knn / 5 | 23.82 | 23.56 | 24.72 | 31.45 |
| C08 | base75 / mixed / knn / 15 | 22.32 | 22.02 | 22.88 | 30.41 |
| C09 | base75 / mixed / nb / None | 25.60 | 26.19 | 20.02 | 30.37 |
| C10 | base75 / mixed / rda / [0.5, 0.1] | 23.23 | 23.77 | 17.79 | 30.55 |
| C11 | base75 / mixed / rda / [0.5, 0.5] | 26.12 | 26.47 | 22.92 | 32.83 |
| C12 | base75 / mixed / rda / [0.0, 0.1] | 20.94 | 21.16 | 15.90 | 27.47 |
| C13 | base75 / mixed / lda / 0.1 | 15.74 | 16.01 | 13.79 | 25.87 |
| C14 | base75 / mixed / lda / 0.5 | 23.98 | 24.04 | 22.57 | 30.08 |
| C15 | base75 / mixed / lda / 0.9 | 27.69 | 27.77 | 24.56 | 29.71 |
| C16 | signed66 / mixed / lda / None | 19.86 | 20.41 | 17.83 | 29.19 |
| C17 | harmonic69 / mixed / lda / None | 30.43 | 30.80 | 28.52 | 39.29 |
| C18 | harmonic66 / mixed / lda / None | 25.83 | 26.27 | 22.30 | 33.83 |
| C19 | pca20 / mixed / lda / None | 17.17 | 17.41 | 15.99 | 26.24 |
| C20 | nca10 / mixed / knn / 5 | 21.65 | 21.38 | 20.51 | 30.62 |
| C21 | harmonic69 / mixed / forest / None | 24.21 | 24.54 | 18.89 | 34.68 |
| C22 | harmonic69 / mixed / svm / None | 16.72 | 16.48 | 13.73 | 24.87 |
| C23 | base75 / mixed / rda / [1.0, 0.1] | 15.66 | 15.93 | 13.75 | 25.68 |
| C24 | base75 / separate / lda / None | 30.91 | 31.21 | 28.66 | 32.17 |

兩factory共用分類器：closed-set accuracy相同是正常；拒絕後final分類另列，不混用同名accuracy。

## 全部開集方法

| 方法 | AUROC | unknown recall% | healthy FPR% | known rejection% | final open-set accuracy% |
|---|---:|---:|---:|---:|---:|
| C01/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 16.02 |
| C01/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 21.12 |
| C02/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 22.64 |
| C02/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 24.85 |
| C03/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 21.59 |
| C03/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 26.20 |
| C04/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 21.70 |
| C04/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 26.30 |
| C05/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 22.39 |
| C05/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 25.29 |
| C06/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 16.23 |
| C06/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 20.08 |
| C07/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 20.07 |
| C07/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 24.57 |
| C08/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 19.43 |
| C08/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 23.93 |
| C09/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 20.17 |
| C09/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 23.50 |
| C10/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 20.47 |
| C10/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 23.81 |
| C11/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 21.87 |
| C11/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 25.20 |
| C12/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 18.60 |
| C12/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 22.89 |
| C13/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 17.75 |
| C13/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 22.54 |
| C14/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 20.00 |
| C14/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 24.53 |
| C15/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 19.94 |
| C15/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 23.62 |
| C16/knn | 0.5263 | 5.47 | 0.03 | 2.76 | 19.87 |
| C16/mahalanobis | 0.5566 | 4.60 | 0.00 | 4.47 | 19.52 |
| C17/knn | 0.5608 | 7.48 | 9.24 | 6.35 | 25.59 |
| C17/mahalanobis | 0.5756 | 8.44 | 0.00 | 4.94 | 27.14 |
| C18/knn | 0.5613 | 7.46 | 9.31 | 6.35 | 22.23 |
| C18/mahalanobis | 0.5916 | 8.18 | 0.00 | 4.78 | 23.73 |
| C19/knn | 0.5867 | 3.40 | 0.99 | 2.46 | 17.26 |
| C19/mahalanobis | 0.5781 | 12.29 | 0.00 | 6.07 | 20.65 |
| C20/knn | 0.5835 | 3.94 | 4.88 | 3.64 | 19.25 |
| C20/mahalanobis | 0.5702 | 9.35 | 2.38 | 5.57 | 21.82 |
| C21/knn | 0.5608 | 7.48 | 9.24 | 6.35 | 23.07 |
| C21/mahalanobis | 0.5756 | 8.44 | 0.00 | 4.94 | 24.31 |
| C22/knn | 0.5608 | 7.48 | 9.24 | 6.35 | 18.03 |
| C22/mahalanobis | 0.5756 | 8.44 | 0.00 | 4.94 | 18.38 |
| C23/knn | 0.5711 | 5.45 | 0.74 | 5.25 | 17.63 |
| C23/mahalanobis | 0.5746 | 18.44 | 0.00 | 12.82 | 22.45 |
| C24/knn | 0.5348 | 16.90 | 30.68 | 19.78 | 22.21 |
| C24/mahalanobis | 0.5388 | 21.07 | 8.99 | 18.73 | 24.04 |
| R01/R01 | 0.5579 | 11.47 | 0.00 | 12.34 | 18.43 |
| R02/R02 | 0.5901 | 14.51 | 0.00 | 13.56 | 18.73 |
| R03/R03 | 0.5643 | 13.37 | 0.00 | 12.62 | 19.19 |
| R04/R04 | 0.4714 | 8.80 | 15.65 | 11.02 | 15.61 |
| R05/R05 | 0.5596 | 12.93 | 0.00 | 12.54 | 19.01 |
| R06/R06 | 0.5877 | 11.44 | 0.07 | 9.22 | 18.41 |
| R07/R07 | 0.5740 | 4.78 | 0.71 | 5.25 | 15.76 |
| R08/R08 | 0.5691 | 6.01 | 0.78 | 5.26 | 16.23 |
| R09/R09 | 0.6043 | 14.66 | 8.91 | 5.51 | 19.00 |
| R10/R10 | 0.5375 | 10.63 | 7.13 | 11.69 | 17.17 |
| R11/R11 | 0.5770 | 5.86 | 0.18 | 7.32 | 16.23 |
| R12/R12 | 0.5664 | 7.06 | 3.80 | 9.94 | 16.70 |
| R13/R13 | 0.5574 | 11.47 | 0.00 | 12.36 | 18.43 |
| R14/R14 | 0.4773 | 4.49 | 5.54 | 6.83 | 14.74 |
| R15/R15 | 0.4586 | 4.49 | 5.54 | 6.83 | 14.74 |
| R16/R16 | 0.4770 | 4.48 | 5.54 | 6.83 | 14.74 |
| R17/R17 | NA | NA | NA | NA | NA |
| R18/R18 | 0.5714 | 22.68 | 9.49 | 12.08 | 30.62 |
| R19/R19 | 0.4677 | 1.95 | 0.11 | 3.48 | 14.62 |
| R20/R20 | 0.4952 | 7.92 | 12.56 | 11.05 | 16.82 |
| R21/R21 | 0.4902 | 4.49 | 5.54 | 6.83 | 14.74 |
| R22/R22 | 0.4900 | 4.49 | 5.54 | 6.83 | 14.74 |

## 描述性最高分（不是部署選擇）

- known_fault_classification.accuracy: C24/knn=0.309091, healthy FPR=0.306756, known rejection=0.197758; C24/mahalanobis=0.309091, healthy FPR=0.089947, known rejection=0.187331; C17/knn=0.304315, healthy FPR=0.092416, known rejection=0.063493
- known_fault_classification.balanced_accuracy: C24/knn=0.312085, healthy FPR=0.306756, known rejection=0.197758; C24/mahalanobis=0.312085, healthy FPR=0.089947, known rejection=0.187331; C17/knn=0.308005, healthy FPR=0.092416, known rejection=0.063493
- known_classification.accuracy: C17/knn=0.392863, healthy FPR=0.092416, known rejection=0.063493; C17/mahalanobis=0.392863, healthy FPR=0.000000, known rejection=0.049382; R18/R18=0.392863, healthy FPR=0.094941, known rejection=0.120828
- unknown_rejection.auroc_unknown_positive: R09/R09=0.604251, healthy FPR=0.089124, known rejection=0.055083; C18/mahalanobis=0.591564, healthy FPR=0.000000, known rejection=0.047776; R02/R02=0.590051, healthy FPR=0.000000, known rejection=0.135584
- unknown_rejection.unknown_recall: R18/R18=0.226793, healthy FPR=0.094941, known rejection=0.120828; C24/mahalanobis=0.210715, healthy FPR=0.089947, known rejection=0.187331; C01/mahalanobis=0.184367, healthy FPR=0.000000, known rejection=0.128212
- final_open_set_classification.accuracy: R18/R18=0.306225, healthy FPR=0.094941, known rejection=0.120828; C17/mahalanobis=0.271446, healthy FPR=0.000000, known rejection=0.049382; C04/mahalanobis=0.262997, healthy FPR=0.000000, known rejection=0.128212

## 逐馬達與轉速完整證據

所有方法、3seed實值、3motor、RPM、配置逐類召回與confusion matrices見compact summary及verified.json.gz，均由保存預測重算並與sealed模型重新推論逐筆比對。以下每方法三顆馬達均值，不挑最好seed。

| 方法 | test motor | fault-only accuracy% | unknown AUROC | unknown recall% | healthy FPR% |
|---|---|---:|---:|---:|---:|
| C01/knn | T1 | 25.93 | 0.5850 | 0.00 | 0.00 |
| C01/knn | T2 | 7.33 | 0.5262 | 15.87 | 2.22 |
| C01/knn | T3 | 15.49 | 0.6020 | 0.49 | 0.00 |
| C01/mahalanobis | T1 | 25.93 | 0.5074 | 0.00 | 0.00 |
| C01/mahalanobis | T2 | 7.33 | 0.6140 | 46.91 | 0.00 |
| C01/mahalanobis | T3 | 15.49 | 0.6024 | 8.40 | 0.00 |
| C02/knn | T1 | 34.67 | 0.5850 | 0.00 | 0.00 |
| C02/knn | T2 | 22.07 | 0.5262 | 15.87 | 2.22 |
| C02/knn | T3 | 23.10 | 0.6020 | 0.49 | 0.00 |
| C02/mahalanobis | T1 | 34.67 | 0.5074 | 0.00 | 0.00 |
| C02/mahalanobis | T2 | 22.07 | 0.6140 | 46.91 | 0.00 |
| C02/mahalanobis | T3 | 23.10 | 0.6024 | 8.40 | 0.00 |
| C03/knn | T1 | 22.62 | 0.5850 | 0.00 | 0.00 |
| C03/knn | T2 | 34.85 | 0.5262 | 15.87 | 2.22 |
| C03/knn | T3 | 14.11 | 0.6020 | 0.49 | 0.00 |
| C03/mahalanobis | T1 | 22.62 | 0.5074 | 0.00 | 0.00 |
| C03/mahalanobis | T2 | 34.85 | 0.6140 | 46.91 | 0.00 |
| C03/mahalanobis | T3 | 14.11 | 0.6024 | 8.40 | 0.00 |
| C04/knn | T1 | 32.30 | 0.5850 | 0.00 | 0.00 |
| C04/knn | T2 | 31.06 | 0.5262 | 15.87 | 2.22 |
| C04/knn | T3 | 17.62 | 0.6020 | 0.49 | 0.00 |
| C04/mahalanobis | T1 | 32.30 | 0.5074 | 0.00 | 0.00 |
| C04/mahalanobis | T2 | 31.06 | 0.6140 | 46.91 | 0.00 |
| C04/mahalanobis | T3 | 17.62 | 0.6024 | 8.40 | 0.00 |
| C05/knn | T1 | 30.42 | 0.5850 | 0.00 | 0.00 |
| C05/knn | T2 | 27.52 | 0.5262 | 15.87 | 2.22 |
| C05/knn | T3 | 22.49 | 0.6020 | 0.49 | 0.00 |
| C05/mahalanobis | T1 | 30.42 | 0.5074 | 0.00 | 0.00 |
| C05/mahalanobis | T2 | 27.52 | 0.6140 | 46.91 | 0.00 |
| C05/mahalanobis | T3 | 22.49 | 0.6024 | 8.40 | 0.00 |
| C06/knn | T1 | 19.84 | 0.5850 | 0.00 | 0.00 |
| C06/knn | T2 | 24.91 | 0.5262 | 15.87 | 2.22 |
| C06/knn | T3 | 4.24 | 0.6020 | 0.49 | 0.00 |
| C06/mahalanobis | T1 | 19.84 | 0.5074 | 0.00 | 0.00 |
| C06/mahalanobis | T2 | 24.91 | 0.6140 | 46.91 | 0.00 |
| C06/mahalanobis | T3 | 4.24 | 0.6024 | 8.40 | 0.00 |
| C07/knn | T1 | 20.41 | 0.5850 | 0.00 | 0.00 |
| C07/knn | T2 | 33.05 | 0.5262 | 15.87 | 2.22 |
| C07/knn | T3 | 17.99 | 0.6020 | 0.49 | 0.00 |
| C07/mahalanobis | T1 | 20.41 | 0.5074 | 0.00 | 0.00 |
| C07/mahalanobis | T2 | 33.05 | 0.6140 | 46.91 | 0.00 |
| C07/mahalanobis | T3 | 17.99 | 0.6024 | 8.40 | 0.00 |
| C08/knn | T1 | 21.08 | 0.5850 | 0.00 | 0.00 |
| C08/knn | T2 | 27.44 | 0.5262 | 15.87 | 2.22 |
| C08/knn | T3 | 18.44 | 0.6020 | 0.49 | 0.00 |
| C08/mahalanobis | T1 | 21.08 | 0.5074 | 0.00 | 0.00 |
| C08/mahalanobis | T2 | 27.44 | 0.6140 | 46.91 | 0.00 |
| C08/mahalanobis | T3 | 18.44 | 0.6024 | 8.40 | 0.00 |
| C09/knn | T1 | 30.26 | 0.5850 | 0.00 | 0.00 |
| C09/knn | T2 | 25.23 | 0.5262 | 15.87 | 2.22 |
| C09/knn | T3 | 21.32 | 0.6020 | 0.49 | 0.00 |
| C09/mahalanobis | T1 | 30.26 | 0.5074 | 0.00 | 0.00 |
| C09/mahalanobis | T2 | 25.23 | 0.6140 | 46.91 | 0.00 |
| C09/mahalanobis | T3 | 21.32 | 0.6024 | 8.40 | 0.00 |
| C10/knn | T1 | 28.05 | 0.5850 | 0.00 | 0.00 |
| C10/knn | T2 | 35.24 | 0.5262 | 15.87 | 2.22 |
| C10/knn | T3 | 6.38 | 0.6020 | 0.49 | 0.00 |
| C10/mahalanobis | T1 | 28.05 | 0.5074 | 0.00 | 0.00 |
| C10/mahalanobis | T2 | 35.24 | 0.6140 | 46.91 | 0.00 |
| C10/mahalanobis | T3 | 6.38 | 0.6024 | 8.40 | 0.00 |
| C11/knn | T1 | 28.01 | 0.5850 | 0.00 | 0.00 |
| C11/knn | T2 | 41.31 | 0.5262 | 15.87 | 2.22 |
| C11/knn | T3 | 9.03 | 0.6020 | 0.49 | 0.00 |
| C11/mahalanobis | T1 | 28.01 | 0.5074 | 0.00 | 0.00 |
| C11/mahalanobis | T2 | 41.31 | 0.6140 | 46.91 | 0.00 |
| C11/mahalanobis | T3 | 9.03 | 0.6024 | 8.40 | 0.00 |
| C12/knn | T1 | 25.71 | 0.5850 | 0.00 | 0.00 |
| C12/knn | T2 | 30.03 | 0.5262 | 15.87 | 2.22 |
| C12/knn | T3 | 7.08 | 0.6020 | 0.49 | 0.00 |
| C12/mahalanobis | T1 | 25.71 | 0.5074 | 0.00 | 0.00 |
| C12/mahalanobis | T2 | 30.03 | 0.6140 | 46.91 | 0.00 |
| C12/mahalanobis | T3 | 7.08 | 0.6024 | 8.40 | 0.00 |
| C13/knn | T1 | 23.64 | 0.5850 | 0.00 | 0.00 |
| C13/knn | T2 | 13.67 | 0.5262 | 15.87 | 2.22 |
| C13/knn | T3 | 9.90 | 0.6020 | 0.49 | 0.00 |
| C13/mahalanobis | T1 | 23.64 | 0.5074 | 0.00 | 0.00 |
| C13/mahalanobis | T2 | 13.67 | 0.6140 | 46.91 | 0.00 |
| C13/mahalanobis | T3 | 9.90 | 0.6024 | 8.40 | 0.00 |
| C14/knn | T1 | 35.07 | 0.5850 | 0.00 | 0.00 |
| C14/knn | T2 | 22.40 | 0.5262 | 15.87 | 2.22 |
| C14/knn | T3 | 14.48 | 0.6020 | 0.49 | 0.00 |
| C14/mahalanobis | T1 | 35.07 | 0.5074 | 0.00 | 0.00 |
| C14/mahalanobis | T2 | 22.40 | 0.6140 | 46.91 | 0.00 |
| C14/mahalanobis | T3 | 14.48 | 0.6024 | 8.40 | 0.00 |
| C15/knn | T1 | 38.23 | 0.5850 | 0.00 | 0.00 |
| C15/knn | T2 | 32.40 | 0.5262 | 15.87 | 2.22 |
| C15/knn | T3 | 12.44 | 0.6020 | 0.49 | 0.00 |
| C15/mahalanobis | T1 | 38.23 | 0.5074 | 0.00 | 0.00 |
| C15/mahalanobis | T2 | 32.40 | 0.6140 | 46.91 | 0.00 |
| C15/mahalanobis | T3 | 12.44 | 0.6024 | 8.40 | 0.00 |
| C16/knn | T1 | 25.93 | 0.6119 | 8.00 | 0.10 |
| C16/knn | T2 | 18.83 | 0.3726 | 0.00 | 0.00 |
| C16/knn | T3 | 14.82 | 0.5945 | 8.40 | 0.00 |
| C16/mahalanobis | T1 | 25.93 | 0.5218 | 0.00 | 0.00 |
| C16/mahalanobis | T2 | 18.83 | 0.5046 | 5.66 | 0.00 |
| C16/mahalanobis | T3 | 14.82 | 0.6435 | 8.13 | 0.00 |
| C17/knn | T1 | 32.91 | 0.6760 | 0.00 | 0.00 |
| C17/knn | T2 | 28.88 | 0.4581 | 14.03 | 27.72 |
| C17/knn | T3 | 29.50 | 0.5483 | 8.40 | 0.00 |
| C17/mahalanobis | T1 | 32.91 | 0.5033 | 0.00 | 0.00 |
| C17/mahalanobis | T2 | 28.88 | 0.6189 | 13.22 | 0.00 |
| C17/mahalanobis | T3 | 29.50 | 0.6047 | 12.09 | 0.00 |
| C18/knn | T1 | 25.79 | 0.6713 | 0.00 | 0.00 |
| C18/knn | T2 | 28.96 | 0.4604 | 13.97 | 27.94 |
| C18/knn | T3 | 22.74 | 0.5521 | 8.40 | 0.00 |
| C18/mahalanobis | T1 | 25.79 | 0.5285 | 0.00 | 0.00 |
| C18/mahalanobis | T2 | 28.96 | 0.6401 | 13.12 | 0.00 |
| C18/mahalanobis | T3 | 22.74 | 0.6060 | 11.41 | 0.00 |
| C19/knn | T1 | 27.22 | 0.6468 | 0.00 | 0.00 |
| C19/knn | T2 | 22.24 | 0.5383 | 9.77 | 2.96 |
| C19/knn | T3 | 2.03 | 0.5751 | 0.43 | 0.00 |
| C19/mahalanobis | T1 | 27.22 | 0.5672 | 0.00 | 0.00 |
| C19/mahalanobis | T2 | 22.24 | 0.6127 | 28.73 | 0.00 |
| C19/mahalanobis | T3 | 2.03 | 0.5543 | 8.16 | 0.00 |
| C20/knn | T1 | 22.28 | 0.6536 | 0.00 | 0.00 |
| C20/knn | T2 | 30.10 | 0.5642 | 11.46 | 14.64 |
| C20/knn | T3 | 12.56 | 0.5327 | 0.37 | 0.00 |
| C20/mahalanobis | T1 | 22.28 | 0.6377 | 0.00 | 0.00 |
| C20/mahalanobis | T2 | 30.10 | 0.6422 | 23.43 | 7.13 |
| C20/mahalanobis | T3 | 12.56 | 0.4306 | 4.61 | 0.00 |
| C21/knn | T1 | 31.94 | 0.6760 | 0.00 | 0.00 |
| C21/knn | T2 | 27.20 | 0.4581 | 14.03 | 27.72 |
| C21/knn | T3 | 13.49 | 0.5483 | 8.40 | 0.00 |
| C21/mahalanobis | T1 | 31.94 | 0.5033 | 0.00 | 0.00 |
| C21/mahalanobis | T2 | 27.20 | 0.6189 | 13.22 | 0.00 |
| C21/mahalanobis | T3 | 13.49 | 0.6047 | 12.09 | 0.00 |
| C22/knn | T1 | 21.14 | 0.6760 | 0.00 | 0.00 |
| C22/knn | T2 | 19.58 | 0.4581 | 14.03 | 27.72 |
| C22/knn | T3 | 9.45 | 0.5483 | 8.40 | 0.00 |
| C22/mahalanobis | T1 | 21.14 | 0.5033 | 0.00 | 0.00 |
| C22/mahalanobis | T2 | 19.58 | 0.6189 | 13.22 | 0.00 |
| C22/mahalanobis | T3 | 9.45 | 0.6047 | 12.09 | 0.00 |
| C23/knn | T1 | 23.67 | 0.5850 | 0.00 | 0.00 |
| C23/knn | T2 | 13.41 | 0.5262 | 15.87 | 2.22 |
| C23/knn | T3 | 9.90 | 0.6020 | 0.49 | 0.00 |
| C23/mahalanobis | T1 | 23.67 | 0.5074 | 0.00 | 0.00 |
| C23/mahalanobis | T2 | 13.41 | 0.6140 | 46.91 | 0.00 |
| C23/mahalanobis | T3 | 9.90 | 0.6024 | 8.40 | 0.00 |
| C24/knn | T1 | 25.10 | 0.6248 | 21.89 | 50.76 |
| C24/knn | T2 | 36.74 | 0.4327 | 23.58 | 41.27 |
| C24/knn | T3 | 30.88 | 0.5470 | 5.23 | 0.00 |
| C24/mahalanobis | T1 | 25.10 | 0.5634 | 0.00 | 0.00 |
| C24/mahalanobis | T2 | 36.74 | 0.5327 | 47.74 | 26.98 |
| C24/mahalanobis | T3 | 30.88 | 0.5204 | 15.47 | 0.00 |
| R01/R01 | T1 | 25.93 | 0.4884 | 0.00 | 0.00 |
| R01/R01 | T2 | 7.33 | 0.5677 | 26.10 | 0.00 |
| R01/R01 | T3 | 15.49 | 0.6177 | 8.29 | 0.00 |
| R02/R02 | T1 | 25.93 | 0.5448 | 8.03 | 0.00 |
| R02/R02 | T2 | 7.33 | 0.5788 | 18.86 | 0.00 |
| R02/R02 | T3 | 15.49 | 0.6466 | 16.64 | 0.00 |
| R03/R03 | T1 | 25.93 | 0.4973 | 0.00 | 0.00 |
| R03/R03 | T2 | 7.33 | 0.5713 | 25.95 | 0.00 |
| R03/R03 | T3 | 15.49 | 0.6242 | 14.17 | 0.00 |
| R04/R04 | T1 | 25.93 | 0.5405 | 0.00 | 0.00 |
| R04/R04 | T2 | 7.33 | 0.4481 | 14.34 | 0.00 |
| R04/R04 | T3 | 15.49 | 0.4256 | 12.06 | 46.95 |
| R05/R05 | T1 | 25.93 | 0.4888 | 0.00 | 0.00 |
| R05/R05 | T2 | 7.33 | 0.5688 | 26.13 | 0.00 |
| R05/R05 | T3 | 15.49 | 0.6212 | 12.66 | 0.00 |
| R06/R06 | T1 | 25.93 | 0.5363 | 0.00 | 0.00 |
| R06/R06 | T2 | 7.33 | 0.6148 | 30.60 | 0.21 |
| R06/R06 | T3 | 15.49 | 0.6120 | 3.71 | 0.00 |
| R07/R07 | T1 | 25.93 | 0.5879 | 0.00 | 0.00 |
| R07/R07 | T2 | 7.33 | 0.5298 | 13.84 | 2.12 |
| R07/R07 | T3 | 15.49 | 0.6045 | 0.49 | 0.00 |
| R08/R08 | T1 | 25.93 | 0.5834 | 0.00 | 0.00 |
| R08/R08 | T2 | 7.33 | 0.5225 | 17.53 | 2.33 |
| R08/R08 | T3 | 15.49 | 0.6015 | 0.49 | 0.00 |
| R09/R09 | T1 | 25.93 | 0.5347 | 0.00 | 0.00 |
| R09/R09 | T2 | 7.33 | 0.6805 | 43.87 | 26.74 |
| R09/R09 | T3 | 15.49 | 0.5975 | 0.10 | 0.00 |
| R10/R10 | T1 | 25.93 | 0.5880 | 0.26 | 0.00 |
| R10/R10 | T2 | 7.33 | 0.4376 | 24.81 | 21.38 |
| R10/R10 | T3 | 15.49 | 0.5868 | 6.83 | 0.00 |
| R11/R11 | T1 | 25.93 | 0.6370 | 0.00 | 0.00 |
| R11/R11 | T2 | 7.33 | 0.4809 | 14.23 | 0.53 |
| R11/R11 | T3 | 15.49 | 0.6132 | 3.33 | 0.00 |
| R12/R12 | T1 | 25.93 | 0.5544 | 4.51 | 11.40 |
| R12/R12 | T2 | 7.33 | 0.5069 | 16.34 | 0.00 |
| R12/R12 | T3 | 15.49 | 0.6378 | 0.33 | 0.00 |
| R13/R13 | T1 | 25.93 | 0.4864 | 0.00 | 0.00 |
| R13/R13 | T2 | 7.33 | 0.5684 | 26.13 | 0.00 |
| R13/R13 | T3 | 15.49 | 0.6175 | 8.29 | 0.00 |
| R14/R14 | T1 | 25.93 | 0.5329 | 5.02 | 9.89 |
| R14/R14 | T2 | 7.33 | 0.4665 | 5.12 | 3.92 |
| R14/R14 | T3 | 15.49 | 0.4324 | 3.33 | 2.82 |
| R15/R15 | T1 | 25.93 | 0.5594 | 5.02 | 9.89 |
| R15/R15 | T2 | 7.33 | 0.3999 | 5.12 | 3.92 |
| R15/R15 | T3 | 15.49 | 0.4164 | 3.33 | 2.82 |
| R16/R16 | T1 | 25.93 | 0.5343 | 5.02 | 9.89 |
| R16/R16 | T2 | 7.33 | 0.4649 | 5.12 | 3.92 |
| R16/R16 | T3 | 15.49 | 0.4317 | 3.31 | 2.82 |
| R17/R17 | T1 | 25.93 | 0.4316 | 0.00 | 5.15 |
| R17/R17 | T2 | NA | NA | NA | NA |
| R17/R17 | T3 | NA | NA | NA | NA |
| R18/R18 | T1 | 32.91 | 0.4812 | 15.35 | 17.76 |
| R18/R18 | T2 | 28.88 | 0.6217 | 11.14 | 0.00 |
| R18/R18 | T3 | 29.50 | 0.6113 | 41.54 | 10.72 |
| R19/R19 | T1 | 25.93 | 0.5357 | 0.00 | 0.00 |
| R19/R19 | T2 | 7.33 | 0.4283 | 0.13 | 0.21 |
| R19/R19 | T3 | 15.49 | 0.4393 | 5.72 | 0.11 |
| R20/R20 | T1 | 25.93 | 0.4469 | 0.00 | 0.00 |
| R20/R20 | T2 | 7.33 | 0.4540 | 23.77 | 37.67 |
| R20/R20 | T3 | 15.49 | 0.5847 | 0.00 | 0.00 |
| R21/R21 | T1 | 25.93 | 0.4894 | 5.02 | 9.89 |
| R21/R21 | T2 | 7.33 | 0.5039 | 5.12 | 3.92 |
| R21/R21 | T3 | 15.49 | 0.4774 | 3.33 | 2.82 |
| R22/R22 | T1 | 25.93 | 0.4821 | 5.02 | 9.89 |
| R22/R22 | T2 | 7.33 | 0.5101 | 5.12 | 3.92 |
| R22/R22 | T3 | 15.49 | 0.4778 | 3.33 | 2.82 |

## 工程狀態與未通過項目

- 用途分離：各fold train/cal/test不同motor；無global selector，validation/selection IDs空。只有known train做scaler/PCA/NCA/classifier/reference，known cal只校準固定score；其他開發motor unknown unused。
- source fingerprint與90CSV SHA前後未變；factory Maha-LW/kNN基礎、正式105維資料與PolarMap未改；已封存歷史檔案不覆寫。
- 未通過方法不能以借test/cal fit、填補missing predicted group或翻轉符號來救分數；全部未完成格與reason列summary。
- NCA固定50iteration預算；觸頂者屬近似／budget-limited，不宣稱已找到最优嵌入。其他warnings完整列summary。
- 老師healthy＋5known／4unknown與按motor群組切分：本輪實際執行主固定配置。其他N／全部126組本輪未重跑，歷史2490次只讀。
- 每fold僅1個test motor，guard每類至少2 test groups要求仍INCOMPLETE；來源session、raw overlap、IQR mask與物理一致性仍UNKNOWN。不能將seeds、RPM、windows當作獨立馬達；無IID窗CI、無RUL、無量化老化。
- 無新的fresh final test，模型選擇／可靠部署未驗證；健康FPR零只是此資料觀察，不是固定5%保證。

## 原始來源與改編定位

28項封存來源加3項補充來源，共31項書目；見repository的reports/literature_expansion/sources.md與sources_addendum.md。部分只作範圍依據，不是31套新演算法已實測。C/R ID參數逐項見封存protocol。自訂表示法、RDA-inspired混合、RMD係數、預測類別cal、融合在core/fault_type_literature.py有函數級來源；不是聲稱新原創已發表方法。

## 歷史控制與成本

[{"new": "C02/mahalanobis", "historical": "A0/mahalanobis", "mean_differences": {"known_fault_classification.accuracy": 0.0, "known_fault_classification.balanced_accuracy": 0.0, "known_fault_classification.macro_f1": 0.0, "known_classification.accuracy": 0.0, "known_classification.balanced_accuracy": 0.0, "known_classification.macro_f1": 0.0, "unknown_rejection.auroc_unknown_positive": 0.0, "unknown_rejection.aupr_unknown_positive": 0.0, "unknown_rejection.unknown_recall": 0.0, "unknown_rejection.unknown_precision": 0.0, "unknown_rejection.unknown_f1": 0.0, "unknown_rejection.fpr_at_95_tpr": 0.0, "known_rejection_rate": 0.0, "healthy_safety.false_positive_rate": 0.0, "open_set_classification_rate": 0.0, "final_open_set_classification.accuracy": 0.0, "selective.accuracy_all_accepted": 0.0, "selective.coverage": 0.0}, "matches": true, "classification_matches": true, "expected_entire_method_match": true, "reference_scope_note": "C02 and A0 both mixed-RPM references", "scope": "saved historical summaries; not refit historical study"}, {"new": "C02/knn", "historical": "A0/knn", "mean_differences": {"known_fault_classification.accuracy": 0.0, "known_fault_classification.balanced_accuracy": 0.0, "known_fault_classification.macro_f1": 0.0, "known_classification.accuracy": 0.0, "known_classification.balanced_accuracy": 0.0, "known_classification.macro_f1": 0.0, "unknown_rejection.auroc_unknown_positive": 0.0, "unknown_rejection.aupr_unknown_positive": 0.0, "unknown_rejection.unknown_recall": 0.0, "unknown_rejection.unknown_precision": 0.0, "unknown_rejection.unknown_f1": 0.0, "unknown_rejection.fpr_at_95_tpr": 0.0, "known_rejection_rate": 0.0, "healthy_safety.false_positive_rate": 0.0, "open_set_classification_rate": 0.0, "final_open_set_classification.accuracy": 0.0, "selective.accuracy_all_accepted": 0.0, "selective.coverage": 0.0}, "matches": true, "classification_matches": true, "expected_entire_method_match": true, "reference_scope_note": "C02 and A0 both mixed-RPM references", "scope": "saved historical summaries; not refit historical study"}, {"new": "C24/mahalanobis", "historical": "A7/mahalanobis", "mean_differences": {"known_fault_classification.accuracy": 0.0, "known_fault_classification.balanced_accuracy": 0.0, "known_fault_classification.macro_f1": 0.0, "known_classification.accuracy": 0.0, "known_classification.balanced_accuracy": 0.0, "known_classification.macro_f1": 0.0, "unknown_rejection.auroc_unknown_positive": 0.0, "unknown_rejection.aupr_unknown_positive": 0.0, "unknown_rejection.unknown_recall": 0.0, "unknown_rejection.unknown_precision": 0.0, "unknown_rejection.unknown_f1": 0.0, "unknown_rejection.fpr_at_95_tpr": 0.0, "known_rejection_rate": 0.0, "healthy_safety.false_positive_rate": 0.0, "open_set_classification_rate": 0.0, "final_open_set_classification.accuracy": 0.0, "selective.accuracy_all_accepted": 0.0, "selective.coverage": 0.0}, "matches": true, "classification_matches": true, "expected_entire_method_match": true, "reference_scope_note": "C24 separately fits/calibrates RPM references; historical A7 shared the per-RPM A1 reference (A1 rpm_strategy=separate). Classifier and detector scopes are both identical; sharing a fitted reference does not mean pooling RPMs. Full metrics should reproduce.", "scope": "saved historical summaries; not refit historical study"}, {"new": "C24/knn", "historical": "A7/knn", "mean_differences": {"known_fault_classification.accuracy": 0.0, "known_fault_classification.balanced_accuracy": 0.0, "known_fault_classification.macro_f1": 0.0, "known_classification.accuracy": 0.0, "known_classification.balanced_accuracy": 0.0, "known_classification.macro_f1": 0.0, "unknown_rejection.auroc_unknown_positive": 0.0, "unknown_rejection.aupr_unknown_positive": 0.0, "unknown_rejection.unknown_recall": 0.0, "unknown_rejection.unknown_precision": 0.0, "unknown_rejection.unknown_f1": 0.0, "unknown_rejection.fpr_at_95_tpr": 0.0, "known_rejection_rate": 0.0, "healthy_safety.false_positive_rate": 0.0, "open_set_classification_rate": 0.0, "final_open_set_classification.accuracy": 0.0, "selective.accuracy_all_accepted": 0.0, "selective.coverage": 0.0}, "matches": true, "classification_matches": true, "expected_entire_method_match": true, "reference_scope_note": "C24 separately fits/calibrates RPM references; historical A7 shared the per-RPM A1 reference (A1 rpm_strategy=separate). Classifier and detector scopes are both identical; sharing a fitted reference does not mean pooling RPMs. Full metrics should reproduce.", "scope": "saved historical summaries; not refit historical study"}]

C02/A0檢查完整混合RPM方法；C24/A7檢查完整RPM分開方法。舊registry的A1 rpm_strategy=separate，A7共用的是per-RPM reference，不是mixed-RPM。四組控制的實際matches及全部差異見上列；未改已鎖定本輪方法來追求歷史分數一致。

physical bundle fit seconds=169.748; fit counts={'classifier_fits': 234, 'factory_reference_fits': 180, 'novelty_reference_fits': 174, 'representation_fits': 81}. 各邏輯run共享模型／參照，不把630組當630個獨立訓練或受試馬達。
