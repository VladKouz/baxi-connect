# Baxi Connect (Custom edition)

Настольное приложение на Python для мониторинга и управления котлом **Baxi** через облако **ZONT**. Данные котла читаются по протоколу **OpenTherm** (блок `z3k-state` в API ZONT). Окно приложения всегда поверх других окон — удобно держать показания под рукой на рабочем столе.

## Возможности

- **Плавающее окно** с тёмным интерфейсом и крупным шрифтом показаний
- **Текущий режим отопления** — отображение и переключение одним нажатиem (Ночь, Комфорт, Эконом, Выключен, Лето и др., в зависимости от конфигурации ZONT)
- **Показания котла в реальном времени** (обновление по таймеру):
  - температура теплоносителя
  - модуляция горелки (%)
  - давление (бар)
  - температура ГВС
- **Автообновление** с настраиваемым интервалом (по умолчанию 10 минут)
- **Окно настроек** — ключи API, интервал обновления, размер шрифта
- **Ручное обновление** (кнопка ↻) и перетаскивание окна мышью

## Требования

- **Python** 3.11+
- **macOS** (tkinter входит в стандартную поставку Python; приложение тестировалось на macOS)
- Аккаунт на [zont.online](https://zont.online) с подключённым контроллером ZONT (H-2000+, H-2 и аналоги)
- Котёл Baxi, подключённый к контроллеру по **OpenTherm**

## Установка

```bash
cd "baxi connect"
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Для разработки (линтер, тесты):

```bash
pip install -e ".[dev]"
```

## Первый запуск и настройка

### 1. Ключи доступа (`secrets.json`)

Скопируйте шаблон и заполните своими данными:

```bash
cp secrets.example.json secrets.json
```

Файл `secrets.json` **не попадает в git** (см. `.gitignore`).


| Поле        | Описание                                                                                           |
| ----------- | -------------------------------------------------------------------------------------------------- |
| `boiler_id` | Серийный номер устройства ZONT (поле `serial` в личном кабинете), например `A1B2C3D4E5F6`          |
| `token`     | Токен API ZONT (заголовок `X-ZONT-Token`), например `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`             |
| `client`    | Контакт разработчика/пользователя для API (заголовок `X-ZONT-Client`), например `user@example.com` |


Те же ключи можно изменить в окне настроек приложения (⚙).

#### Как получить токен

Токен выдаётся через API ZONT методом `[get_authtoken](https://my.zont.online/api/docs/#get_authtoken)`. Нужны **логин и пароль** от [личного кабинета ZONT](https://my.zont.online/).

**Документация API:**

- [my.zont.online/api/docs](https://my.zont.online/api/docs/) — основная
- [lk.zont-online.ru/api/docs](https://lk.zont-online.ru/api/docs/) — зеркало

**Шаг 1. Запросить токен**

Подставьте свой логин, пароль и e-mail (тот же, что пойдёт в `client`):

```bash
curl -X POST 'https://my.zont.online/api/get_authtoken' \
  -u 'your_login:your_password' \
  -H 'X-ZONT-Client: user@example.com' \
  -H 'Content-Type: application/json' \
  -d '{"client_name": "Baxi Connect"}'
```

Пример успешного ответа:

```json
{
  "ok": true,
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

Скопируйте значение поля `token` в `secrets.json`.

Тот же запрос на Python:

```python
import requests

response = requests.post(
    "https://my.zont.online/api/get_authtoken",
    auth=("your_login", "your_password"),
    headers={"X-ZONT-Client": "user@example.com"},
    json={"client_name": "Baxi Connect"},
    timeout=30,
)
data = response.json()
print(data["token"])
```

**Шаг 2. Узнать `boiler_id` (serial)**

После получения токена запросите список устройств:

```bash
curl -X POST 'https://my.zont.online/api/devices' \
  -H 'X-ZONT-Client: user@example.com' \
  -H 'X-ZONT-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
  -H 'Content-Type: application/json' \
  -d '{"load_io": false}'
```

В ответе найдите нужный контроллер и поле `serial` — это значение для `boiler_id`:

```json
{
  "ok": true,
  "devices": [
    {
      "name": "Мой котёл",
      "serial": "A1B2C3D4E5F6"
    }
  ]
}
```

**Шаг 3. Заполнить `secrets.json`**

```json
{
  "boiler_id": "A1B2C3D4E5F6",
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "client": "user@example.com"
}
```

**Важно:**

- Пароль от ZONT в приложение **не сохраняется** — только токен.
- Если API начинает отвечать **403**, токен мог быть отозван в личном кабинете — получите новый через `get_authtoken`.
- Заголовок `X-ZONT-Client` обязателен во всех запросах; укажите там свой реальный e-mail.

### 2. Параметры интерфейса (`settings.json`)

Создаётся автоматически при первом запуске:

```json
{
  "refresh_interval_minutes": 10,
  "font_size": 28
}
```


| Поле                       | Описание                                              |
| -------------------------- | ----------------------------------------------------- |
| `refresh_interval_minutes` | Интервал автообновления данных (минимум 1 минута)     |
| `font_size`                | Размер шрифта значений на главном экране (минимум 12) |


## Запуск

```bash
source .venv/bin/activate
baxi-connect
```

или:

```bash
python -m baxi_connect.main
```

При старте окно открывается размером около **540×760** px, поверх остальных приложений.

## Интерфейс

### Главное окно

- **Заголовок** — Baxi Connect (Custom edition)
- **Блок режимов** — горизонтальный ряд кнопок с иконками; активный режим подсвечен цветом
- **4 карточки показаний** (одинакового размера, с иконками):
  - теплоноситель (°C)
  - модуляция горелки (%), с индикатором прогресса
  - давление (бар)
  - ГВС (°C)
- **Строка статуса** — время последнего успешного обновления или текст ошибки

Управление:


| Элемент          | Действие                    |
| ---------------- | --------------------------- |
| ↻                | Обновить данные сейчас      |
| ⚙                | Открыть настройки           |
| Режим (чип)      | Переключить режим отопления |
| Текст / карточки | Перетаскивание окна         |


### Окно настроек

- Boiler ID, Token, Client — подключение к ZONT API
- Интервал обновления (минуты)

## Интеграция с ZONT API

Приложение использует официальное REST API ZONT:


| Операция                   | Endpoint                                      | Метод                     |
| -------------------------- | --------------------------------------------- | ------------------------- |
| Чтение состояния устройств | `https://my.zont.online/api/devices`          | POST, `{"load_io": true}` |
| Смена режима отопления     | `https://my.zont.online/api/send_z3k_command` | POST                      |


Заголовки каждого запроса:

```
X-ZONT-Client: <client>
X-ZONT-Token: <token>
Content-Type: application/json
```

### Откуда берутся показания

Устройство ищется по `boiler_id` (= `serial` в ответе API). Данные OpenTherm извлекаются из:

```
devices[].io["z3k-state"][*].ot
```

Маппинг полей OpenTherm → интерфейс:


| Показание в приложении    | Поле OpenTherm | Описание                      |
| ------------------------- | -------------- | ----------------------------- |
| Температура теплоносителя | `bt`           | Boiler temperature            |
| Модуляция горелки         | `rml`          | Relative modulation level (%) |
| Давление                  | `wp`           | Water pressure                |
| Температура ГВС           | `dt`           | DHW temperature               |


### Смена режима

Команда отправляется для выбранного режима из `z3k_config.heating_modes`:

```json
{
  "device_id": 123456,
  "object_id": 20001,
  "command_name": "SelectHeatingMode",
  "command_args": null,
  "is_guaranteed": true
}
```

`object_id` — это `id` режима из конфигурации ZONT (например, `20001` = «Комфорт»; конкретные значения зависят от вашего устройства).

Документация API: [my.zont.online/api/docs](https://my.zont.online/api/docs/)

## Структура проекта

```
baxi connect/
├── assets/icons/          # PNG-иконки режимов и показаний
├── secrets.example.json   # Шаблон ключей (без секретов)
├── secrets.json           # Ключи API (локально, в .gitignore)
├── settings.json          # Настройки интерфейса
├── pyproject.toml
└── src/baxi_connect/
    ├── main.py            # Точка входа
    ├── config.py          # Загрузка/сохранение secrets и settings
    ├── models.py          # BoilerReading, HeatingMode
    ├── zont_api.py        # Клиент ZONT API
    └── ui/
        ├── app.py         # Главный цикл, таймер, смена режима
        ├── display_window.py
        ├── mode_selector.py
        ├── settings_window.py
        ├── theme.py       # Тема, MetricCard, IconButton
        └── icons.py       # Загрузка иконок
```

## Разработка

Проверка стиля:

```bash
ruff check src
```

Запуск тестов (если добавлены):

```bash
pytest
```

Переустановка после изменений:

```bash
pip install -e .
```

## Безопасность

- Не коммитьте `secrets.json` — файл в `.gitignore`
- Токен ZONT даёт доступ к управлению отоплением; храните его только локально
- При утечке токена отзовите его в личном кабинете ZONT и выпустите новый

## Устранение неполадок


| Проблема                      | Возможная причина                                          |
| ----------------------------- | ---------------------------------------------------------- |
| «Устройство не найдено»       | Неверный `boiler_id` (проверьте serial в ZONT)             |
| «Данные OpenTherm не найдены» | OpenTherm не включён или котёл offline                     |
| Ошибка сети / SSL             | Нет интернета или проблемы с сертификатами Python на macOS |
| 403 от API                    | Токен отозван — получите новый через `get_authtoken`       |
| Окно обрезано                 | Увеличьте окно вручную; минимальный размер 460×680         |


## Лицензия и авторство

Проект создан для личного использования (**Custom edition**). Иконки режимов и метрик — [Icons8 Fluency](https://icons8.com/icons/fluency).