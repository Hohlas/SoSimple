# Сырые гипотезы брэйншторма (разметка кластеров)

Сгенерировано idea_brainstorm.js + idea_check.js, фаза кластеров. Ранжирования нет.
Один кластер = один механизм edge.

## Volatility regime transition prediction [кластер 1]
- Суть: Predict transitions between volatility regimes (low→high, high→low) rather than price direction. Train on realized volatility clustering and regime change points. Trade when regime transition probability exceeds threshold, with direction-agnostic straddle-like positions.
- Обходимый тупик: already-moved, regime drift
- Откуда edge: [гипотеза] Volatility clustering is well-documented in financial markets; large moves tend to follow large moves. The edge comes from predicting when volatility will expand, not which direction price will move.
- Теги: радикальная

## Time-to-event survival modeling [кластер 1]
- Суть: Model time until next significant price movement (>X ATR) using survival analysis (Cox proportional hazards, parametric survival models). Target is hazard rate, not direction. Enter when predicted event probability in next N bars exceeds threshold.
- Обходимый тупик: already-moved, low R²
- Откуда edge: [гипотеза] Market microstructure creates predictable clustering of large moves around events; survival models capture this temporal structure without requiring directional prediction.
- Теги: 

## Path morphology classification [кластер 2]
- Суть: Classify price path shapes (trending, mean-reverting, spiking, consolidating) using shape descriptors (fractal dimension, Hurst exponent, path efficiency). Different exit strategies for each morphology. Predict morphology, not outcome.
- Обходимый тупик: already-moved
- Откуда edge: [гипотеза] Different path morphologies have different statistical properties; trending paths favor momentum exits, mean-reverting paths favor contrarian exits. Morphology is more predictable than direction.
- Теги: 

## Conditional return distribution modeling [кластер 3]
- Суть: Model full conditional distribution of returns (not just mean) using mixture density networks or quantile regression. Trade when distribution shows asymmetry or fat tails. Target is distribution shape, not point forecast.
- Обходимый тупик: low R², already-moved
- Откуда edge: [гипотеза] Return distributions are time-varying and conditionally asymmetric; capturing higher moments (skewness, kurtosis) provides edge even when mean return is unpredictable.
- Теги: радикальная

## Multi-scale amplitude decomposition [кластер 4]
- Суть: Decompose amplitude into components at different time scales using wavelet transforms or bandpass filters. Predict amplitude at each scale separately. The amplitude filter works (2.11); different scales may have different predictability and edge sources.
- Обходимый тупик: already-moved
- Откуда edge: [гипотеза] Short-term and long-term amplitude have different drivers (microstructure vs macro); decomposing allows targeting the more predictable component and avoiding scale-mismatch.
- Теги: 

## Cross-asset relative strength signals [кластер 5]
- Суть: Use correlated currency pairs (EUR/USD vs USD/CHF, AUD/USD vs NZD/USD) to predict relative movement. Target is spread between correlated assets, not absolute direction. Pairs trading logic applied to FX correlations.
- Обходимый тупик: regime drift
- Откуда edge: [гипотеза] Correlated assets have temporary divergences that revert; relative strength is more stable than absolute direction because it cancels common factors (USD strength, risk sentiment).
- Теги: 

## Liquidity event prediction [кластер 6]
- Суть: Predict liquidity events (spread widening, volume spikes, gap formations) rather than price movement. Target is liquidity state change. Trade when liquidity event probability is high, using market orders to capture dislocations.
- Обходимый тупик: already-moved, low R²
- Откуда edge: [гипотеза] Liquidity provision is costly; market makers demand compensation for adverse selection. Predicting when liquidity will dry up allows capturing the liquidity premium.
- Теги: радикальная

## Regime transition early warning system [кластер 7]
- Суть: Model regime transitions themselves (2023 breakpoint killed strategies in 2.8). Target is probability of regime change within N bars. Use change-point detection, structural break tests. Reduce position size or exit when regime change likely.
- Обходимый тупик: regime drift
- Откуда edge: [гипотеза] Regime transitions have precursors (volatility increase, correlation breakdown, volume pattern changes); detecting these allows defensive positioning before strategy breakdown.
- Теги: 

## Microstructure imbalance prediction [кластер 6]
- Суть: Predict short-term order flow imbalances using tick-level data (if available) or high-frequency proxies (bid-ask spread changes, intra-bar price distribution). Target is microstructure imbalance, not directional move.
- Обходимый тупик: already-moved
- Откуда edge: [гипотеза] Order flow has short-term predictability due to institutional execution algorithms and hedging flows; microstructure signals decay fast but may be exploitable at appropriate frequency.
- Теги: радикальная

## Flow Toxicity VPIN Regime [кластер 6]
- Суть: Вычислять VPIN (Volume-Synchronized Probability of Informed Trading) по тиковому потоку как индикатор токсичности потока. Торговать только в режимах низкой токсичности, когда спред стабилен и исполнение предсказуемо. Не предсказывает направление — фильтрует моменты, когда рынок «нормален».
- Обходимый тупик: календарная доминантность
- Откуда edge: [гипотеза] информированные трейдеры создают кластеры токсичного потока; в тихие периоды spread-составляющая ниже, а fill-качество выше — это механика исполнения, а не прогноз цены.
- Теги: радикальная

## Hawkes Volatility Clustering [кластер 1]
- Суть: Моделировать само-возбуждение волатильности через процесс Hawkes: каждое крупное движение повышает интенсивность будущих движений. Использовать условную интенсивность как сигнал для входа в кластер волатильности, без прогноза знака.
- Обходимый тупик: already moved
- Откуда edge: [гипотеза] кластеризация волатильности — эмпирический факт; Hawkes даёт параметрическую оценку вероятности следующего события в окне, что устойчивее эмпирических ATR-порогов.
- Теги: 

## PCMCI Causal Drivers [кластер 8]
- Суть: Применить PCMCI (алгоритм causal discovery для временных рядов) для выявления причинно-следственных связей между кросс-инструментальными переменными (нефть, бонды, индексы) и целевой парой. Использовать только причинные связи как признаки, отсекая ложные корреляции.
- Обходимый тупик: low R²
- Откуда edge: [гипотеза] причинные связи между активами устойчивее корреляционных; causal filter устраняет шумовые признаки, повышая signal-to-noise без leakage.
- Теги: радикальная

## BOCPD Regime Switching [кластер 7]
- Суть: Bayesian Online Change-Point Detection в реальном времени определяет структурные сдвиги режима. Торговая система активна только когда BOCPD подтверждает стабильный режим; при detection change-point — переход в standby.
- Обходимый тупик: regime drift
- Откуда edge: [гипотеза] режимный перелом 2023 — не noise, а структурный сдвиг; BOCPD даёт вероятностную детекцию без скользящих окон, которые запаздывают.
- Теги: 

## Survival Competing Risks Exit [кластер 9]
- Суть: Модель выживаемости с конкурирующими рисками: вместо тройного барьера, моделировать hazard-функции для TP/SL/timeout как конкурирующих событий. Оптимизировать hold duration по conditional survival probability, а не по фиксированным барьерам.
- Обходимый тупик: не указан
- Откуда edge: [гипотеза] конкурирующие риски — стандарт в medical statistics; hazard-модель учитывает time-varying covariates и цензурирование, что даёт более точный exit timing чем фиксированные пороги.
- Теги: похоже на: тройной барьер

## Transfer Entropy Cross-Asset [кластер 8]
- Суть: Вычислять transfer entropy (непараметрическая мера направленного информационного потока) между парами валют для обнаружения лидеров и запаздывающих. Использовать TE-профиль как признак: если одна пара «ведёт», другая следует с задержкой.
- Обходимый тупик: already moved
- Откуда edge: [гипотеза] transfer entropy улавливает нелинейные направленные зависимости, которые не видны в корреляции; информационное лидерство между активами — устойчивый микро-эффект.
- Теги: радикальная

## Topological Persistence Features [кластер 2]
- Суть: Применить TDA (persistent homology) к скользящим окнам ценовых данных: извлекать топологические инварианты (число дыр, компонент связности) как признаки режима. Топологические свойства устойчивы к шуму и нормировке.
- Обходимый тупик: low R²
- Откуда edge: [гипотеза] топологическая структура ценового облака кодирует режимные свойства, которые не видны в статистических моментах; persistence отфильтровывает шумовые флуктуации.
- Теги: радикальная

## Synthetic Control Anomaly [кластер 5]
- Суть: Построить синтетический контроль (synthetic control method) из взвешенной комбинации других валютных пар как counterfactual для целевой пары. Торговать отклонения от синтетического пути — это аномалии, не объяснимые общим фактором.
- Обходимый тупик: уже не работает: одноисточниковый OHLC
- Откуда edge: [гипотеза] синтетический контроль — стандарт в causal inference для policy evaluation; cross-sectional counterfactual выделяет idiosyncratic движение, не зависящее от общего рыночного фактора.
- Теги: радикальная

## Fluctuation Dissipation Entry [кластер 10]
- Суть: Применить флуктуационно-диссипативную теорему из статистической физики: в равновесии отклик системы пропорционален флуктуациям. Отклонение от FDT-соотношения указывает на неравновесный режим, где цена более предсказуема.
- Обходимый тупик: не указан
- Откуда edge: [гипотеза] валютный рынок вблизи равновесия — efficient; отклонение от FDT — индикатор temporary disequilibrium, когда price impact предсказуем.
- Теги: радикальная

## Queue Imbalance Microstructure [кластер 6]
- Суть: Моделировать лимитный ордербук как систему массового обслуживания: arrival rate заявок на покупку vs продажу, service rate (исполнение). Queue imbalance (разница нормированных интенсивностей) — сигнал давления без прогноза направления.
- Обходимый тупик: не указан
- Откуда edge: [гипотеза] queue imbalance — стандартный микро-сигнал в HFT; на Forex спот-рынке дисбаланс лимиток создаёт краткосрочное давление, устойчивое из-за структурных ограничений market-making.
- Теги: радикальная

## Волатильность как аномалия [кластер 1]
- Суть: Conformal prediction строит доверительные интервалы для каждого бара. Когда интервал аномально узок (рынок в компрессии), а следующий бар расширяется за пределы — это сигнал на вход. Направление не предсказывается, торгуется сам факт выхода из компрессии.
- Обходимый тупик: already-moved: сигнал не о движении, а о структурном изменении волатильности; не требует знания знака.
- Откуда edge: [гипотеза] рыночные микро-структуры демонстрируют кластеризацию волатильности: после аномально узких интервалов следует расширение, которое можно обнаружить без предсказания направления.
- Теги: радикальная

## Survival exit timing [кластер 9]
- Суть: Вместо классификации breach/no-breach моделируется hazard-функция времени до пробоя уровня. Кривая выживания задаёт динамический exit: если вероятность дожить до бара k падает ниже порога — выходим. Breach-сигнал был реален диагностически, но не конвертировался в прибыль; survival-рефрейминг меняет вопрос с «будет ли пробой» на «когда ждать».
- Обходимый тупик: low R²: hazard-модель не требует точного предсказания, только относительного ранжирования по времени.
- Откуда edge: [гипотеза] условное распределение времени до пробоя содержит больше информации, чем бинарный классификатор, потому что форма hazard-кривой устойчивее точки перегиба.
- Теги: 

## Амплитудно-календарный режимный отпечаток [кластер 11]
- Суть: Амплитудный фильтр стабилен, календарная доминантность — факт. Вместо использования календаря как сигнала, календарно-амплитудное взаимодействие используется как идентификатор режима. Кластеризация по профилю (час×ATR-квантиль), торговля только в режимах, исторически соответствующих profitable-кластерам.
- Обходимый тупик: regime drift: режимный перелом 2023 обнаруживается как смена кластерной структуры, а не как падение PF модели.
- Откуда edge: [гипотеза] совместное распределение внутидневной волатильности и календарного времени формирует квази-стационарные режимы, переходы между которыми реже, чем переходы внутри режима.
- Теги: 

## Rank stability confidence [кластер 12]
- Суть: Вместо одной модели — ансамбль из K моделей на разных подвыборках признаков. Устойчивость рангового порядка предсказаний (Kendall tau между подвыборками) — мета-сигнал: высокий agreement = торговать, низкий = пропуск. Не выбирает winner-правило, а измеряет надёжность самого факта торговли.
- Обходимый тупик: автовыбор winner: ансамбль не выбирает лучшую модель, а агрегирует все; малые выборки: agreement устойчивее абсолютного значения при малом N.
- Откуда edge: [гипотеза] если множество моделей с разными подмножествами признаков согласны, что текущий бар — торговый, это свидетельство структурной выраженности сигнала, а не артефакта одной модели.
- Теги: 

## MFE conditional quantile exit [кластер 3]
- Суть: MFE/MAE уже вычисляются. Вместо предсказания направления регрессируется условное распределение MFE (квантили 0.5/0.75/0.9) при текущих признаках. Квантильная регрессия задаёт адаптивный take-profit: если предсказанный MFE q75 < spread — не торговать. Направление не нужно, нужна только оценка масштаба движения.
- Обходимый тупик: already-moved: MFE — future-derived для входа, но для exit он может быть заменён на rolling-окно исторического MFE в похожих структурных условиях; leakage обходит использование out-of-sample MFE-распределения как reference.
- Откуда edge: [гипотеза] условная медиана MFE в структурно похожих окнах стабильнее, чем направление, потому что амплитуда — единственный носитель сигнала (подтверждено MI-аудитом).
- Теги: 

## Fractal structural similarity [кластер 2]
- Суть: Фрактальные признаки не подаются в классификатор, а используются как эмбеддинг структурного отпечатка окна. Текущее окно сравнивается с историческими окнами через косинусное сходство в пространстве фрактальных признаков. Торговля — когда текущий отпечаток близок к исторически profitable-окнам. Задача рефреймится из классификации в retrieval.
- Обходимый тупик: low R²: retrieval не требует регрессионной точности, только относительного сходства; time-only dominance: структурный отпечаток не содержит календарных признаков.
- Откуда edge: [гипотеза] фрактальная структура ценового окна кодирует режим рынка, и повторение структурных паттернов коррелирует с повторением исходов — аналогия с k-NN в пространстве признаков.
- Теги: 

## Nero tick-flow imbalance [кластер 13]
- Суть: Nero-поток (MT5 producer) доступен как фича-поток, но использовался только для parity-проверки. Гипотеза: асимметрия частоты тиков (buy-tick rate vs sell-tick rate в скользящем окне) — order-flow imbalance — независимый сигнал, не выведенный из OHLC. Торговля при устойчивом перекосе в сторону одного направления.
- Обходимый тупик: one-source OHLC: Nero — независимый источник данных, не производный от OHLC; информационная граница: tick-flow может содержать информацию о знаке, которой нет в OHLC.
- Откуда edge: [гипотеза] асимметрия потока тиков отражает дисбаланс лимитных и маркет-ордеров, который предшествует движению цены и не captured OHLC-признаками.
- Теги: 

## Adversarial regime gate [кластер 14]
- Суть: Классификатор train-vs-recent обучается различать признаки обучающего и последнего тестового периода. Его AUC — количественная мера сдвига распределения. Когда AUC > 0.60 (рынок «ушёл»), размер позиции сокращается или торговля приостанавливается. Это не сигнал входа, а мета-фильтр уверенности.
- Обходимый тупик: regime drift: перелом 2023 обнаруживается напрямую как distribution shift; расширение обучения не спасает — adversarial gate не расширяет обучение, а останавливает торговлю при несовпадении.
- Откуда edge: [гипотеза] если признаки train и test статистически различимы, модель не может обобщать; обнаружение этого факта — необходимый условие торговли, а не улучшение модели.
- Теги: радикальная

## Bootstrap agreement meta-signal [кластер 12]
- Суть: Модель обучается N раз на bootstrap-агрегатах. Доля моделей, предсказывающих trade (signal ≠ 0), — мета-сигнал. Торговля только когда ≥80% моделей согласны. Это не автовыбор winner (каждая модель — полноценный кандидат), а измерение устойчивости решения.
- Обходимый тупик: seed instability: 2/5 сидов PF>2 — agreement напрямую измеряет, зависит ли результат от сида; малые выборки: при N=30 agreement 80% = 24/30 моделей, что статистически значимо.
- Откуда edge: [гипотеза] если большинство bootstrap-моделей согласны, что бар — торговый, это свидетельство, что сигнал не является артефактом конкретной подвыборки.
- Теги: 

## Cross-sectional FX rank selection [кластер 15]
- Суть: Вместо предсказания направления одной пары — ранжировать 20–30 пар по относительной силе за последние N баров и входить в топ-квинтиль long /.bottom-квинтиль short. Направление конкретной пары не предсказывается; edge в персистентности рангов.
- Обходимый тупик: Направленческий сигнал (MI direction FAIL, все постановки 2.7/2.11)
- Откуда edge: [гипотеза] институциональные потоки ребалансировки и трендовая инерция на межвалютном уровне создают персистентность относительной силы; платят трейдеры, которые торгуют отдельные пары против тренда
- Теги: радикальная; похоже на: прямое предсказание направления

## Volatility risk premium harvesting [кластер 16]
- Суть: Систематическая продажа OTM strangles на FX-опционах (или их синтетиках через котировки implied vol). Направление не нужно — edge в структурном превышении implied over realized volatility. Частота решений — раз в день/неделю, не на бар.
- Обходимый тупик: Информационная граница (MI direction FAIL, 2.1) и внутрибаровая хронология fill (2.12)
- Откуда edge: [гипотеза] хедж-фонды и корпораты систематически переплачивают за страховку через options premium; realized vol стабильно ниже implied — это документированный академический эффект
- Теги: радикальная

## Macro regime portfolio allocation [кластер 17]
- Суть: Вместо торговли на каждом баре — классифицировать макро-режим (risk-on/risk-off/кризис) по spreads, rates, VIX и аллоцировать капитал между заранее подготовленными sub-strategies. Частота решений — раз в неделю/месяц.
- Обходимый тупик: Режимный перелом 2023 (2.8, 2.9) и календарная доминантность (2.12)
- Откуда edge: [гипотеза] макро-переключения управляются центральными банками и структурными потоками; платят те, кто остаётся в неправильном режиме при смене цикла
- Теги: радикальная

## Negative selection — when NOT to trade [кластер 14]
- Суть: Модель предсказывает не вход, а пропуск: оценивает ожидаемые транзакционные издержки (spread widening, low volatility, session overlap) и фильтрует периоды, где cost-to-edge ratio неблагоприятен. Edge — не в прибыльных сделках, а в избежании убыточных.
- Обходимый тупик: Малые выборки и хрупкая годовая стабильность (2.2, 2.4, 2.12)
- Откуда edge: [гипотеза] транзакционные издержки кластеризуются во времени; платят маркет-мейкеры, которые забирают spread в моменты, когда трейдер вынужден войти
- Теги: радикальная; похоже на: календарная доминантность

## Carry-momentum interaction on EM FX [кластер 15]
- Суть: Торговать EM FX пары (USD/MXN, USD/ZAR, USD/TRY) через комбинацию carry (процентный дифференциал) и momentum. Carry даёт структурный дрейф, momentum — тайминг входа. Направление предсказывается не из цены, а из макро-переменных.
- Обходимый тупик: Направленческий сигнал (2.7, 2.11) и single-instrument OHLC (2.12, 2.13)
- Откуда edge: [гипотеза] carry trade премиум на EM валютах документирован в академической литературе; платят спекулянты, которые несут tail-risk без adequate compensation
- Теги: радикальная

## Execution venue asymmetry [кластер 18]
- Суть: Использовать разницу в исполнении между лимитными и рыночными ордерами на разных сессиях: размещать лимитки на одной сессии (Asian, узкий spread для определённых пар), а исполнение получить на другой (London/NY, расширение). Edge в микроструктуре, не в прогнозе цены.
- Обходимый тупик: Внутрибаровая хронология fill (2.6, 2.12) и single-source OHLC (2.12, 2.13)
- Откуда edge: [гипотеза] асинхронность ликвидности между сессиями создаёт предсказуемый паттерн fill quality; платят трейдеры, которые входят рыночными ордерами в illiquid hours
- Теги: радикальная

## Cross-asset lead-lag signals [кластер 19]
- Суть: Использовать движение коррелированных активов (equity indices, bond yields, commodity prices) как leading indicator для FX, вместо лаговых признаков той же пары. S&P 500 futures, US10Y yield, WTI — потенциально содержат информацию о направлении USD-пар раньше, чем сама цена FX.
- Обходимый тупик: Already-moved (2.11) и информационная граница (2.1)
- Откуда edge: [гипотеза] cross-asset information propagation имеет задержки из-за сегментации участников; платят те, кто реагирует на движение bonds с опозданием в FX
- Теги: радикальная

## Gamma hedging flow front-running [кластер 16]
- Суть: Опционные дилеры обязаны хеджировать gamma exposure у страйков с высокой open interest. Это создаёт предсказуемые pinning и acceleration эффекты около крупных страйков на еженедельных/ежедневных экспирациях. Сигнал из options open interest, не из OHLC.
- Обходимый тупик: Направленческий сигнал (2.7, 2.11) и low R² (2.1)
- Откуда edge: [гипотеза] дилеры механически хеджируют gamma, создавая предсказуемые потоки; платят direction-трейдеры, которые входят в сторону dealer hedging flow около экспираций
- Теги: радикальная

## Ultra-low frequency regime bets [кластер 17]
- Суть: Полный отказ от внутридневной/часовой торговли. Входить раз в месяц-квартал на основе макро-сигналов ( Purchasing Managers Index divergence, central bank dot-plot shifts, fiscal policy changes). Каждая сделка — недельный/месячный hold. 4–12 сделок в год.
- Обходимый тупик: Календарная доминантность (2.12), regime drift (2.8) и малые выборки (2.2)
- Откуда edge: [гипотеза] макро-тренды управляются асимметрией monetary policy циклов; платят спекулянты, которые торгуют против центральных банков на коротких горизонтах
- Теги: радикальная

## Adverse selection cost model as signal [кластер 14]
- Суть: Построить модель adverse selection (информационное преимущество контрагентов) и использовать её как фильтр: торговать только когда модель показывает, что текущий spread не содержит информационную ренту. Это переворачивает задачу — не «где цена пойдёт», а «когда меня не обманывают».
- Обходимый тупик: Leakage и хронология fill (2.5, 2.12), low R² (2.1)
- Откуда edge: [гипотеза] токсичность потока (order flow toxicity) кластеризуется; платят неинформированные трейдеры, которые входят когда informed traders уже знают направление
- Теги: радикальная; похоже на: календарная доминантность
