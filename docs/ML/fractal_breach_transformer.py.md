# fractal_breach_transformer.py

**Назначение:** Небольшой Transformer-энкодер для бинарной классификации breach (Stage 5.0).

**Статус:** Завершён (использован в Stage 5.0)

**Архитектура:**
- token_projection: Linear(token_dim → d_model=64)
- pos_embedding: обучаемый эмбеддинг позиции (0..seq_len-1)
- encoder: 2 слоя, nhead=4, dim_feedforward=128, dropout=0.15
- pooling: masked mean + newest-valid-token concat → 2*d_model
- row_mlp: MLP для строковых признаков (ATR + время)
- head: Linear(2*d_model + d_model/2, 1) → BCEWithLogitsLoss

**Вход:**
- tokens: (batch, seq_len, token_dim)
- row_features: (batch, row_dim)
- mask: (batch, seq_len), True=валидный токен

**Выход:** logits (batch, 1)

**TokenSelector:** вспомогательный класс для отбора и упорядочивания фракталов:
- `by_corridor()` — фракталы в пределах ±X*ATR от fractal0.price
- `by_nearest()` — K ближайших по цене
- `newest_n()` — N свежайших фракталов
- `all_fractals()` — все фракталы (fractal0 самый свежий)

**Использование:**
```python
from ML.models.fractal_breach_transformer import FractalBreachTransformer, TokenSelector

model = FractalBreachTransformer(token_dim=10, row_dim=5, d_model=64, nhead=4)
logits = model(tokens, row_features, mask)
```

**Связанные файлы:**
- `ML/baseline/benchmark_stage5_transformer_breach.py` — раннер
- `tests/test_stage5_transformer_breach.py` — тесты
- `ML/models/transformer.py` — родительский Transformer (3-классовая классификация)
