export const meta = {
  name: 'brainstorm-workflow',
  description: 'Брэйншторм новых источников trading edge: 4 параллельных генератора гипотез по векторам поиска → разметка кластеров без слияния → спор «автор идеи × критик» на кластер (3 раунда, досрочный выход при признании фатального аргумента) → синтез-арбитр с правом только понижать вердикты → итоговый список в docs/audit/brainstorm-filtered.md.',
  phases: ['Генерация', 'Кластеры', 'Споры', 'Синтез-арбитр', 'Верификация'],
  // Контрактные ограничения:
  //   - Контекстное окно субагента ~150K. Основной вход каждого агента —
  //     docs/audit/retrospective.md (~2K слов), читается целиком.
  //   - knowledge-rag (search_knowledge) — только точечная проверка фактов;
  //     отчёты docs/reports/ и ML/reports/ целиком не читаются.
  //   - Спор идёт на кластер, не на идею: один представитель + заметка о
  //     соседях по кластеру. Раунды внутри пары последовательны, пары —
  //     параллельны. Каждый раунд — НОВЫЙ вызов агента с передачей всей
  //     предыдущей переписки пары в промпте (долгоживущих агентов нет).
  //   - Анти-сговор: вердикт меняется только под новые аргументы, а не под
  //     уверенность тона; досрочный выход — по признанию фатального
  //     аргумента автором, а не по «согласию сторон»; арбитр вправе только
  //     понижать вердикты критика, не повышать.
};

// Потолок числа кластеров, идущих в споры (стоимость = кластеры × 2–3 вызова).
const MAX_CLUSTERS = 20;

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

const ALLOWED_VERDICTS = ['выживает', 'условно', 'убита'];

// ═══════════════════════════════════════════════════════
// Фаза 1: Генерация (divergence)
// Параллельные генераторы по векторам поиска. Векторы пересекаются
// намеренно — пересечения размечает фаза кластеров.
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
// Фаза 2: Разметка кластеров
// Агент только нумерует кластеры похожих идей и удаляет нарушающие
// жёсткий запрет. Формулировки НЕ переписываются и НЕ сливаются:
// источник истины — rawIdeas, кластер лишь группирует.
// ═══════════════════════════════════════════════════════

phase('Кластеры');

const rawBlock = rawIdeas
  .map((h, i) => `${i + 1}. ${h.name}
Суть: ${h.essence}
Тупик: ${h.deadend || 'не указан'}
Источник edge: ${h.edge_source}
Теги: ${Array.isArray(h.tags) ? h.tags.join('; ') : ''}`)
  .join('\n\n');

const clusterRaw = await agent(
  `Ниже — сырые гипотезы о новых источниках trading edge, собранные
${vectors.length} независимыми генераторами (с пересекающимися векторами).
Ретроспективу перечитывать не нужно.

${rawBlock}

Твоя задача — ТОЛЬКО разметка, без переписывания:
1. Разбей гипотезы на кластеры по совпадению механизма edge (кто платит и
   почему эффект устойчив) — даже при разной упаковке. Близкие по теме,
   но разные по механизму идеи — разные кластеры. Одиночные идеи получают
   свой кластер.
2. Удали идеи, нарушающие жёсткий запрет: классические индикаторы
   (RSI, MACD, скользящие средние и т.п.) и прочие примитивные отжившие
   методы. Больше не удаляй ничего: новизну проверяет спор.
3. Названия гипотез верни ДОСЛОВНО, как в списке — по ним идёт связка.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"items": [{"name": "...", "cluster": 1}], "removed": [{"name": "...", "reason": "..."}]}`,
  { phase: 'Кластеры', label: 'Разметка кластеров' }
);

let clusterMap, removedByAgent;
try {
  const parsed = parseJson(clusterRaw, 'Разметка кластеров');
  clusterMap = new Map(
    (Array.isArray(parsed.items) ? parsed.items : [])
      .filter(it => it && it.name && Number.isFinite(Number(it.cluster)))
      .map(it => [String(it.name), Number(it.cluster)])
  );
  removedByAgent = Array.isArray(parsed.removed) ? parsed.removed : [];
} catch (e) {
  log('ОШИБКА: ' + e.message + '. Завершаю.');
  throw e;
}
if (clusterMap.size === 0) {
  log('ОШИБКА: разметка не вернула ни одной гипотезы. Завершаю.');
  throw new Error('No ideas after cluster marking');
}
if (removedByAgent.length > 0) {
  log(`Жёсткий запрет: удалено ${removedByAgent.length} — ${removedByAgent.map(r => r.name).join(', ')}.`);
}

// Источник истины — rawIdeas: формулировки не могли быть поглощены при слиянии.
const droppedByMarking = rawIdeas.filter(h => !clusterMap.has(String(h.name))).map(h => h.name);
if (droppedByMarking.length > 0) {
  log(`Внимание: разметка потеряла ${droppedByMarking.length} идей: ${droppedByMarking.join(', ')}.`);
}
let ideas = rawIdeas
  .filter(h => clusterMap.has(String(h.name)))
  .map(h => ({ ...h, cluster: clusterMap.get(String(h.name)) }));

// Группировка по кластерам с сохранением порядка появления.
const clusters = [];
const clusterById = new Map();
ideas.forEach(h => {
  if (!clusterById.has(h.cluster)) {
    const c = { id: h.cluster, members: [] };
    clusterById.set(h.cluster, c);
    clusters.push(c);
  }
  clusterById.get(h.cluster).members.push(h);
});

// Сохраняем промежуточный артефакт (все идеи, с номерами кластеров).
const ideasMd = `# Сырые гипотезы брэйншторма (разметка кластеров)

Сгенерировано brainstorm-workflow.js, фаза 2. Ранжирования нет.
Один кластер = один механизм edge.

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
  { phase: 'Кластеры', label: 'Запись brainstorm-ideas.md' }
);

// Потолок числа кластеров для фазы споров. Отброшенные уходят в лог И в
// протокол арбитра — не должны исчезать молча из итогового документа.
let droppedClusters = [];
if (clusters.length > MAX_CLUSTERS) {
  droppedClusters = clusters.slice(MAX_CLUSTERS).map(c => c.members[0].name + (c.members.length > 1 ? ` (+${c.members.length - 1})` : ''));
  clusters.length = MAX_CLUSTERS;
  log(`Потолок ${MAX_CLUSTERS} кластеров: отброшено ${droppedClusters.length} — ${droppedClusters.join(', ')}.`);
}
log(`Кластеров в спор: ${clusters.length}.`);

// ═══════════════════════════════════════════════════════
// Фаза 3: Споры (автор идеи × критик, на кластер)
// Раунд 1 — критик атакует. Раунд 2 — автор защищает или признаёт
// фатальный аргумент (досрочный выход: «убита»). Раунд 3 — критик
// подводит черту: конспект «за и против» + финальный вердикт для арбитра.
// Пары параллельны; раунды внутри пары последовательны.
// ═══════════════════════════════════════════════════════

phase('Споры');

const clusterNote = (c) => {
  if (c.members.length < 2) return '';
  const others = c.members.slice(1).map(m => `«${m.name}»: ${m.essence}`).join('\n');
  return `В этом же кластере (тот же механизм edge) есть близкие идеи — спор
ведётся по самой полной формулировке, но вердикт распространяется на весь кластер:
${others}
`;
};

const ideaBlock = (h) => `Название: ${h.name}
Суть: ${h.essence}
Обходимый тупик: ${h.deadend || 'не указан'}
Откуда edge: ${h.edge_source}
Теги: ${Array.isArray(h.tags) ? h.tags.join('; ') : ''}`;

log(`Запускаю ${clusters.length} споров параллельно (до 3 вызовов на пару)...`);

const debateResults = await parallel(
  clusters.map(c => async () => {
    const rep = c.members[0];

    // Раунд 1: критик атакует.
    const attackRaw = await agent(
      `Ты — критически настроенный рецензент количественных исследований.
Твоя задача — атаковать гипотезу и найти её слабые места. Не защищай идею
и не ищи ей оправданий. Это раунд 1 спора: после твоей атаки автор идеи
получит слово, затем ты подведёшь черту.

Контекст: проект SoSimple (Forex, personal research). Порог успеха:
PF ≥ 1.3 на строгом out-of-sample с bootstrap CI (нижняя граница > 1.0).
За ~6 месяцев ни одна система его не прошла.

Вход: прочитай docs/audit/retrospective.md ЦЕЛИКОМ. База проверки новизны —
секция 2 (пройденные направления) и секция 4 (что не работает).
knowledge-rag (search_knowledge) — только точечная проверка фактов,
если гипотеза ссылается на результат, которого нет в ретроспективе.

${clusterNote(c)}
Гипотеза:
${ideaBlock(rep)}

Выполни по порядку:
1. Новизна. Найди в ретроспективе (секции 2 и 4) эту идею или аналог с ТЕМ ЖЕ
   механизмом edge. Совпадение темы или слов — НЕ доказательство: нужна
   точная цитата из секции, описывающая тот же механизм. Если аналог есть —
   preliminary_verdict "убита", в retrospective_ref — секция и цитата.
2. Атака. До трёх самых уязвимых мест (данные, стационарность, исполнение,
   размер выборки, происхождение edge).
3. Фальсификация. Спроектируй убивающий эксперимент: что проверить, метрика,
   конкретный порог/число, которое убивает идею, стоимость (часы/дни).
   Эксперимент НЕ проводи. Если убивающий тест в рамках проекта не
   формулируется — falsifiable=false с объяснением.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"novelty": {"duplicate_of": null, "retrospective_ref": null},
 "vulnerabilities": ["...", "..."],
 "falsification": {"test": "...", "metric": "...", "kill_threshold": "...", "cost": "часы/дни", "falsifiable": true},
 "preliminary_verdict": "выживает|условно|убита"}`,
      { phase: 'Споры', label: `${rep.name} — атака` }
    );

    let attack;
    try {
      attack = parseJson(attackRaw, `Критик «${rep.name}», раунд 1`);
    } catch (e) {
      log(`Спор «${rep.name}» не состоялся (раунд 1): ` + e.message);
      return { cluster: c.id, idea: rep, members: c.members, status: 'no_debate' };
    }

    // Раунд 2: автор защищает или признаёт фатальный аргумент.
    const defenseRaw = await agent(
      `Ты — автор гипотезы ниже. Критик её атаковал. Твоя задача — честная
защита по существу, НЕ защита любой ценой.

Гипотеза:
${ideaBlock(rep)}

Атака критика:
Новизна: ${JSON.stringify(attack.novelty || null)}
Уязвимости: ${JSON.stringify(attack.vulnerabilities || [])}
Фальсификация: ${JSON.stringify(attack.falsification || null)}
Предварительный вердикт: ${attack.preliminary_verdict || 'не указан'}

Правила:
- Отвечай на каждый аргумент по существу. Не пересказывай суть идеи заново.
- Если аргумент критика фатален и неустраним (например, точная цитата из
  ретроспективы о том же механизме edge) — признай это явно: concession=true
  и укажи, какой именно аргумент принят. Честное признание ценнее плохой защиты.
- Если критик ссылается на секцию ретроспективы, можешь прочесть эту секцию
  в docs/audit/retrospective.md, чтобы проверить цитату.
- Слабый механизм «кто платит» допустимо признать и уточнить, это не фатально.
- Не выдавай предположения за факты; спекуляции помечай [гипотеза].
- Ответ — до 200 слов.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"concession": false, "accepted_arguments": [], "defense": "..."}`,
      { phase: 'Споры', label: `${rep.name} — защита` }
    );

    let defense;
    try {
      defense = parseJson(defenseRaw, `Автор «${rep.name}», раунд 2`);
    } catch (e) {
      // Защита не распарсилась — передаём критику сырой текст, спор не рвём.
      log(`Защита «${rep.name}» не распарсилась: ` + e.message);
      defense = {
        concession: false,
        accepted_arguments: [],
        defense: '(технический сбой: ответ автора не распарсен или отсутствует) ' + normalizeResult(defenseRaw),
      };
    }

    // Досрочный выход: автор признал фатальный аргумент — раунд 3 не нужен.
    if (defense.concession === true) {
      return {
        cluster: c.id, idea: rep, members: c.members, status: 'conceded',
        attack, defense,
        final: {
          verdict: 'убита',
          rationale: 'Автор признал фатальный аргумент критика: ' +
            (Array.isArray(defense.accepted_arguments) ? defense.accepted_arguments.join('; ') : defense.defense || ''),
          vulnerabilities: attack.vulnerabilities || [],
          falsification: attack.falsification || null,
          novelty: attack.novelty || null,
          potential: null, potential_why: null,
        },
      };
    }

    // Раунд 3: критик подводит черту — конспект «за и против» для арбитра.
    const finalRaw = await agent(
      `Ты — тот же критик из раунда 1 (твоя атака воспроизведена ниже). Автор
идеи ответил на атаку. Подведи черту спора: составь конспект «за и против»
и вынеси финальный вердикт для независимого арбитра.

Гипотеза:
${ideaBlock(rep)}

Твоя атака (раунд 1):
${JSON.stringify(attack)}

Ответ автора (раунд 2):
${JSON.stringify(defense)}

Правила:
- Вердикт меняется ТОЛЬКО под новые факты и аргументы из ответа автора —
  не под уверенность тона и не потому, что автор возражает. Если защита не
  добавила ничего содержательного — сохрани предварительный вердикт.
- Не дополняй и не улучшай гипотезу.
- Уточни фальсификацию, если защита дала новые данные; иначе оставь свою.
- Потенциал (1–5): правдоподобие устойчивого edge ТОЛЬКО по механизму
  «кто платит» (поле edge_source) и результатам спора; не выдумывай числа,
  которых нет в материалах.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"name": ${JSON.stringify(rep.name)},
 "pros": ["..."],
 "cons": ["..."],
 "novelty": {"duplicate_of": null, "retrospective_ref": null},
 "vulnerabilities": ["...", "..."],
 "falsification": {"test": "...", "metric": "...", "kill_threshold": "...", "cost": "часы/дни", "falsifiable": true},
 "potential": 1,
 "potential_why": "одно предложение",
 "verdict": "выживает|условно|убита",
 "rationale": "одно предложение"}`,
      { phase: 'Споры', label: `${rep.name} — итог критика` }
    );

    let final;
    try {
      final = parseJson(finalRaw, `Критик «${rep.name}», раунд 3`);
      if (!ALLOWED_VERDICTS.includes(String(final.verdict))) {
        throw new Error(`вердикт вне тройки: ${final.verdict}`);
      }
    } catch (e) {
      log(`Спор «${rep.name}» завершён без финала (раунд 3): ` + e.message);
      return { cluster: c.id, idea: rep, members: c.members, status: 'no_debate', attack, defense };
    }

    return { cluster: c.id, idea: rep, members: c.members, status: 'debated', attack, defense, final };
  })
);

// Сборка результатов: связка по индексу, статусы спора.
const debates = [];
const noDebates = [];
debateResults.forEach((d, i) => {
  if (d == null) {
    noDebates.push(clusters[i].members[0].name);
    debates.push({ cluster: clusters[i].id, idea: clusters[i].members[0], members: clusters[i].members, status: 'no_debate' });
    return;
  }
  debates.push(d);
});
if (noDebates.length > 0) {
  log(`Внимание: без полного спора: ${noDebates.join(', ')}.`);
}

const verdictRank = { 'выживает': 0, 'условно': 1, 'убита': 2, 'без спора': 3 };
const merged = debates.map(d => {
  const verdict = d.final && ALLOWED_VERDICTS.includes(String(d.final.verdict))
    ? String(d.final.verdict)
    : 'без спора';
  const pot = d.final ? Number(d.final.potential) : NaN;
  return {
    ...d.idea,
    cluster: d.cluster,
    cluster_size: d.members.length,
    verdict,
    potential: Number.isFinite(pot) && pot >= 1 && pot <= 5 ? pot : null,
    potential_why: d.final ? d.final.potential_why || null : null,
    falsifiable: d.final && d.final.falsification
      ? d.final.falsification.falsifiable !== false
      : false,
    debate: d,
  };
}).sort((a, b) => (verdictRank[a.verdict] ?? 3) - (verdictRank[b.verdict] ?? 3));

const counts = { выживает: 0, условно: 0, убита: 0, 'без спора': 0 };
merged.forEach(m => { counts[m.verdict] = (counts[m.verdict] || 0) + 1; });
log(`Вердикты споров: выживает ${counts['выживает']}, условно ${counts['условно']}, убита ${counts['убита']}, без спора ${counts['без спора']}.`);

// ═══════════════════════════════════════════════════════
// Фаза 4: Синтез-арбитр
// Читает протоколы споров и секции 2/4 ретроспективы; вправе только
// ПОНИЖАТЬ вердикты критиков. Пишет итоговый документ.
// ═══════════════════════════════════════════════════════

phase('Синтез-арбитр');

const fmtFals = (f) => f
  ? `${f.test} | метрика: ${f.metric} | убивает: ${f.kill_threshold} | стоимость: ${f.cost}${f.falsifiable === false ? ' [нефальсифицируема]' : ''}`
  : 'не задана';

const protocolBlock = merged.map(m => {
  const d = m.debate;
  const head = `### ${m.name} [кластер ${m.cluster}${m.cluster_size > 1 ? `, идей в кластере: ${m.cluster_size}` : ''}]
${ideaBlock(m)}
Вердикт критика: ${m.verdict}${m.potential != null ? ` | потенциал: ${m.potential}/5 (${m.potential_why || 'без обоснования'})` : ''}`;
  if (d.status === 'no_debate') {
    return head + '\nСПОР НЕ СОСТОЯЛСЯ (ошибка агента). Вердикт: без спора.';
  }
  const parts = [head,
    `Раунд 1 (атака критика):
  Новизна: ${d.attack && d.attack.novelty ? `аналог: ${d.attack.novelty.duplicate_of || 'не найден'}; ссылка: ${d.attack.novelty.retrospective_ref || 'нет'}` : 'не задана'}
  Уязвимости: ${d.attack && Array.isArray(d.attack.vulnerabilities) ? d.attack.vulnerabilities.join('; ') : '—'}
  Фальсификация: ${fmtFals(d.attack && d.attack.falsification)}
  Предварительный вердикт: ${(d.attack && d.attack.preliminary_verdict) || '—'}`,
    d.status === 'conceded'
      ? `Раунд 2 (автор): ПРИЗНАЛ фатальный аргумент — ${Array.isArray(d.defense.accepted_arguments) ? d.defense.accepted_arguments.join('; ') : d.defense.defense || ''}. Спор остановлен досрочно.`
      : `Раунд 2 (защита автора): ${d.defense.defense || '—'}`,
  ];
  if (d.status === 'debated' && d.final) {
    parts.push(`Раунд 3 (конспект критика):
  За: ${Array.isArray(d.final.pros) ? d.final.pros.join('; ') : '—'}
  Против: ${Array.isArray(d.final.cons) ? d.final.cons.join('; ') : '—'}
  Итог: ${d.final.rationale || ''}`);
  }
  return parts.join('\n');
}).join('\n\n');

await agent(
  `Ты — арбитр брэйншторма. Ниже — протоколы споров «автор идеи × критик».

Вход:
1. Протоколы споров:
${protocolBlock}

2. Прочитай в docs/audit/retrospective.md секции 2 и 4 — первоисточник для
   проверки «убита за переупаковку»: цитата критика должна реально
   описывать тот же механизм edge.
${droppedClusters.length > 0 ? `
3. Кластеры, НЕ ОЦЕНЁННЫЕ из-за потолка стоимости (спор по ним не проводился):
${droppedClusters.join('; ')}
` : ''}
Полномочия арбитра:
- Ты вправе ПОНИЗИТЬ вердикт критика («выживает» → «условно» → «убита»),
  если конспект спора или ретроспектива показывают, что критик был мягок.
- ПОВЫШАТЬ вердикты запрещено: если критик убил идею, она остаётся убитой.
- Своих оценок потенциала не выдумывай — используй числа критиков как есть.
- Записи со статусом «без спора» — технический сбой агента, а не свойство
  идеи: не помечай их [нефальсифицируема] и не выноси по ним суждений.

Напиши файл docs/audit/brainstorm-filtered.md со структурой:
1. Короткий список выживших (вердикт «выживает», при нехватке — добирай из
   «условно»; всего не более 10), строго по убыванию потенциала.
   Для каждой: суть (1–2 предложения), обходимый тупик, убивающий
   эксперимент с метрикой и порогом, стоимость, потенциал,
   пометки [радикальная]/[спекуляция]/«условно».
   Одна идея на кластер: если в итог попали несколько идей одного кластера —
   оставь версию с высшим потенциалом.
   [нефальсифицируема] — в конец списка с объяснением.
   Идеи со статусом «без спора» в короткий список НЕ включай — выведи их
   отдельным примечанием в конце документа; туда же добавь кластеры,
   не оценённые из-за потолка стоимости, с пометкой «не оценивались».
2. Таблица-сводка: идея | вердикт | потенциал | обходимый тупик |
   убивающий результат | стоимость.
3. Список убитых: идея | причина | ссылка на секцию ретроспективы,
   если убита за переупаковку; «автор признал аргумент» — если досрочно.
4. Если ты понизил чей-то вердикт — перечисли эти случаи отдельной строкой
   с обоснованием.

Правила:
- Не улучшай, не дополняй и не воскрешай убитые идеи.
- Числа и цитаты из протоколов не выдумывай заново — используй как есть.
- Спекуляции помечай [гипотеза].

Используй инструмент Write. После записи НЕ выводи содержимое файла —
сообщи только: сколько идей выжило, условно, убито, понижено арбитром —
и топ-3 выживших кратким списком.`,
  { phase: 'Синтез-арбитр', label: 'Итоговый документ' }
);

// ═══════════════════════════════════════════════════════
// Фаза 5: Верификация
// Дешёвый assert: итоговый файл реально записан и не пуст.
// ═══════════════════════════════════════════════════════

phase('Верификация');

const verifyResult = await agent(
  `Проверь результат брэйншторма. Используй bash:
ls -l docs/audit/brainstorm-filtered.md docs/audit/brainstorm-ideas.md
wc -w docs/audit/brainstorm-filtered.md docs/audit/brainstorm-ideas.md
grep -ci "таблица-сводка" docs/audit/brainstorm-filtered.md
Если хотя бы один файл отсутствует, brainstorm-filtered.md содержит меньше
150 слов, или grep вернул 0 (нет раздела «Таблица-сводка») — ответь СТРОГО:
"ABORT: <причина>". Иначе ответь СТРОГО:
"OK: filtered <число> слов, ideas <число> слов".`,
  { phase: 'Верификация', label: 'Assert итоговых файлов' }
);

if (/^ABORT:/i.test(normalizeResult(verifyResult).trim())) {
  log('ОШИБКА: верификация прервана — ' + normalizeResult(verifyResult).slice(0, 200));
  throw new Error('Verification aborted: ' + normalizeResult(verifyResult).slice(0, 200));
}

log('Брэйншторм завершён: docs/audit/brainstorm-filtered.md');
