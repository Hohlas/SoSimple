export const meta = {
  name: 'brainstorm-workflow',
  description: 'Брэйншторм новых источников trading edge: 4 параллельных генератора гипотез по векторам поиска → разметка кластеров похожих идей без слияния → по 2 независимых критика на идею → детерминированное слияние вердиктов → синтез итогового списка в docs/audit/brainstorm-filtered.md.',
  phases: ['Генерация', 'Дедупликация', 'Атака гипотез', 'Синтез', 'Верификация'],
  // Контрактные ограничения:
  //   - Контекстное окно субагента ~150K. Основной вход каждого агента —
  //     docs/audit/retrospective.md (~2K слов), читается целиком.
  //   - knowledge-rag (search_knowledge) — только точечная проверка фактов;
  //     отчёты docs/reports/ и ML/reports/ целиком не читаются.
  //   - Одна идея = один критик. Критики не видят оценок друг друга
  //     (независимые треки) — защита от коррелированных ошибок.
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
- deadend: необязательное поле. Если идея обходит конкретный тупик из
  ретроспективы (already-moved, regime drift, leakage, малые выборки,
  low R², time-only dominance и т.д.) — назови его. Если аналога
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
// Фаза 2: Разметка кластеров и нормализация
// Один агент помечает похожие гипотезы кластерами (БЕЗ слияния)
// и применяет жёсткие запреты, удаляя нарушающие идеи.
// ═══════════════════════════════════════════════════════

phase('Дедупликация');

const rawBlock = rawIdeas
  .map((h, i) => `${i + 1}. ${h.name}
Суть: ${h.essence}
Тупик: ${h.deadend || 'не указан'}
Источник edge: ${h.edge_source}
Теги: ${Array.isArray(h.tags) ? h.tags.join('; ') : ''}`)
  .join('\n\n');

const dedupRaw = await agent(
  `Ниже — сырые гипотезы о новых источниках trading edge, собранные
${vectors.length} независимыми генераторами (с пересекающимися векторами).

${rawBlock}

Твоя задача:
1. Разметь кластеры: идеи с совпадающим механизмом edge получают один
   номер кластера (число, начиная с 1). НЕ сливай и НЕ переписывай идеи —
   каждая формулировка сохраняется как есть. Выбор лучшей версии внутри
   кластера — работа этапа критики, не твоя.
2. Удали идеи, нарушающие жёсткий запрет: классические индикаторы
   (RSI, MACD, скользящие средние и т.п.) и прочие примитивные отжившие
   методы. Больше ничего не убивай: новизну по источнику информации
   проверяет следующий этап, у тебя для этого нет контекста.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки.
items содержит ВСЕ неудалённые идеи, имя в name — в точности как во входе:
{"items": [{"name":"...","cluster":1}]}`,
  { phase: 'Дедупликация', label: 'Разметка кластеров' }
);

let clustersByName;
try {
  const items = parseJson(dedupRaw, 'Разметка кластеров').items;
  clustersByName = new Map(
    (Array.isArray(items) ? items : [])
      .filter(it => it && it.name)
      .map(it => [String(it.name), Number(it.cluster) || 0])
  );
} catch (e) {
  log('ОШИБКА: ' + e.message + '. Завершаю.');
  throw e;
}

// Идеи берутся из rawIdeas (первоисточник фазы 1): дедупликатор возвращает
// только имена и кластеры, поэтому переписать или «поглотить» формулировку
// он не может даже теоретически. Идея, чьё имя не вернулось, — удалена
// по жёсткому запрету.
const removed = rawIdeas.filter(h => !clustersByName.has(String(h.name))).map(h => h.name);
let ideas = rawIdeas
  .filter(h => clustersByName.has(String(h.name)))
  .map(h => ({ ...h, cluster: clustersByName.get(String(h.name)) }));
if (removed.length > 0) {
  log(`Удалено по жёсткому запрету: ${removed.length} — ${removed.join(', ')}.`);
}
if (ideas.length === 0) {
  log('ОШИБКА: разметка не вернула ни одной гипотезы. Завершаю.');
  throw new Error('No hypotheses after cluster marking');
}
const clusterSizes = ideas.reduce((acc, h) => { acc[h.cluster] = (acc[h.cluster] || 0) + 1; return acc; }, {});
const nClusters = Object.keys(clusterSizes).filter(c => c !== '0').length;
log(`После разметки: ${ideas.length} идей в ${nClusters} кластерах.`);

// Сохраняем промежуточный артефакт (Этап 1).
const ideasMd = `# Сырые гипотезы брэйншторма (после разметки кластеров)

Сгенерировано brainstorm-workflow.js, фаза 2. Ранжирования нет.
Идеи с одинаковым номером кластера имеют похожий механизм edge.

${ideas.map(h => `## ${h.name} [кластер ${h.cluster}]
- Суть: ${h.essence}
- Обходимый тупик: ${h.deadend || 'не указан'}
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

// Для идей из многоэлементных кластеров показываем критику соседние
// формулировки: пусть оценит, какая версия механизма сформулирована сильнее.
const clusterNote = (idea) => {
  const siblings = ideas.filter(h => h.cluster === idea.cluster && h.name !== idea.name);
  if (siblings.length === 0) return '';
  return `В кластере с этой идеей есть похожие формулировки: ${siblings.map(s => `«${s.name}» (${s.essence})`).join('; ')}.
Учти их при оценке: если одна из версий кластера сформулирована сильнее,
отметь это в rationale — но оценивай именно данную гипотезу.`;
};

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

Гипотеза:
Название: ${job.idea.name}
Суть: ${job.idea.essence}
Обходимый тупик: ${job.idea.deadend || 'не указан'}
Откуда edge: ${job.idea.edge_source}
Теги: ${job.idea.tags.join('; ')}
${clusterNote(job.idea)}

Выполни по порядку:
1. Новизна. Есть ли в ретроспективе (секции 2 и 4) идея с ТЕМ ЖЕ
   механизмом получения edge? Совпадение темы или слов недостаточно:
   переупаковка — только если совпадает, ОТКУДА берётся edge.
   Если переупаковка — verdict "убита", в rationale — точная цитата
   секции и что именно совпадает. Если механизм другой — идея нова,
   даже при похожей теме.
2. Атака. До трёх самых уязвимых мест (данные, стационарность, исполнение,
   размер выборки, происхождение edge).
3. Фальсификация. Спроектируй убивающий эксперимент: что проверить, метрика,
   конкретный порог/число, которое убивает идею. Эксперимент НЕ проводи.
   Если убивающий тест в рамках проекта не формулируется —
   falsifiable=false, в falsification — объяснение.
4. Происхождение edge. Слабый или отсутствующий механизм «кто платит» —
   добавь в массив tags элемент "спекуляция". Это снижает позицию,
   но не убивает.
5. Потенциал. Оцени potential от 1 до 5: правдоподобность устойчивого edge
   строго по полю «Откуда edge» и своим уязвимостям. 5 — механизм конкретен
   и устойчив, 1 — механизм не назван или явно неустойчив. Обоснуй одной
   фразой в potential_why.
6. Вердикт: "выживает" / "условно" / "убита". Если идея требует доработки,
   чтобы выжить — «условно» с указанием, чего не хватает.
   Убивай без сожаления: идея с неустранимым уязвимым местом не проходит.
   Не дополняй и не улучшай гипотезы.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"name": ${JSON.stringify(job.idea.name)},
 "novelty": {"duplicate_of": null, "retrospective_ref": "..."},
 "vulnerabilities": ["...", "..."],
 "falsification": {"test": "...", "metric": "...", "kill_threshold": "...", "cost": "часы/дни", "falsifiable": true},
 "potential": 3,
 "potential_why": "одна фраза",
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
  // Потенциал — среднее числовых оценок критиков (1–5); нет оценок — null.
  const pots = reviews.map(r => Number(r.potential)).filter(p => Number.isFinite(p) && p >= 1 && p <= 5);
  const potential = pots.length > 0 ? Math.round((pots.reduce((a, b) => a + b, 0) / pots.length) * 10) / 10 : null;
  return {
    ...idea,
    verdict,
    under_reviewed: reviews.length < MIN_REVIEWS,
    falsifiable,
    potential,
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

const mergedBlock = merged.map(m => `### ${m.name} [кластер ${m.cluster}]
Суть: ${m.essence}
Обходимый тупик: ${m.deadend || 'не указан'}
Откуда edge: ${m.edge_source}
Теги: ${m.tags.join('; ')}
Потенциал (среднее оценок критиков, 1–5): ${m.potential ?? 'нет оценок'}
Вердикт (по ${m.reviews.length} независимым рецензиям): ${m.verdict}${m.under_reviewed ? ' [недооценена: рецензий меньше минимума]' : ''}${m.falsifiable === false ? ' [нефальсифицируема]' : ''}
${m.reviews.map((r, k) => `Рецензия ${k + 1}: ${r.rationale || ''}
  Уязвимости: ${(r.vulnerabilities || []).join('; ')}
  Потенциал: ${r.potential ?? '—'} (${r.potential_why || 'без обоснования'})
  Фальсификация: ${r.falsification ? `${r.falsification.test} | метрика: ${r.falsification.metric} | убивает: ${r.falsification.kill_threshold} | стоимость: ${r.falsification.cost}` : 'не задана'}`).join('\n')}`).join('\n\n');

await agent(
  `Ты пишешь итоговый документ брэйншторма по результатам независимой
критики. Ниже — идеи с вердиктами. Ретроспективу перечитывать не нужно.

${mergedBlock}

Напиши файл docs/audit/brainstorm-filtered.md со структурой:

1. Короткий список выживших (вердикт «выживает», при нехватке — добирай из
   «условно»; всего не более 10), строго по убыванию поля «Потенциал».
   Своих оценок потенциала не выдумывай — используй только данные из блока.
   Для каждой: суть (1–2 предложения), обходимый тупик, убивающий
   эксперимент с метрикой и порогом, стоимость, потенциал,
   пометки [радикальная]/[спекуляция]/«условно».
   Идеи одного кластера не дублируй: выбирай версию с высшим потенциалом.
   [нефальсифицируема] — в конец списка с объяснением.
   Идеи с вердиктом «без рецензии» в короткий список НЕ включай —
   выведи их отдельным примечанием в конце документа.
2. Таблица-сводка: идея | вердикт | потенциал | обходимый тупик |
   убивающий результат | стоимость.
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
