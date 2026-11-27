# План развития `android-mcp`

> Живой документ. Обновляется по мере развития проекта.
> Статус: **Этап 0 — согласование и каркас**.

## 0. Цель проекта

MCP-сервер (Model Context Protocol) для полноценного управления Android-устройствами
из ИИ-агентов. **Работает по сети (Wi-Fi), а не только по USB.**

Пишется с нуля, «грамотно»: чистые модули, тесты, CI, релизы.

Ключевые отличия от существующих решений:
- **Network-first** — управление телефоном по Wi-Fi / через туннель, из любой точки.
- **Агент реально видит экран** (скриншот как image-content, а не путь к файлу).
- Неблокирующий async-ADB, мультидевайс, approval-gate на опасные действия.

## 1. Что такое MCP (кратко)

MCP — открытый стандарт (Anthropic, 2024, JSON-RPC 2.0 поверх stdio / SSE / HTTP).
Сервер пишется один раз и работает в любом клиенте: Claude Desktop, Claude Code,
Cursor, Cline, VS Code Copilot, Zed, Windsurf, **Hermes Agent**. Именно поэтому наш
сервер — универсальный, а не «для Hermes».

## 2. Анализ референса (AsmanovLev/android-mcp)

Первый прототип, вдохновивший проект (2 ★, TS/Node, ADB, монолит 812 строк).

Черпаем оттуда | Отвергаем
---|---
Инъекция touch через `sendevent` (hold/drag/multi-touch) | Скриншот только путём к файлу (модель не видит экран)
Макросы `unlock`/`home`/`back`/панели | `spawnSync` блокирует loop
Разбор UI-tree через `uiautomator dump` | Старый SDK 0.5.0, хардкод путей
Набор инструментов app/gesture/state | Плейнтекст-хранилище паролей

## 3. Сетевой доступ (ключевое требование)

Телефон должен управляться **по сети**, а не быть привязанным к USB.

### 3.1 Способы подключения к телефону

| Способ | Как | Когда |
|---|---|---|
| **Wireless ADB (LAN)** | Android 11+: `adb pair ip:port` → `adb connect ip:port` | телефон и сервер в одной сети |
| **Телефон — VPN-клиент домашней сети** ⭐ | телефон подключается клиентом (WireGuard/L2TP) к домашнему VPN → получает IP в VPN-подсети (77/79/80/81/82) → сервер видит его **как в LAN** | телефон из интернета, а сервер дома |
| **ADB over Tailscale** | Tailscale на телефоне → хост видит его IP | доступ из любой точки |
| **HTTP MCP on-device** (см. V2) | APK отдаёт MCP по HTTP(S) | совсем без ADB |

> **Решение (зафиксировано):** primary — wireless ADB; достижимость телефона — через
> (а) домашнюю LAN, (б) **телефон как VPN-клиент домашнего VPN**, (в) Tailscale.
> Все три варианта сводятся к одному: у телефона есть IP, достижимый с хоста сервера.
> On-device APK (V2) — не фокус, отложено.

### 3.2 Что это значит для архитектуры

- **Транспорт клиент↔сервер:** `stdio` (локально) **+ Streamable HTTP / SSE** (удалённый агент).
- **Транспорт сервер↔телефон:** ADB по TCP + **автопереподключение** (wireless ADB рвётся).
- **Connection-строки:** сервер принимает `--serial`, `--host`, `--port`, реестр устройств.
- **Безопасность сети:** ADB — это полный доступ к устройству, поэтому:
  - только по доверенной сети (Tailscale/WG) либо с bind на loopback;
  - на Android 11+ пара обязательна (pairing) — используем;
  - для on-device HTTP — bearer-токен + TLS.

### 3.3 Топология (целевая)

```
Hermes Agent (в любой точке)
        │  MCP over HTTP(S)  +  туннель Tailscale/WG при необходимости
        ▼
  android-mcp (host:  .66 / ПК / ноут)
        │  ADB over TCP (Wi-Fi)
        ▼
   Android-телефон  (wireless ADB <> Tailscale)
```

## 4. Архитектура

### 4.1 Базовый продукт (V1) — host-side MCP-сервер

```
ИИ-клиент (Hermes/Cursor/Claude)
        │  MCP (stdio / HTTP)                 ← универсальный протокол
        ▼
  android-mcp (Python, asyncio)
        │  adb (Wi-Fi / USB / туннель)
        ▼
   Android-устройство
```

- **Транспорт к клиенту:** stdio (основной) + HTTP/SSE (удалённо).
- **Транспорт к телефону:** ADB. На телефоне **ничего ставить не надо** (кроме включения отладки).
- **Ядро:** модуль `AndroidDevice` (async-обёртка над adb) + реестр инструментов.

### 4.2 Модульная структура

```
src/android_mcp/
├── __init__.py
├── __main__.py          # entrypoint (python -m android_mcp)
├── server.py            # регистрация MCP-инструментов + транспорт (stdio/HTTP)
├── adb.py               # async subprocess-обёртка над adb
├── transport.py         # wireless ADB: pair/connect/disconnect, автопереподключение
├── device.py            # модель устройства, выбор активного, мультидевайс
├── ui.py                # парсинг uiautomator XML → интерактивные элементы
├── gestures.py          # tap/swipe/hold/drag/multi-touch (input + sendevent)
├── screenshot.py        # screencap → MCP image-content (base64 PNG)
├── apps.py              # install/start/stop/delete/list
├── sources.py           # RuStore / F-Droid поиск и загрузка APK
├── security.py          # approval-gate, политика опасных действий
└── config.py            # конфиг (env / yaml), без хардкода путей
```

### 4.3 Суб-продукты и варианты

| Вариант | Что это | Плюсы | Когда |
|---|---|---|---|
| **V1 Host ADB MCP** (базовый) | Python-сервер, общается с телефоном по ADB (Wi-Fi/USB/туннель) | Быстро к результату, ноль софта на телефоне | MVP, сейчас |
| **V2 On-device MCP** | APK (Kotlin) как MCP-сервер: AccessibilityService + HTTP(S) | Не нужен ADB и хост, доступ по сети из любой точки | Этап 6, опционально |
| **V3 CLI** | Та же логика без MCP — `android-mcp tap 100 200` | Скрипты, крон, ручное управление | Побочно |
| **V4 Библиотека** | Ядро как importable Python-пакет | Переиспользование в других проектах | Если нужно |
| **V5 Hermes-skill** | `SKILL.md`, учит агента пользоваться сервером | Агент делает меньше ошибок | После V1 |

## 5. Инструменты (целевой набор)

| Инструмент | Назначение | Этап |
|---|---|---|
| `device_list` | Список устройств + выбор активного | 1 |
| `device_connect` | Wireless ADB: `pair` / `connect` / `disconnect` / статус | 1 |
| `screenshot` | **Скриншот как изображение** (+ опц. UI-tree) | 1 |
| `dump_ui` | Только UI-дерево (текст) | 1 |
| `tap` / `swipe` / `type` / `press_key` | Базовый ввод | 1 |
| `long_press` / `drag` / `multi_touch` | Жесты через `sendevent` | 2 |
| `gesture_combo` | Последовательность шагов | 2 |
| `macro` | `unlock`/`home`/`back`/`recents`/панели | 2 |
| `wait_for` | Ожидание появления/исчезновения элемента | 2 |
| `app_install` / `app_start` / `app_stop` / `app_uninstall` / `app_list` | Управление приложениями | 3 |
| `store_search` / `store_download` | RuStore / F-Droid | 3 |
| `device_state` | Батарея, ориентация, экран, foreground-пакет | 2 |
| `activity_start` | Запуск Activity по intent | 3 |
| `adb_restart` | Перезапуск adb-сервера | 1 |

## 6. Этапы (план → согласование → этапами, сначала одно устройство)

- [x] **Этап 0. Согласование + каркас** — репо, план, структура, CI *(закрыт)*
- [ ] **Этап 1. MVP** — device/screenshot(image)/ui/tap/swipe/type/key/launch + **wireless ADB** — проверить на одном телефоне по Wi-Fi *(в работе; на MIUI input/ui_dump заблокированы — см. §10)*
- [ ] **Этап 2. Жесты и макросы** — hold/drag/multi-touch, combo, macro, wait_for, device_state
- [ ] **Этап 3. Приложения и магазины** — app_*, RuStore/F-Droid, activity_start
- [ ] **Этап 4. Сеть и безопасность** — ✅ HTTP-транспорт (stdio/streamable-http/sse); ⬜ туннель (Tailscale/WG), approval-gate, ревью
- [ ] **Этап 5. Релиз** — пакет, документация, теги, README, V5 skill
- [ ] **Этап 6 (опц.). On-device вариант** — APK + AccessibilityService (MCP по HTTP)

Каждый фикс — commit+push; каждая сборка — тег/релиз.

## 7. Решения (зафиксировано)

| Вопрос | Решение |
|---|---|
| Стек сервера | **Python 3.11+**, официальный `mcp` SDK (FastMCP), `asyncio` |
| Имя / owner | `RuslanStrogov/android-mcp` (публичный) |
| Доступ к телефону | **Network-first**: wireless ADB; достижимость — LAN / **телефон как VPN-клиент домашней сети** / Tailscale; USB — запасной |
| Транспорт к клиенту | stdio + HTTP/SSE (удалённый агент) |
| Формат кода | Чистые модули, type hints, `ruff` + `pytest` |
| Git | `feature/*` → PR → `dev` → PR → `main`; conventional commits |
| Лицензия | MIT |
| Хост-подход | Базовый (V1). On-device (V2) — позже, опционально |

## 8. Смежные проекты (разграничение)

| Проект | ★ | Где работает | Что делает | Отличие от нас |
|---|---|---|---|---|
| `mobile-next/mobile-mcp` | 11k | хост | ADB + accessibility, iOS+Android | не network-first, токены |
| `danielealbano/android-remote-control-mcp` | 870 | **на телефоне** | APK = MCP, AccessibilityService, HTTP | тяжёлый, только on-device |
| `CursorTouch/Android-MCP` | 940 | хост | ADB, Python `uvx` | без image-скриншота |
| `fullread/DeepADB` | 24 | хост | 209 инструментов по ADB | перегруз инструментов |
| `termuxgpt/termux-mcp` | 49 | **на телефоне** | shell в Termux + termux-api (REST+`termux-native-mcp`) | это терминал внутри телефона, **не** UI-автоматизация; AGPL-3.0 |

`termux-mcp` и наш проект — разные слои (shell-on-device vs UI-автоматизация по ADB),
не конкуренты; код под AGPL-3.0 не переносим, только идеи.

## 9. Открытые вопросы

- ~~Модель и версия Android свободного телефона~~ → **Redmi Note 7 (`lavender`), Android 10 / MIUI 12**
- Телефон в Tailscale/WireGuard для доступа извне — да/нет, какой туннель.
- Нужна ли интеграция с флотом Hermes (авто-подключение профилей к серверу).

## 10. Тестовое устройство (эталон)

| Параметр | Значение |
|---|---|
| Модель | Redmi Note 7 (`lavender`), MIUI 12 (V125), Android 10 (SDK 29) |
| Serial (USB) | `9735ca45` |
| Wi-Fi ADB | `192.168.10.210:5555` (wireless, `adb tcpip 5555`; на Android <11 pairing недоступен) |
| Настройки для автономной работы | `svc power stayon true` (не гаснет на зарядке), `locksettings set-disabled true` (не блокируется) |
| Ограничение | MIUI блокирует `settings put` (нет WRITE_SECURE_SETTINGS) — часть тюнинга недоступна без root |
| **❗ Блокировка ввода** | MIUI без спец-тумблера запрещает `input tap/swipe/text/keyevent` (**INJECT_EVENTS denied**). Лечится: *Настройки → Дополнительные → Для разработчиков → «Отладка по USB (настройки безопасности)»* (нужен Mi-аккаунт) либо root |
| ❗ `uiautomator dump` | На этом ROM падает («could not get idle state» / таймаут) |
| Что реально работает | screenshot ✅, запуск/стоп приложений ✅; input ❌, ui_dump ❌ (до тумблера/рута) |
| Важно | После ребута слетает `tcpip`/stayon → нужен USB + повторная авторизация |

### 10.1 Диагностика возможностей (`device_capabilities`)

Чтобы не гадать, сервер умеет **пробовать возможности** и отчитываться (`capabilities.py`):
`screenshot`, `input_inject`, `ui_dump`, `app_control` → ✅/❌ с причиной.
Первый прогон на Redmi Note 7: screenshot ✅, app_control ✅, input ❌ (INJECT_EVENTS), ui_dump ❌.
