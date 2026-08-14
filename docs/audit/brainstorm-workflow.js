export const meta = {
  name: 'brainstorm-workflow',
  description: 'Брэйншторм новых источников trading edge: 4 параллельных генератора гипотез по векторам поиска → дедупликация → по 2 независимых критика на идею → детерминированное слияние вердиктов → синтез итогового списка в docs/audit/brainstorm-filtered.md.',
  phases: ['Генерация', 'Дедупликация', 'Атака гипотез', 'Синтез', 'Верификация'],
  // Контрактные ограничения:
  //   - Контекстное окно субагента ~150K. Основной вход каждого агента —
  //     docs/audit/retrospective.md (~2K слов), читается целиком.
  //   - knowledge-rag (search_knowledge) — только точечная проверка фактов;
  //     отчёты docs/reports/ и ML/reports/ целиком не читаются.
  //   - Одна идея = один критик. Критики не видят оценок друг друга
  //     (независимые треки) — защита от коррелированных ошибок.
  //   - Промпт-основа каждой фазы: docs/audit/next.md.
};

// Настройки: число независимых треков критики и минимальное число
// рецензий на идею (меньше — идея помечается как недооценённая).
const REVIEWERS_PER_IDEA = 2;
const MIN_REVIEWS = 2;
// Потолок числа идей после дедупликации: защита от разрастания фазы 3
// (критиков = идеи × REVIEWERS_PER_IDEA).
const MAX_IDEAS_AFTER_DEDUP = 20;

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
      return JSON.parse(cleaned.slice(first, last + 1));
    }
    throw new Error(label + ': не удалось извлечь JSON');
  }
};

// ═══════════════════════════════════════════════════════
// Фаза 1: Генерация (divergence)
// Параллельные генераторы по векторам поиска. Векторы пересекаются
// намеренно — пересечения убирает фаза дедупликации.
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
  leakage, малые выборки, low R², time-only dominance и т.д.).
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
    list.forEach(h => { if (h && h.name && h.essence) rawIdeas.push(h); });
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
// Фаза 2: Дедупликация и нормализация
// Один агент сливает близкие гипотезы и применяет жёсткие запреты,
// удаляя нарушающие идеи.
// ═══════════════════════════════════════════════════════

phase('Дедупликация');

const rawBlock = rawIdeas
  .map((h, i) => `${i + 1}. ${h.name}
Суть: ${h.essence}
Тупик: ${h.deadend}
Источник edge: ${h.edge_source}
Теги: ${Array.isArray(h.tags) ? h.tags.join('; ') : ''}`)
  .join('\n\n');

const dedupRaw = await agent(
  `Ниже — сырые гипотезы о новых источниках trading edge, собранные
${vectors.length} независимыми генераторами (с пересекающимися векторами).
Ретроспективу перечитывать не нужно.

${rawBlock}

Твоя задача:
1. Слей гипотезы с совпадающим механизмом edge — даже при разной упаковке.
   У объединённой оставь самую полную формулировку и все упомянутые тупики.
2. Удали идеи, нарушающие жёсткий запрет: классические индикаторы
   (RSI, MACD, ...) и прочие примитивные отжившие
   методы. Новизну по источнику информации проверяет следующий этап.
3. Теги объединяй. Пометки «похоже на: ...» и «радикальная» сохраняй.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"hypotheses": [{"name":"...","essence":"...","deadend":"...","edge_source":"...","tags":[]}]}`,
  { phase: 'Дедупликация', label: 'Слияние и чистка' }
);

let ideas;
try {
  ideas = parseJson(dedupRaw, 'Дедупликация').hypotheses;
} catch (e) {
  log('ОШИБКА: ' + e.message + '. Завершаю.');
  throw e;
}
ideas = (ideas || [])
  .filter(h => h && h.name && h.essence)
  .map(h => ({
    name: String(h.name),
    essence: String(h.essence),
    deadend: String(h.deadend || ''),
    edge_source: String(h.edge_source || ''),
    tags: Array.isArray(h.tags) ? h.tags : [],
  }));
if (ideas.length === 0) {
  log('ОШИБКА: дедупликация не вернула гипотез. Завершаю.');
  throw new Error('No hypotheses after dedup');
}
log(`После дедупликации: ${ideas.length} идей.`);

// Сохраняем промежуточный артефакт (Этап 1).
const ideasMd = `# Сырые гипотезы брэйншторма (после дедупликации)

Сгенерировано brainstorm-workflow.js, фаза 2. Ранжирования нет.

${ideas.map(h => `## ${h.name}
- Суть: ${h.essence}
- Обходимый тупик: ${h.deadend}
- Откуда edge: ${h.edge_source}
- Теги: ${h.tags.join('; ')}`).join('\n\n')}
`;

await agent(
  `Запиши приведённый ниже текст КАК ЕСТЬ в файл docs/audit/brainstorm-ideas.md
через инструмент Write. Ничего не добавляй и не редактируй. В ответе сообщи
только: «записано, N слов».

${ideasMd}`,
  { phase: 'Дедупликация', label: 'Запись brainstorm-ideas.md' }
);

// Потолок числа идей для фазы критики (аудит: стоимость растёт как
// идеи × REVIEWERS_PER_IDEA). Отброшенные — в лог, файл-артефакт полный.
if (ideas.length > MAX_IDEAS_AFTER_DEDUP) {
  const dropped = ideas.slice(MAX_IDEAS_AFTER_DEDUP).map(h => h.name);
  ideas = ideas.slice(0, MAX_IDEAS_AFTER_DEDUP);
  log(`Потолок ${MAX_IDEAS_AFTER_DEDUP} идей: отброшено ${dropped.length} — ${dropped.join(', ')}.`);
}

// ═══════════════════════════════════════════════════════
// Фаза 3: Атака гипотез (convergence)
// REVIEWERS_PER_IDEA независимых критиков на каждую идею.
// ═══════════════════════════════════════════════════════

phase('Атака гипотез');

const reviewJobs = [];
ideas.forEach((idea, i) => {
  for (let k = 1; k <= REVIEWERS_PER_IDEA; k++) {
    reviewJobs.push({ idea, idx: i, track: k });
  }
});
log(`Запускаю ${reviewJobs.length} критиков (${ideas.length} идей × ${REVIEWERS_PER_IDEA} трека)...`);

const reviewResults = await parallel(
  reviewJobs.map(job => () =>
    agent(
      `Ты — критически настроенный рецензент количественных исследований.
Атакуй гипотезу и убивай слабые. Не защищай идею и не ищи ей оправданий:
твоя ценность — жёсткий отсев. Других рецензий ты не видишь.

Контекст: проект SoSimple (Forex, personal research). Порог успеха:
PF ≥ 1.5 на строгом out-of-sample с bootstrap CI (нижняя граница > 1.0).
За ~6 месяцев ни одна система его не прошла.

Вход:
1. docs/audit/retrospective.md — прочитай ЦЕЛИКОМ. База проверки новизны:
   секция 2 — пройденные направления, секция 4 — что не работает.
2. knowledge-rag (search_knowledge) — только точечная проверка фактов,
   если гипотеза ссылается на результат, которого нет в ретроспективе.

Ключевые установленные факты (для быстрой проверки новизны, детали — в
ретроспективе):
- MI-аудит: маргинальная информация о направлении практически отсутствует
  (MI direction 0.003–0.004 bits, direction FAIL), потолок R² 0.006–0.030
  (см. 2.1). Идея обязана объяснять, откуда берётся информация, которой
  по MI-аудиту нет.
- Единственный стабильный сигнал — амплитудно-движенческий режим, а не знак
  (см. 2.11, 3).
- Календарная доминантность: no-ML hour-baseline догоняет ML-PF, все
  winner-правила time_only (см. 2.12).
- Весь edge Fixed11 зависел от некорректной внутрибаровой хронологии fill;
  после фикса PF < 1 (см. 2.12).
- Режимный перелом на границе 2023: провал 2023–2026 устойчив к расширению
  обучения (см. 2.8).

Гипотеза:
Название: ${job.idea.name}
Суть: ${job.idea.essence}
Обходимый тупик: ${job.idea.deadend}
Откуда edge: ${job.idea.edge_source}
Теги: ${job.idea.tags.join('; ')}

Выполни по порядку:
1. Новизна. Найди в ретроспективе (секции 2 и 4) эту идею или близкий аналог.
   Переупаковка закрытого направления → verdict "убита", в rationale —
   ссылка на секцию.
2. Атака. До трёх самых уязвимых мест (данные, стационарность, исполнение,
   размер выборки, происхождение edge).
3. Фальсификация. Спроектируй убивающий эксперимент: что проверить, метрика,
   конкретный порог/число, которое убивает идею. Эксперимент НЕ проводи.
   Если убивающий тест в рамках проекта не формулируется —
   falsifiable=false, в falsification — объяснение.
4. Происхождение edge. Слабый или отсутствующий механизм «кто платит» —
   добавь в массив tags элемент "спекуляция". Это снижает позицию,
   но не убивает.
5. Вердикт: "выживает" / "условно" / "убита". Если идея требует доработки,
   чтобы выжить — «условно» с указанием, чего не хватает.
   Убивай без сожаления: идея с неустранимым уязвимым местом не проходит.
   Не дополняй и не улучшай гипотезы.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"name": ${JSON.stringify(job.idea.name)},
 "novelty": {"duplicate_of": null, "retrospective_ref": "..."},
 "vulnerabilities": ["...", "..."],
 "falsification": {"test": "...", "metric": "...", "kill_threshold": "...", "cost": "часы/дни", "falsifiable": true},
 "tags": [],
 "verdict": "выживает|условно|убита",
 "rationale": "одно предложение"}`,
      { phase: 'Атака гипотез', label: `${job.idea.name} #${job.track}` }
    )
  )
);

// Группировка рецензий по идее с сохранением связки по индексу job.
// Вердикт вне тройки «выживает/условно/убита» — брак: рецензия отбрасывается,
// иначе неизвестный вариант молча превращался бы в «выживает» (аудит, п.2).
const ALLOWED_VERDICTS = ['выживает', 'условно', 'убита'];
const reviewsByIdea = ideas.map(() => []);
const missingReviews = [];
reviewResults.forEach((r, j) => {
  const job = reviewJobs[j];
  if (r == null) { missingReviews.push(job.idea.name); return; }
  try {
    const rev = parseJson(r, `Критик ${job.idea.name} #${job.track}`);
    if (rev && ALLOWED_VERDICTS.includes(String(rev.verdict))) {
      reviewsByIdea[job.idx].push(rev);
    } else {
      missingReviews.push(job.idea.name);
      log(`Внимание: ${job.idea.name} #${job.track} — вердикт вне тройки (${rev && rev.verdict}), рецензия отброшена.`);
    }
  } catch (e) {
    missingReviews.push(job.idea.name);
    log('Не удалось распарсить рецензию: ' + e.message);
  }
});
if (missingReviews.length > 0) {
  log(`Внимание: нет полной рецензии для: ${[...new Set(missingReviews)].join(', ')}.`);
}

// Детерминированное слияние вердиктов (без отдельного агента):
//   - любое «убита» — окончательно (консенсус критиков на убийство не нужен);
//   - любое «условно» при отсутствии «убита» — «условно»;
//   - все «выживает» — «выживает»;
//   - ноль рецензий — отдельный статус «без рецензии» (в короткий список
//     синтеза не допускается, аудит п.3).
const verdictRank = { 'выживает': 0, 'условно': 1, 'убита': 2, 'без рецензии': 3 };
const merged = ideas.map((idea, i) => {
  const reviews = reviewsByIdea[i];
  const verdicts = reviews.map(r => String(r.verdict));
  let verdict;
  if (reviews.length === 0) verdict = 'без рецензии';
  else if (verdicts.includes('убита')) verdict = 'убита';
  else if (verdicts.includes('условно')) verdict = 'условно';
  else verdict = 'выживает';
  // Флаг falsifiable живёт внутри объекта falsification (аудит, п.1).
  const hasFalsification = reviews.some(r => r.falsification);
  const falsifiable = reviews.some(r => r.falsification && r.falsification.falsifiable === false)
    ? false
    : hasFalsification;
  const extraTags = [...new Set(reviews.flatMap(r => (Array.isArray(r.tags) ? r.tags : [])))];
  return {
    ...idea,
    verdict,
    under_reviewed: reviews.length < MIN_REVIEWS,
    falsifiable,
    tags: [...new Set([...idea.tags, ...extraTags])],
    reviews,
  };
}).sort((a, b) => (verdictRank[a.verdict] ?? 3) - (verdictRank[b.verdict] ?? 3));

const counts = { выживает: 0, условно: 0, убита: 0, 'без рецензии': 0 };
merged.forEach(m => { counts[m.verdict] = (counts[m.verdict] || 0) + 1; });
log(`Вердикты: выживает ${counts['выживает']}, условно ${counts['условно']}, убита ${counts['убита']}, без рецензии ${counts['без рецензии']}.`);

// ═══════════════════════════════════════════════════════
// Фаза 4: Синтез итогового документа
// ═══════════════════════════════════════════════════════

phase('Синтез');

const mergedBlock = merged.map(m => `### ${m.name}
Суть: ${m.essence}
Обходимый тупик: ${m.deadend}
Откуда edge: ${m.edge_source}
Теги: ${m.tags.join('; ')}
Вердикт (по ${m.reviews.length} независимым рецензиям): ${m.verdict}${m.under_reviewed ? ' [недооценена: рецензий меньше минимума]' : ''}${m.falsifiable === false ? ' [нефальсифицируема]' : ''}
${m.reviews.map((r, k) => `Рецензия ${k + 1}: ${r.rationale || ''}
  Уязвимости: ${(r.vulnerabilities || []).join('; ')}
  Фальсификация: ${r.falsification ? `${r.falsification.test} | метрика: ${r.falsification.metric} | убивает: ${r.falsification.kill_threshold} | стоимость: ${r.falsification.cost}` : 'не задана'}`).join('\n')}`).join('\n\n');

await agent(
  `Ты пишешь итоговый документ брэйншторма по результатам независимой
критики. Ниже — идеи с вердиктами. Ретроспективу перечитывать не нужно.

${mergedBlock}

Напиши файл docs/audit/brainstorm-filtered.md со структурой:

1. Короткий список выживших (вердикт «выживает», при нехватке — добирай из
   «условно»; всего не более 10), от самых дешёвых к самым дорогим по
   стоимости убивающего эксперимента. Правдоподобие edge оценивай ТОЛЬКО
   по полю «Откуда edge» — других данных о потенциале нет, ничего не
   додумывай. Для каждой: суть (1–2 предложения), обходимый тупик,
   убивающий эксперимент с метрикой и порогом, стоимость,
   пометки [радикальная]/[спекуляция]/«условно».
   [нефальсифицируема] — в конец списка с объяснением.
   Идеи с вердиктом «без рецензии» в короткий список НЕ включай —
   выведи их отдельным примечанием в конце документа.
2. Таблица-сводка: идея | вердикт | обходимый тупик | убивающий результат |
   стоимость.
3. Список убитых: идея | причина | ссылка на секцию ретроспективы,
   если убита за переупаковку.

Правила:
- Не улучшай, не дополняй и не воскрешай убитые идеи.
- Вердикты и числа из рецензий не выдумывай заново — используй как есть.
- Спекуляции помечай [гипотеза].

Используй инструмент Write. После записи НЕ выводи содержимое файла —
сообщи только: сколько идей выжило, условно, убито — и топ-3 выживших
кратким списком.`,
  { phase: 'Синтез', label: 'Итоговый документ' }
);

// ═══════════════════════════════════════════════════════
// Фаза 5: Верификация
// Дешёвый assert: итоговый файл реально записан и не пуст.
// ═══════════════════════════════════════════════════════

phase('Верификация');

const verifyResult = await agent(
  `Проверь результат брэйншторма. Используй bash:
ls -l docs/audit/brainstorm-filtered.md
и wc -w docs/audit/brainstorm-filtered.md
Если файл отсутствует или содержит меньше 150 слов — ответь СТРОГО:
"ABORT: <причина>". Иначе ответь СТРОГО: "OK: <число> слов".`,
  { phase: 'Верификация', label: 'Assert итогового файла' }
);

if (/^ABORT:/i.test(normalizeResult(verifyResult).trim())) {
  log('ОШИБКА: верификация прервана — ' + normalizeResult(verifyResult).slice(0, 200));
  throw new Error('Verification aborted: ' + normalizeResult(verifyResult).slice(0, 200));
}

log('Брэйншторм завершён: docs/audit/brainstorm-filtered.md');
