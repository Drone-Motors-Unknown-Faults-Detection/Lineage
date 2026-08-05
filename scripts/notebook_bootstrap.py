"""Notebook 共用的初始化：日誌、stdout/stderr tee、matplotlib 自動存圖。

128 個 notebook 原本各自內嵌一份 56 行的 bootstrap，任何修正都要改 128 個
地方（issue #42 就是這樣被複製了 128 份）。統一收斂到這個模組，notebook
端只留下三行呼叫。

用法（notebook 第一個 cell）：

    from scripts.notebook_bootstrap import bootstrap

    LOG, RUN_PATHS = bootstrap()
"""

from __future__ import annotations

import atexit

from scripts.logger import (
    RunPaths,
    SimpleFileLogger,
    save_plot,
    setup_logger,
    tee_std_to_file,
)


def _patch_pyplot(log: SimpleFileLogger, run_paths: RunPaths) -> None:
    """讓 plt.show() 在顯示之前先把當前 figure 存進 output/。

    每張 figure 只會被存一次，判斷依據是 figure 物件本身。

    先前的版本改用「距離上次存圖不足 0.5 秒就跳過」的時間窗口來去重，
    結果會把緊接在學習曲線後面的混淆矩陣整張丟掉——因為時間戳是在
    plt.show() 回來之後才更新的（issue #42）。改以 figure 識別之後，
    連續產生多張圖也不會漏。
    """
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    if getattr(plt, "_lineage_save_plot_patched", False):
        return
    plt._lineage_save_plot_patched = True

    orig_show = plt.show
    saving: set[int] = set()

    def show_and_save(*args, **kwargs):
        fig = plt.gcf()
        key = id(fig)

        # key 已在集合中表示這張圖正走在存檔流程裡，直接放行避免遞迴
        # （savefig 理論上不會回頭呼叫 show，這裡只是保險）。
        if key not in saving:
            saving.add(key)
            try:
                save_plot(plt, log, run_paths)
            except Exception:
                pass

        try:
            return orig_show(*args, **kwargs)
        finally:
            try:
                plt.close(fig)
            except Exception:
                pass
            # figure 關掉後 id 可能被新物件重用，這裡一定要移除。
            saving.discard(key)

    plt.show = show_and_save


def bootstrap(program: str = "notebook") -> tuple[SimpleFileLogger, RunPaths]:
    """建立本次執行的 logger、把 stdout/stderr 導向 log、並掛上自動存圖。"""
    log, run_paths = setup_logger(program, console=False)

    tee_ctx = tee_std_to_file(run_paths.log_file)
    tee_ctx.__enter__()
    atexit.register(tee_ctx.__exit__, None, None, None)

    # 確保 TensorFlow 在結束時釋放 GPU/graph 資源
    try:
        import tensorflow as tf

        atexit.register(tf.keras.backend.clear_session)
    except Exception:
        pass

    _patch_pyplot(log, run_paths)
    return log, run_paths
