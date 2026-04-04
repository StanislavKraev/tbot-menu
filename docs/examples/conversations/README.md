Вот production-ready реализация диалогового бота с FSM (Finite State Machine) состояниями в PostgreSQL.
Состояния сохраняются в БД и восстанавливаются при перезапуске бота или рестарте сессии.

dialog_bot/
├── alembic/
│   └── versions/
│       └── 001_dialog_states.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── main.py
│   ├── states.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── postgres.py
│   └── handlers/
│       ├── __init__.py
│       └── order.py
├── .env
├── requirements.txt
└── docker-compose.yml

Как работает восстановление состояния
Пользователь начал заказ → состояние waiting_for_quantity + данные {"product": "iPhone"} сохранены в PostgreSQL
Бот перезапущен → при следующем сообщении Aiogram делает get_state() и get_data() из PostgresStorage
Пользователь продолжает → бот знает, что ждет количество, и предлагает ввести его
Команды бота
/order — начать оформление заказа
/cancel — отменить текущий диалог
/status — проверить текущее состояние (отладка)
Состояние сохраняется даже при перезагрузке сервера или обновлении кода бота.
