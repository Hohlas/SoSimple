## Stop conditions

Остановить текущий cycle и не продолжать model sweep, если:

- data contract не прошёл leakage gate;
- online features недоступны;
- candidate-source не live-safe;
- test уже был использован для выбора;
- validation gate не пройден;
- единственный плюс кандидата держится на одной стороне, одном году или очень малом N;
- cost-aware result отрицателен;
- MT4 parity показывает critical mismatch;
- forward data отсутствуют, но требуется forward verdict.

Правильный следующий шаг в этих случаях: написать reject/diagnostic report и сформулировать новую ограниченную гипотезу.
