"""訓練前後的健全性檢查（issue #50）。

Step 3 / Step 6 的訓練若因為輸入含 NaN 而失敗，不會拋出任何例外——模型照樣
存檔、notebook 照樣「成功」結束、`.sh` 的 `set -e` 也不會觸發。唯一的線索是
準確率剛好等於 `1 / 類別數`：

    Step3_Model_01   Loss: nan, Accuracy: 0.2017     # 0.2017 = 1/5

特徵檔 2972 x 105 個值裡只有一個 NaN，就足以把整個網路的權重汙染成 NaN。
這個模組把那種靜默失敗變成明確的例外。

用法（Step 3 / Step 6 的訓練 cell）：

    from scripts.train_guard import assert_finite_inputs, assert_model_learned

    assert_finite_inputs(X_train=X_train, X_test=X_test)

    with device_scope():
        model = build_cnn_model(...)
        history = model.fit(...)

    results = model.evaluate(...)
    assert_model_learned(history, results, num_classes)
"""

from __future__ import annotations

import numpy as np


class TrainingSanityError(AssertionError):
    """訓練資料或訓練結果未通過健全性檢查。"""


def assert_finite_inputs(**arrays) -> None:
    """確認每個輸入陣列都不含 NaN 或 inf。

    以關鍵字傳入，名稱會出現在錯誤訊息裡：

        assert_finite_inputs(X_train=X_train, X_test=X_test)
    """
    for name, arr in arrays.items():
        a = np.asarray(arr, dtype=float)
        n_nan = int(np.isnan(a).sum())
        n_inf = int(np.isinf(a).sum())
        if n_nan or n_inf:
            # 指出前幾個出問題的位置，方便回頭查特徵檔
            bad = np.argwhere(~np.isfinite(a))
            head = ", ".join(str(tuple(int(i) for i in idx)) for idx in bad[:5])
            more = f"，另有 {len(bad) - 5} 處" if len(bad) > 5 else ""
            raise TrainingSanityError(
                f"{name} 含非有限值：NaN {n_nan} 個、inf {n_inf} 個。"
                f"位置（列, 欄）：{head}{more}。"
                f"請檢查對應的 *_Group_feature_data.csv 是否有缺值未被 dropna 濾掉。"
            )


def assert_model_learned(
    history,
    results,
    num_classes: int,
    *,
    margin: float = 0.05,
) -> None:
    """確認訓練確實收斂，而不是產出一個隨機猜測水準的模型。

    兩道檢查：

    1. 最終 loss 必須是有限值。NaN loss 沒有任何模糊空間，一定是壞的。
    2. 測試準確率不得貼近 `1 / num_classes`。落在該水準代表模型什麼都沒學到，
       最常見的成因就是 NaN 汙染。

    `margin` 是第二道的容忍度。真的很難的任務也可能接近隨機水準，若確認是
    資料本身的問題而非 bug，可以放寬或在呼叫端跳過這道檢查。
    """
    final_loss = float(history.history["loss"][-1])
    if not np.isfinite(final_loss):
        raise TrainingSanityError(
            f"訓練結束時 loss = {final_loss}，權重已被 NaN/inf 汙染，模型無效。"
        )

    eval_loss, accuracy = float(results[0]), float(results[1])
    if not np.isfinite(eval_loss):
        raise TrainingSanityError(f"評估 loss = {eval_loss}，模型無效。")

    chance = 1.0 / num_classes
    if accuracy <= chance + margin:
        raise TrainingSanityError(
            f"測試準確率 {accuracy:.4f} 未超過隨機猜測水準 "
            f"(1/{num_classes} = {chance:.4f}，容忍度 {margin})，模型可能未收斂。"
        )
