export const meta = {
  name: 'idea-check',
  description: 'Часть 2 брэйншторма: читает docs/audit/brainstorm-raw.json (результат idea-brainstorm) → фильтр жёсткого запрета → спор «автор идеи × критик» на каждую гипотезу (3 раунда, досрочный выход при признании фатального аргумента) → синтез-арбитр с правом только понижать вердикты → итоговый список в docs/audit/brainstorm-filtered.md. Запускать на дешёвой модели.',
  phases: ['Чтение входа', 'Фильтр', 'Споры', 'Синтез-арбитр', 'Верификация'],
  // Контрактные ограничения:
  //   - Контекстное окно субагента ~150K. Основной вход каждого агента —
  //     docs/audit/retrospective.md (~2K слов), читается целиком.
  //   - knowledge-rag (search_knowledge) — только точечная проверка фактов;
  //     отчёты docs/reports/ и ML/reports/ целиком не читаются.
  //   - Вход — файл docs/audit/brainstorm-raw.json от части 1; скрипт можно
  //     запускать в другой среде (например, opencode), если там доступен
  //     тот же рантайм оркестрации.
  //   - Кластеризации нет: каждая гипотеза спорится индивидуально — итог не
  //     зависит от случайного слияния идей в группы. Раунды внутри пары
  //     последовательны, пары — параллельны. Каждый раунд — НОВЫЙ вызов
  //     агента с передачей всей предыдущей переписки пары в промпте
  //     (долгоживущих агентов нет).
  //   - Анти-сговор: вердикт меняется только под новые аргументы, а не под
  //     уверенность тона; досрочный выход — по признанию фатального
  //     аргумента автором ПРИ предварительном вердикте критика «убита»
  //     (иначе обязателен раунд 3 — защита от послушных уступок модели-автора),
  //     а не по «согласию сторон»; арбитр вправе только понижать вердикты
  //     критика, не повышать.
};

// Потолок числа гипотез, идущих в споры (стоимость = гипотезы × 2–3 вызова).
const MAX_IDEAS = 30;

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
// Фаза 1: Чтение входа от части 1
// ═══════════════════════════════════════════════════════

phase('Чтение входа');

const rawRead = await agent(
  `Прочитай файл docs/audit/brainstorm-raw.json (инструмент Read). Это сырые
гипотезы, подготовленные первой частью брэйншторма. Ничего не редактируй,
не дополняй и не переформулируй. Если файл отсутствует — ответь СТРОГО:
"ABORT: файл docs/audit/brainstorm-raw.json отсутствует, сначала запустите idea-brainstorm".
Иначе ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"hypotheses": [{"name":"...","essence":"...","deadend":"...","edge_source":"...","tags":[]}]}`,
  { phase: 'Чтение входа', label: 'Чтение brainstorm-raw.json' }
);

if (/^ABORT:/i.test(normalizeResult(rawRead).trim())) {
  log('ОШИБКА: ' + normalizeResult(rawRead).slice(0, 200));
  throw new Error('Input missing: brainstorm-raw.json');
}

let parsedRaw;
try {
  parsedRaw = parseJson(rawRead, 'Чтение brainstorm-raw.json');
} catch (e) {
  log('ОШИБКА: ' + e.message + '. Завершаю.');
  throw e;
}
const rawIdeas = (Array.isArray(parsedRaw.hypotheses) ? parsedRaw.hypotheses : [])
  .filter(h => h && h.name && h.essence)
  .map(h => ({ ...h, tags: Array.isArray(h.tags) ? h.tags : [] }));
if (rawIdeas.length === 0) {
  log('ОШИБКА: во входном файле нет гипотез. Завершаю.');
  throw new Error('No hypotheses in brainstorm-raw.json');
}
log(`Загружено гипотез: ${rawIdeas.length}.`);

// ═══════════════════════════════════════════════════════
// Фаза 2: Фильтр жёсткого запрета
// Агент только удаляет идеи, нарушающие жёсткий запрет (классические
// индикаторы и примитивные отжившие методы). Формулировки НЕ
// переписываются: источник истины — rawIdeas. Кластеризации нет —
// каждая гипотеза дальше спорится индивидуально.
// ═══════════════════════════════════════════════════════

phase('Фильтр');

const rawBlock = rawIdeas
  .map((h, i) => `${i + 1}. ${h.name}
Суть: ${h.essence}
Тупик: ${h.deadend || 'не указан'}
Источник edge: ${h.edge_source}
Теги: ${Array.isArray(h.tags) ? h.tags.join('; ') : ''}`)
  .join('\n\n');

const filterRaw = await agent(
  `Ниже — сырые гипотезы о новых источниках trading edge, собранные
независимыми генераторами (с пересекающимися векторами).
Ретроспективу перечитывать не нужно.

${rawBlock}

Твоя задача — ТОЛЬКО фильтрация, без переписывания:
1. Удали идеи, нарушающие жёсткий запрет: классические индикаторы
   (RSI, MACD, скользящие средние и т.п.) и прочие примитивные отжившие
   методы; идеи, где торговые решения принимаются на таймфреймах ниже M5
   или требуются стакан/латентностные техники (тики допустимы только в
   роли симуляции исполнения и диагностик); идеи на макроэкономических
   показателях и событиях (ставки, экономический календарь).
2. Названия гипотез верни ДОСЛОВНО, как в списке — по ним идёт связка.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"kept": ["..."], "removed": [{"name": "...", "reason": "..."}]}`,
  { phase: 'Фильтр', label: 'Фильтр жёсткого запрета' }
);

let keptNames, removedByAgent;
try {
  const parsed = parseJson(filterRaw, 'Фильтр жёсткого запрета');
  keptNames = new Set(
    (Array.isArray(parsed.kept) ? parsed.kept : [])
      .filter(n => typeof n === 'string')
      .map(String)
  );
  removedByAgent = Array.isArray(parsed.removed) ? parsed.removed : [];
} catch (e) {
  log('ОШИБКА: ' + e.message + '. Завершаю.');
  throw e;
}
if (keptNames.size === 0) {
  log('ОШИБКА: фильтр не вернул ни одной гипотезы. Завершаю.');
  throw new Error('No ideas after hard-ban filter');
}
if (removedByAgent.length > 0) {
  log(`Жёсткий запрет: удалено ${removedByAgent.length} — ${removedByAgent.map(r => r.name).join(', ')}.`);
}

const droppedByFilter = rawIdeas.filter(h => !keptNames.has(String(h.name))).map(h => h.name);
if (droppedByFilter.length > removedByAgent.length) {
  const lost = droppedByFilter.filter(n => !removedByAgent.some(r => r.name === n));
  if (lost.length > 0) {
    log(`Внимание: фильтр потерял ${lost.length} идей: ${lost.join(', ')}.`);
  }
}
const ideas = rawIdeas.filter(h => keptNames.has(String(h.name)));

// Потолок числа гипотез для фазы споров. Отброшенные уходят в лог И в
// протокол арбитра — не должны исчезать молча из итогового документа.
let droppedIdeas = [];
if (ideas.length > MAX_IDEAS) {
  droppedIdeas = ideas.slice(MAX_IDEAS).map(h => h.name);
  ideas.length = MAX_IDEAS;
  log(`Потолок ${MAX_IDEAS} гипотез: отброшено ${droppedIdeas.length} — ${droppedIdeas.join(', ')}.`);
}
log(`Гипотез в спор: ${ideas.length}.`);

// ═══════════════════════════════════════════════════════
// Фаза 3: Споры (автор идеи × критик, на каждую гипотезу)
// Раунд 1 — критик атакует. Раунд 2 — автор защищает или признаёт
// фатальный аргумент (досрочный выход «убита» — только если предварительный
// вердикт критика тоже «убита»). Раунд 3 — критик подводит черту: конспект
// «за и против» + финальный вердикт для арбитра.
// Пары параллельны; раунды внутри пары последовательны.
// ═══════════════════════════════════════════════════════

phase('Споры');

const ideaBlock = (h) => `Название: ${h.name}
Суть: ${h.essence}
Обходимый тупик: ${h.deadend || 'не указан'}
Откуда edge: ${h.edge_source}
Теги: ${Array.isArray(h.tags) ? h.tags.join('; ') : ''}`;

log(`Запускаю ${ideas.length} споров параллельно (до 3 вызовов на пару)...`);

const debateResults = await parallel(
  ideas.map(idea => async () => {
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

Гипотеза:
${ideaBlock(idea)}

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
      { phase: 'Споры', label: `${idea.name} — атака` }
    );

    let attack;
    try {
      attack = parseJson(attackRaw, `Критик «${idea.name}», раунд 1`);
    } catch (e) {
      log(`Спор «${idea.name}» не состоялся (раунд 1): ` + e.message);
      return { idea, status: 'no_debate' };
    }

    // Раунд 2: автор защищает или признаёт фатальный аргумент.
    const defenseRaw = await agent(
      `Ты — автор гипотезы ниже. Критик её атаковал. Твоя задача — честная
защита по существу, НЕ защита любой ценой.

Гипотеза:
${ideaBlock(idea)}

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
- Если критик привёл аналог из ретроспективы — явно назови, какое ограничение
  убило аналог, есть ли оно в твоей версии, и какой заранее зафиксированный
  тест провалится, если оно живо. Если ограничение то же самое — признай.
- Слабый механизм «кто платит» допустимо признать и уточнить, это не фатально.
- Не выдавай предположения за факты; спекуляции помечай [гипотеза].
- Ответ — до 200 слов.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"concession": false, "accepted_arguments": [], "defense": "..."}`,
      { phase: 'Споры', label: `${idea.name} — защита` }
    );

    let defense;
    try {
      defense = parseJson(defenseRaw, `Автор «${idea.name}», раунд 2`);
    } catch (e) {
      // Защита не распарсилась — передаём критику сырой текст, спор не рвём.
      log(`Защита «${idea.name}» не распарсилась: ` + e.message);
      defense = {
        concession: false,
        accepted_arguments: [],
        defense: '(технический сбой: ответ автора не распарсен или отсутствует) ' + normalizeResult(defenseRaw),
      };
    }

    // Досрочный выход: автор признал фатальный аргумент, И критик в раунде 1
    // сам счёл идею убитой. Если предварительный вердикт мягче, уступка не
    // убивает идею автоматически — раунд 3 обязателен: критик решает,
    // действительно ли признанный аргумент фатален (защита от послушных
    // уступок модели-автора, убивающих идею строже, чем её атакующий).
    if (defense.concession === true && attack.preliminary_verdict === 'убита') {
      return {
        idea, status: 'conceded',
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
${ideaBlock(idea)}

Твоя атака (раунд 1):
${JSON.stringify(attack)}

Ответ автора (раунд 2):
${JSON.stringify(defense)}

Правила:
- Вердикт меняется ТОЛЬКО под новые факты и аргументы из ответа автора —
  не под уверенность тона и не потому, что автор возражает. Если защита не
  добавила ничего содержательного — сохрани предварительный вердикт.
- Если автор признал аргумент (concession=true), но твой предварительный
  вердикт не был «убита» — реши по существу, действительно ли признанный
  аргумент фатален для идеи. Само по себе признание автора не обязывает
  убивать идею, если ты в раунде 1 не счёл её убитой.
- Не дополняй и не улучшай гипотезу.
- Уточни фальсификацию, если защита дала новые данные; иначе оставь свою.
- Потенциал (1–5): правдоподобие устойчивого edge ТОЛЬКО по механизму
  «кто платит» (поле edge_source) и результатам спора; не выдумывай числа,
  которых нет в материалах.

Ответь ИСКЛЮЧИТЕЛЬНО валидным JSON без markdown-обёртки:
{"name": ${JSON.stringify(idea.name)},
 "pros": ["..."],
 "cons": ["..."],
 "novelty": {"duplicate_of": null, "retrospective_ref": null},
 "vulnerabilities": ["...", "..."],
 "falsification": {"test": "...", "metric": "...", "kill_threshold": "...", "cost": "часы/дни", "falsifiable": true},
 "potential": 1,
 "potential_why": "одно предложение",
 "verdict": "выживает|условно|убита",
 "rationale": "одно предложение"}`,
      { phase: 'Споры', label: `${idea.name} — итог критика` }
    );

    let final;
    try {
      final = parseJson(finalRaw, `Критик «${idea.name}», раунд 3`);
      if (!ALLOWED_VERDICTS.includes(String(final.verdict))) {
        throw new Error(`вердикт вне тройки: ${final.verdict}`);
      }
    } catch (e) {
      log(`Спор «${idea.name}» завершён без финала (раунд 3): ` + e.message);
      return { idea, status: 'no_debate', attack, defense };
    }

    return { idea, status: 'debated', attack, defense, final };
  })
);

// Сборка результатов: связка по индексу, статусы спора.
const debates = [];
const noDebates = [];
debateResults.forEach((d, i) => {
  if (d == null) {
    noDebates.push(ideas[i].name);
    debates.push({ idea: ideas[i], status: 'no_debate' });
    return;
  }
  debates.push(d);
});
if (noDebates.length > 0) {
  log(`Внимание: без полного спора: ${noDebates.join(', ')}.`);
}

// Полные протоколы споров — отдельный артефакт: аудит вердиктов и поведения
// агентов «автор»/«критик» без выкапывания переписки из чата.
const debateStatusLine = {
  debated: 'полный спор (3 раунда)',
  conceded: 'досрочный выход: автор признал фатальный аргумент (предварительный вердикт критика «убита»)',
  no_debate: 'спор не состоялся (технический сбой агента)',
};
const protocolsMd = `# Протоколы споров брэйншторма

Сгенерировано idea_check.js, фаза споров. Ответы агентов по раундам — дословно (JSON).

${debates.map(d => `## ${d.idea.name}
Статус: ${debateStatusLine[d.status] || d.status}

Блок идеи:
${ideaBlock(d.idea)}

Раунд 1 — атака критика:
${d.attack ? JSON.stringify(d.attack, null, 2) : '(нет — сбой агента)'}

Раунд 2 — ответ автора:
${d.defense ? JSON.stringify(d.defense, null, 2) : '(нет — спор не дошёл до раунда 2)'}

Раунд 3 — итог критика:
${d.status === 'conceded'
    ? `(пропущен — досрочный выход). Итог досрочного выхода: ${JSON.stringify(d.final, null, 2)}`
    : (d.final ? JSON.stringify(d.final, null, 2) : '(нет — сбой агента)')}
`).join('\n')}`;

await agent(
  `Запиши приведённый ниже текст КАК ЕСТЬ в файл docs/audit/brainstorm-protocols.md
через инструмент Write. Ничего не добавляй и не редактируй. В ответе сообщи
только: «записано, N слов».

${protocolsMd}`,
  { phase: 'Споры', label: 'Запись brainstorm-protocols.md' }
);

const verdictRank = { 'выживает': 0, 'условно': 1, 'убита': 2, 'без спора': 3 };
const merged = debates.map(d => {
  const verdict = d.final && ALLOWED_VERDICTS.includes(String(d.final.verdict))
    ? String(d.final.verdict)
    : 'без спора';
  const pot = d.final ? Number(d.final.potential) : NaN;
  return {
    ...d.idea,
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
  const head = `### ${m.name}
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
      : `Раунд 2 (защита автора): ${d.defense.concession === true ? `ПРИЗНАЛ аргумент (${Array.isArray(d.defense.accepted_arguments) ? d.defense.accepted_arguments.join('; ') : 'без списка'}), но предварительный вердикт критика не «убита» — спор продолжен. ` : ''}${d.defense.defense || '—'}`,
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
${droppedIdeas.length > 0 ? `
3. Идеи, НЕ ОЦЕНЁННЫЕ из-за потолка стоимости (спор по ним не проводился):
${droppedIdeas.join('; ')}
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
   [нефальсифицируема] — в конец списка с объяснением.
   Идеи со статусом «без спора» в короткий список НЕ включай — выведи их
   отдельным примечанием в конце документа; туда же добавь идеи,
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
// Дешёвый assert: итоговые файлы реально записаны и не пусты.
// ═══════════════════════════════════════════════════════

phase('Верификация');

const verifyResult = await agent(
  `Проверь результат брэйншторма. Используй bash:
ls -l docs/audit/brainstorm-filtered.md docs/audit/brainstorm-protocols.md
wc -w docs/audit/brainstorm-filtered.md docs/audit/brainstorm-protocols.md
grep -ci "таблица-сводка" docs/audit/brainstorm-filtered.md
Если хотя бы один файл отсутствует, brainstorm-filtered.md содержит меньше
150 слов, или grep вернул 0 (нет раздела «Таблица-сводка») — ответь СТРОГО:
"ABORT: <причина>". Иначе ответь СТРОГО:
"OK: filtered <число> слов, protocols <число> слов".`,
  { phase: 'Верификация', label: 'Assert итоговых файлов' }
);

if (/^ABORT:/i.test(normalizeResult(verifyResult).trim())) {
  log('ОШИБКА: верификация прервана — ' + normalizeResult(verifyResult).slice(0, 200));
  throw new Error('Verification aborted: ' + normalizeResult(verifyResult).slice(0, 200));
}

log('Проверка идей завершена: docs/audit/brainstorm-filtered.md');
