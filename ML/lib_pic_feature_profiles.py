# =============================================================================
# Файл: lib_pic_feature_profiles.py
# Назначение: Общие профили признаков `lib_PIC` для диагностики и будущего обучения.
# Обновлён: 2026-04-19
# Входные данные:
#   - DataFrame с колонками `fractal0..fractalN` и опциональными row-level колонками
# Выходные данные:
#   - DataFrame с выбранным набором инженерных признаков
# Использование:
#   from ML.lib_pic_feature_profiles import build_lib_pic_feature_profile
# Примечания:
#   - Не читает CSV и не запускает обучение.
# =============================================================================

from __future__ import annotations

import numpy as np
import pandas as pd

from ML.feature_importance_diagnostics import build_grouped_features
from ML.lib_pic_geometry_feature_bank import GEOMETRY_FEATURE_PREFIX, build_lib_pic_geometry_feature_bank
from ML.lib_pic_path_reaction_feature_bank import PATH_REACTION_FEATURE_PREFIX, build_lib_pic_path_reaction_feature_bank


BASELINE_CLEAN_DROP_GROUPS = ('direction', 'price_position', 'path_long', 'path_short')

LIB_PIC_FEATURE_PROFILES = (
    'baseline_full',
    'baseline_clean',
    'baseline_full_path',
    'baseline_clean_path',
    'baseline_clean_geometry_path',
)


def _prefixed_columns(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    columns = [column for column in frame.columns if column.startswith(prefix)]
    return frame[columns].replace([np.inf, -np.inf], 0.0).fillna(0.0)


def validate_lib_pic_feature_profile(profile: str) -> None:
    """Проверяет имя профиля признаков `lib_PIC`."""
    if profile not in LIB_PIC_FEATURE_PROFILES:
        available = ', '.join(LIB_PIC_FEATURE_PROFILES)
        raise ValueError(f'unknown lib_PIC feature profile: {profile}. Available: {available}')


def clean_baseline_columns(base: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    """Удаляет группы, которые диагностически ухудшали компактный baseline."""
    drop_columns: set[str] = set()
    for group in BASELINE_CLEAN_DROP_GROUPS:
        drop_columns.update(groups.get(group, []))
    keep_columns = [column for column in base.columns if column not in drop_columns]
    return base[keep_columns].copy()


def build_lib_pic_feature_parts(frame: pd.DataFrame, seq_len: int) -> dict[str, pd.DataFrame]:
    """Строит базовые, geometry и path части один раз для нескольких профилей.

    Аргументы:
        frame: DataFrame с fractal-колонками.
        seq_len: Сколько свежих фракталов использовать из строки.

    Возвращает:
        Словарь с частями признаков: `baseline_full`, `baseline_clean`, `geometry`, `path`.
    """
    base, groups = build_grouped_features(frame, seq_len=seq_len)
    geometry = build_lib_pic_geometry_feature_bank(frame)
    path = build_lib_pic_path_reaction_feature_bank(frame)
    return {
        'baseline_full': base,
        'baseline_clean': clean_baseline_columns(base, groups),
        'geometry': _prefixed_columns(geometry, GEOMETRY_FEATURE_PREFIX),
        'path': _prefixed_columns(path, PATH_REACTION_FEATURE_PREFIX),
    }


def assemble_lib_pic_feature_profile(parts: dict[str, pd.DataFrame], profile: str) -> pd.DataFrame:
    """Собирает один профиль из заранее построенных частей."""
    validate_lib_pic_feature_profile(profile)
    baseline_key = 'baseline_clean' if profile.startswith('baseline_clean') else 'baseline_full'
    frames = [parts[baseline_key]]
    if profile in ('baseline_full_path', 'baseline_clean_path', 'baseline_clean_geometry_path'):
        frames.append(parts['path'])
    if profile == 'baseline_clean_geometry_path':
        frames.append(parts['geometry'])
    return pd.concat(frames, axis=1).replace([np.inf, -np.inf], 0.0).fillna(0.0)


def build_lib_pic_feature_profile(frame: pd.DataFrame, profile: str, seq_len: int) -> pd.DataFrame:
    """Строит готовый профиль признаков `lib_PIC`.

    Аргументы:
        frame: DataFrame с fractal-колонками.
        profile: Один из `LIB_PIC_FEATURE_PROFILES`.
        seq_len: Сколько свежих фракталов использовать из строки.

    Возвращает:
        Числовой DataFrame признаков. Индекс совпадает с входным `frame`.
    """
    return assemble_lib_pic_feature_profile(build_lib_pic_feature_parts(frame, seq_len=seq_len), profile=profile)
