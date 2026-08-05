"""模型結構相關的共用工具。

Step 4 / Step 5 需要取出 CNN 的中間層輸出，當作 HDBSCAN 叢集與馬氏距離的
無監督特徵空間。原本的寫法是硬編死層名：

    feat_model = Model(inputs=cnn.input, outputs=cnn.get_layer('flatten').output)

但三種架構的特徵層並不同名——ResNet 用 Global Average Pooling，根本沒有
Flatten 層，於是 9 個 ResNet 的 Step 4 與 9 個 Step 5 notebook 全部拋出
`ValueError: No such layer: flatten`（issue #52）。

    CNN_C8000      12 層   ... max_pooling1d_2, flatten, dense, dropout, 輸出
    VGG16_C8000    25 層   ... flatten, dense, dropout, dense_1, dropout_1, 輸出
    ResNet_C8000   69 層   ... add_7, activation_16, global_average_pooling1d, 輸出
"""

from __future__ import annotations

# 依序嘗試的特徵層名稱。順序有意義：先找 Flatten，沒有才退到 GAP。
FEATURE_LAYER_CANDIDATES = ("flatten", "global_average_pooling1d")


def get_feature_layer(model):
    """回傳要作為無監督特徵空間的中間層。

    依 `FEATURE_LAYER_CANDIDATES` 的順序找；都找不到時退回輸出層的前一層
    （對這三種架構而言，那就是分類頭前面的最後一個特徵層）。
    """
    for name in FEATURE_LAYER_CANDIDATES:
        try:
            return model.get_layer(name)
        except ValueError:
            continue

    fallback = model.layers[-2]
    print(
        f"[model_utils] 找不到 {FEATURE_LAYER_CANDIDATES} 之中任何一層，"
        f"改用輸出層前一層：{fallback.name}"
    )
    return fallback


def feature_layer_output(model):
    """`get_feature_layer(model).output` 的簡寫。"""
    return get_feature_layer(model).output
