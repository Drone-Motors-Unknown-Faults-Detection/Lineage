import tensorflow as tf


def _configure() -> tuple[str, list]:
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            names = [gpu.name for gpu in tf.config.experimental.get_visible_devices('GPU')]
            print(f"[gpu_utils] GPU x{len(gpus)} 已啟用：{names}")
            return '/GPU:0', gpus
        except RuntimeError as e:
            print(f"[gpu_utils] GPU 初始化失敗（{e}），回退至 CPU")
    print("[gpu_utils] 未偵測到 GPU，使用 CPU")
    return '/CPU:0', []


DEVICE, _GPUS = _configure()


def device_scope():
    """回傳 tf.device context manager，自動對應 GPU 或 CPU。

    使用範例：
        with device_scope():
            model = build_cnn_model(...)
            model.fit(...)
    """
    return tf.device(DEVICE)


def gpu_count() -> int:
    return len(_GPUS)


def is_gpu() -> bool:
    return len(_GPUS) > 0
