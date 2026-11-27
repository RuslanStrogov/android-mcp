---
name: android-mcp
description: "Drive Android devices through the android-mcp MCP server (ADB over Wi-Fi/USB). Use when the user wants to control or automate an Android phone — screenshot, tap, swipe, type, launch apps, read device state/battery. Covers wireless ADB, MIUI ROM limits, and multi-device selection."
version: 0.1.0
author: Ruslan Strogov
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [android, adb, mcp, automation, mobile, screenshot]
    related_skills: [hermes-agent]
---

# android-mcp — управление Android-устройством из агента

Сервер `android-mcp` (MCP) даёт агенту инструменты для управления Android-телефоном
через ADB — скриншоты, жесты, ввод, запуск приложений, состояние устройства.
Работает по Wi-Fi и с несколькими устройствами.

Репозиторий: https://github.com/RuslanStrogov/android-mcp

## Когда использовать

- Пользователь просит посмотреть экран телефона / сделать скриншот.
- Автоматизация Android: нажать, свайпнуть, ввести текст, открыть приложение.
- Проверить состояние устройства (батарея, температура, foreground-приложение).
- Управление телефоном по сети (Wi-Fi / VPN / Tailscale), не только по USB.

## Установка и подключение к Hermes

Сервер запускается как обычный MCP-сервер. В `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  android:
    command: python
    args: ["-m", "android_mcp"]
    env:
      ANDROID_MCP_SERIAL: "192.168.10.210:5555"   # опц.: устройство по умолчанию
```

Для удалённого доступа (агент и телефон в разных сетях) — HTTP-транспорт:

```yaml
mcp_servers:
  android:
    url: "http://<host>:8000/mcp"
```

После правки конфига — перезагрузить gateway: `hermes gateway reload` (или перезапуск).
Инструменты появятся с префиксом клиента (обычно `mcp_android_*`).

Проверка живости:
```bash
ANDROID_MCP_SERIAL=<serial> python scripts/smoke_mcp.py
```

## Инструменты

| Инструмент | Что делает |
|---|---|
| `device_list` | список подключённых устройств (USB/Wi-Fi) |
| `screenshot` | скриншот **как изображение** (агент видит экран) |
| `device_state` | батарея %, температура, экран, foreground-приложение |
| `device_capabilities` | **доктор**: что разрешает ROM (screenshot/input/ui_dump/app_control) |
| `dump_ui` | UI-дерево: интерактивные + подписанные элементы (индекс, координаты, подпись) |
| `tap` / `tap_text` | тап по координатам / по тексту элемента |
| `swipe` | свайп (x1,y1)→(x2,y2), длительность |
| `type_text` | ввод текста в активное поле |
| `press_key` | back/home/recents/menu/power/wakeup/enter/delete/volume/camera/call |
| `wake` | разбудить экран |
| `app_launch` / `app_stop` / `app_list` | запуск/стоп/список приложений |

## Рабочий цикл (как действовать)

1. **Оценить обстановку:** `device_list` → `device_capabilities` → `device_state`.
   Если `device_capabilities` показывает ❌ по `input_inject` — тапать не получится (см. Проблемы).
2. **Посмотреть экран:** `screenshot` (возвращает изображение) — принимай решения по картинке.
3. **Действие:** `tap`/`tap_text`/`swipe`/`type_text`/`press_key`.
4. **Проверить результат:** снова `screenshot` или `device_state` (foreground сменился?).

Цикл «увидел → нажал → проверил». Не полагайся вслепую на координаты — сверяйся со скриншотом.

## Проблемы и решения (важно)

- **MIUI блокирует `input`** (`INJECT_EVENTS` без «Отладки по USB (настройки безопасности)»).
  Симптом: `tap/swipe/type_text` возвращают ошибку про INJECT_EVENTS. Решение — включить
  этот тумблер в *Для разработчиков* (нужен Mi-аккаунт) либо root. Проверяй `device_capabilities`.
- **`uiautomator dump` медленный/нестабильный** — на некоторых ROM падает
  («could not get idle state»). Приоритет — `screenshot`; `dump_ui` — как дополнение.
- **Android < 11**: нет современного wireless-pairing → `adb tcpip 5555` (включается по USB,
  слетает при перезагрузке).
- **Несколько устройств**: задавай `serial` явно или ставь `ANDROID_MCP_SERIAL`.
- **Безопасность**: ADB даёт полный доступ к телефону — только доверенная сеть/туннель.
  Не выполняй платежи/удаления без подтверждения пользователя.

## Examples

Разблокировать и открыть приложение:
```
wake()
swipe(540, 1800, 540, 600, 300)     # свайп вверх
type_text("1234")                    # PIN, если есть
app_launch("com.android.settings")
screenshot()                         # убедиться, что открылось
```

Узнать, что на экране и нажать по тексту:
```
screenshot()
tap_text("Wi-Fi")
```
