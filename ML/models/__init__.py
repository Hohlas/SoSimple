# =============================================================================
# Файл: __init__.py
# Назначение: Реестр нейросетевых моделей для классификации фракталов
# Язык: Python 3.11+
# Обновлён: 2026-02-18
# =============================================================================

"""
Реестр моделей для сравнения архитектур.

Все модели имеют единый интерфейс:
    forward(x: Tensor, mask: Tensor | None = None) -> Tensor
    Вход:  x shape (batch, seq_len, features) или (batch, features, seq_len) для CNN
    Выход: logits shape (batch, num_classes)
"""

from ML.models.bilstm import BiLSTMClassifier
from ML.models.cnn1d import CNN1DClassifier
from ML.models.transformer import TransformerClassifier
from ML.models.hybrid_cnn_lstm import HybridCNNLSTMClassifier

# Реестр: имя → класс модели
MODEL_REGISTRY: dict[str, type] = {
    'bilstm': BiLSTMClassifier,
    'cnn1d': CNN1DClassifier,
    'transformer': TransformerClassifier,
    'hybrid': HybridCNNLSTMClassifier,
}


def get_model(name: str, **kwargs) -> 'torch.nn.Module':
    """
    Создание модели по имени.

    Аргументы:
        name: Имя модели из MODEL_REGISTRY ('bilstm', 'cnn1d', 'transformer', 'hybrid')
        **kwargs: Дополнительные аргументы (input_features, num_classes и т.д.)

    Возвращает:
        Инстанс модели

    Исключения:
        ValueError: Если имя модели не найдено в реестре
    """
    if name not in MODEL_REGISTRY:
        available = ', '.join(MODEL_REGISTRY.keys())
        raise ValueError(f"Модель '{name}' не найдена. Доступны: {available}")
    return MODEL_REGISTRY[name](**kwargs)
