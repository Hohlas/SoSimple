export const meta = {
  name: 'idea-brainstorm',
  description: 'Часть 1 брэйншторма: 4 параллельных генератора гипотез о новых источниках trading edge (векторы пересекаются намеренно). Результат — docs/audit/brainstorm-raw.json для части 2 (idea-check). Запускать на сильной модели.',
  phases: ['Генерация', 'Запись'],
  // Контрактные ограничения:
  //   - Контекстное окно субагента ~150K. Основной вход каждого агента —
  //     docs/audit/retrospective.md (~2K слов), читается целиком.
  //   - knowledge-rag (search_knowledge) — только точечная проверка фактов;
  //     отчёты docs/reports/ и ML/reports/ целиком не читаются.
  //   - Передатчик в часть 2 — файл docs/audit/brainstorm-raw.json;
  //     часть 2 (idea-check) может быть запущена в другой среде. Модель
  //     выбирается вручную в настройках запускающей сессии.
};

// ═══════════════════════════════════════════════════════
// Утилиты
// ═══════════════════════════════════════════════════════

const normalizeResult = (r) => {
  if (r == null) return '';
  if (typeof r === 'string') return r;
  if (typeof r === 'object' && r.content != null) return String(r.content);
  try { return JSON.stringify(r); } catch { return ''; }
};

const parseJson = (raw, label) => {
  const s = normalizeResult(raw).trim();
  if (!s) throw new Error(label + ': пустой ответ агента');
  const cleaned = s.replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/i, '');
  try {
    return JSON.parse(cleaned);
  } catch (_) {
    const first = cleaned.indexOf('{');
    const last = cleaned.lastIndexOf('}');
    if (first !== -1 && last > first) {
      try {
        return JSON.parse(cleaned.slice(first, last + 1));
      } catch (__) { /* переход к стандартизированной ошибке ниже */ }
    }
    throw new Error(label + ': не удалось извлечь JSON');
  }
};

// ═══════════════════════════════════════════════════════
// Фаза 1: Генерация (divergence)
// Параллельные генераторы по векторам поиска. Векторы пересекаются
// намеренно — пересечения размечает часть 2.
// ═══════════════════════════════════════════════════════

phase('Генерация');

const vectors = [
  {
    name: 'Данные и таргеты',
    focus: `Новые представления данных и таргеты: НЕ «направление следующего бара».
Волатильность, амплитуда, форма пути, горизонт до события, условные
распределения, альтернативные формулировки цели (не классификация направления).`,
  },
  {
    name: 'Смежные области',
    focus: `Методы из смежных областей, применённые к Forex-ряду: микроструктура,
статистическая физика, causal inference, change-point detection,
survival analysis, теория очередей и аналогичные.`,
  },
  {
    name: 'Комбинации и рефрейминг',
    focus: `Комбинации известных подходов анализа временных рядов в новой роли
и рефрейминг задачи: торговля как другая задача (отбор, ранжирование,
управление риском, поиск аномалий), новые схемы входа/выхода,
ансамбли по новому признаку.`,
  },
  {
    name: 'Радикальные',
    focus: `Радикально новые подходы, противоречащие текущим допущениям проекта:
другая частота решений, другие инструменты/пары, отказ от предсказания
в пользу отбора или хеджирования, асимметрии исполнения. Каждую помечай
[радикальная].`,
  },
];

log(`Запускаю ${vectors.length} генераторов параллельно...`);

const genResults = await parallel(
  vectors.map(v => () =>
    agent(
      `Ты — исследователь количественной торговли, генератор идей. Задача —
количество и широта охвата. Критика и самоцензура запрещены: оценка
жизнеспособности — работа следующего этапа.

Контекст: проект SoSimple (Forex, personal research). За ~6 месяцев
(февраль–август 2026) ~150 исследований. Порог успеха: PF ≥ 1.3 на строгом
out-of-sample с bootstrap CI (нижняя граница > 1.0) — не достигнут ни разу.

Вход: прочитай docs/audit/retrospective.md ЦЕЛИКОМ. Секция 2 — направления
и вердикты, секции 4/6/7 — что не работает, нерешённые проблемы,
накопленные ограничения. knowledge-rag (search_knowledge) — только точечная
проверка фактов; отчёты целиком не читай.

Твой вектор поиска: ${v.name}
${v.focus}

Сгенерируй 6–10 гипотез о принципиально новых источниках устойчивого
trading edge, которые ретроспектива ещё не исключила.
Количество важнее глубины: эксперименты не проектируй, идеи не ранжируй.

Формат каждой гипотезы (в JSON-полях):
- name: 2–5 слов.
- essence: 1–3 предложения.
- deadend: какой тупик из ретроспективы обходит (already-moved, regime drift,
  leakage, малые выборки, low R², time-only dominance и т.д.). Если аналога
  в ретроспективе нет — оставь пустым, не притягивай.
- edge_source: одно предложение — кто платит и почему эффект может быть
  устойчивым; начинай с «[гипотеза] ».
- tags: массив. Если явно похожа на закрытое направление из секции 4 —
  добавь элемент «похоже на: <название>». Для этого вектора допустим
  элемент «радикальная».

Не предлагай классические индикаторы (RSI, MACD, скользящие средние и т.п.)
и прочие примитивные отжившие методы. Не выдавай предположения за факты.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"hypotheses": [{"name":"...","essence":"...","deadend":"...","edge_source":"...","tags":[]}],
 "vector": "${v.name}"}`,
      { phase: 'Генерация', label: v.name }
    )
  )
);

// Сохраняем связку результат ↔ вектор по индексу (не filter(Boolean) до map).
const rawIdeas = [];
const genFailures = [];
genResults.forEach((r, i) => {
  if (r == null) { genFailures.push(vectors[i].name); return; }
  try {
    const parsed = parseJson(r, `Генератор «${vectors[i].name}»`);
    const list = Array.isArray(parsed.hypotheses) ? parsed.hypotheses : [];
    list.forEach(h => {
      if (h && h.name && h.essence) {
        // Нормализация на входе: дальше h.tags используется без защит.
        rawIdeas.push({ ...h, tags: Array.isArray(h.tags) ? h.tags : [] });
      }
    });
  } catch (e) {
    genFailures.push(vectors[i].name);
    log('Не удалось распарсить: ' + e.message);
  }
});

if (genFailures.length > 0) {
  log(`Внимание: генераторы без результата: ${genFailures.join(', ')}.`);
}
if (rawIdeas.length === 0) {
  log('ОШИБКА: все генераторы упали или не дали гипотез. Завершаю.');
  throw new Error('No hypotheses generated');
}
log(`Сырых гипотез: ${rawIdeas.length}.`);

// ═══════════════════════════════════════════════════════
// Фаза 2: Запись передатчика для части 2
// ═══════════════════════════════════════════════════════

phase('Запись');

const rawJson = JSON.stringify({ hypotheses: rawIdeas }, null, 2);

await agent(
  `Запиши приведённый ниже текст КАК ЕСТЬ в файл docs/audit/brainstorm-raw.json
через инструмент Write. Ничего не добавляй и не редактируй. В ответе сообщи
только: «записано, N гипотез».

${rawJson}`,
  { phase: 'Запись', label: 'Запись brainstorm-raw.json' }
);

// Верификация: файл реально записан и содержит гипотезы.
const verifyResult = await agent(
  `Проверь результат. Используй bash:
ls -l docs/audit/brainstorm-raw.json
и wc -c docs/audit/brainstorm-raw.json
Если файл отсутствует или его размер меньше 500 байт — ответь СТРОГО:
"ABORT: <причина>". Иначе ответь СТРОГО: "OK: <число> байт".`,
  { phase: 'Запись', label: 'Assert brainstorm-raw.json' }
);

if (/^ABORT:/i.test(normalizeResult(verifyResult).trim())) {
  log('ОШИБКА: верификация прервана — ' + normalizeResult(verifyResult).slice(0, 200));
  throw new Error('Verification aborted: ' + normalizeResult(verifyResult).slice(0, 200));
}

log(`Генерация завершена: ${rawIdeas.length} гипотез в docs/audit/brainstorm-raw.json. Запускайте часть 2 (idea-check).`);
