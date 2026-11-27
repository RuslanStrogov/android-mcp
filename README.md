# android-mcp

> MCP-сервер для управления Android-устройствами из ИИ-агентов.
> Написан с нуля: async, мультидевайс, агент **видит экран**, approval-gate на опасные действия.

[![CI](https://img.shields.io/github/actions/workflow/status/RuslanStrogov/android-mcp/ci.yml?branch=main&label=CI)](.github/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

## Что это

`Model Context Protocol` (MCP) — открытый стандарт, по которому ИИ-клиент
(Claude Desktop, Claude Code, Cursor, Cline, VS Code, **Hermes Agent** и др.)
подключает внешние инструменты. Этот сервер даёт агенту полноценный доступ к
Android-устройству: скриншоты, UI-дерево, жесты, ввод, управление приложениями.

Работает через `adb` — **на телефоне ставить ничего не нужно**.

## Возможности (целевые)

- 📸 **Скриншот как изображение** — модель реально видит экран, а не только текст.
- 🖱️ Жесты: tap, swipe, long-press, drag, multi-touch (через `sendevent`).
- ⌨️ Ввод текста, аппаратные кнопки, макросы (`unlock`, `home`, `back`…).
- 🤖 Управление приложениями: install / start / stop / uninstall / list.
- 🏪 Поиск и загрузка APK из RuStore и F-Droid.
- 📱 Мультидевайс, wireless ADB (`pair` / `connect`).
- 🔒 Approval-gate на опасные операции.

## Инструменты

Реализовано (этап 1, MVP):

| Инструмент | Назначение | Проверено |
|---|---|---|
| `device_list` | список устройств (USB/Wi-Fi) | ✅ |
| `screenshot` | скриншот **как изображение** (image-content) | ✅ |
| `device_state` | батарея/температура, экран, foreground-приложение | ✅ |
| `device_capabilities` | доктор: что вообще разрешает ROM | ✅ |
| `app_launch` / `app_stop` / `app_list` | управление приложениями | ✅ |
| `dump_ui` | UI-дерево (интерактивные + подписанные элементы) | ✅ код, ⚠️ ROM |
| `tap` / `tap_text` / `swipe` / `type_text` / `press_key` / `wake` | ввод | ✅ код, ⚠️ ROM |

⚠️ **ROM-ограничение (MIUI):** без включённой «Отладки по USB (настройки безопасности)»
MIUI запрещает инъекцию ввода (`INJECT_EVENTS`) — тогда `tap/swipe/type` и `uiautomator`
не работают. Инструмент `device_capabilities` покажет это сразу. См. `PLAN.md §10`.

## Статус

🚧 **В разработке.** Активная работа — см. [`PLAN.md`](PLAN.md).

- [x] Этап 0 — каркас, план, CI
- [ ] Этап 1 — MVP
- [ ] Этап 2 — жесты и макросы
- [ ] Этап 3 — приложения и магазины
- [ ] Этап 4 — безопасность и мультидевайс
- [ ] Этап 5 — релиз

## Установка

```bash
git clone https://github.com/RuslanStrogov/android-mcp.git
cd android-mcp
```

Требования: Python 3.11+, `adb` (Android platform-tools), устройство с включённой
отладкой (USB или Wi-Fi).

## Подключение к клиенту

```jsonc
// пример конфигурации MCP-клиента
{
  "mcpServers": {
    "android": {
      "command": "python",
      "args": ["-m", "android_mcp"]
    }
  }
}
```

## Архитектура

См. [`PLAN.md`](PLAN.md) и [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Лицензия

[MIT](LICENSE) © Ruslan Strogov
