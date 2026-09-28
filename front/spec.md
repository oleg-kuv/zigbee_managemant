# Спецификация интерфейса: Админ-панель Zigbee-проекта

> Документ описывает интерфейс раздела **«Управление»** и общий каркас приложения. Спецификация составлена на основе утверждённого брифа и текущей реализации и является источником истины для дизайна и вёрстки.

---

## 1. Общие сведения

| Параметр | Значение |
|---|---|
| Продукт | Админ-панель управления Zigbee-устройствами (умный дом / IoT) |
| Разделы | «Показатели» (не в разработке), «Управление» (в разработке) |
| Платформы | Desktop, Mobile (адаптив) |
| Стиль | Минималистичный, светлый, «чистый» |
| Шрифт | Inter (400 / 500 / 600) |
| Язык интерфейса | Русский |

---

## 2. Каркас приложения

```
┌───────────┬────────────────────────────────────────┐
│           │  [Mobile topbar — только ≤640px]       │
│  Sidebar  ├────────────────────────────────────────┤
│           │                                        │
│           │  Main (контентная область)             │
│           │                                        │
└───────────┴────────────────────────────────────────┘
```

- **Sidebar** — слева, фиксированная ширина, вертикальный flex.
- **Content wrapper** — занимает оставшееся пространство.
- **Mobile topbar** — виден только на ширине ≤ 640px, sticky, содержит кнопку меню, логотип, статус системы и аватар.

### 2.1. Breakpoints

| Диапазон | Поведение |
|---|---|
| > 1280px | 6 колонок плиток, сайдбар развёрнут/свёрнут по кнопке |
| 1081–1280px | 5 колонок |
| 861–1080px | 4 колонки |
| 641–860px | 3 колонки |
| ≤ 640px | 2 колонки, сайдбар = выезжающий drawer, появляется mobile topbar |

---

## 3. Сайдбар (Sidebar)

### 3.1. Общие параметры

| Параметр | Значение |
|---|---|
| Ширина (expanded) | `240px` |
| Ширина (collapsed) | `64px` |
| Padding | `20px 12px` |
| Граница справа | `1px solid #E5E7EB` |
| Фон | `#FFFFFF` |
| Анимация ширины | `0.22s cubic-bezier(0.4, 0, 0.2, 1)` |
| z-index | 20 (desktop) / 100 (mobile drawer) |

### 3.2. Структура

1. **Brand** (логотип + название «Zigbee Home»)
2. **Nav** — список пунктов меню (flex: 1)
3. **Footer** — кнопка «Свернуть/Развернуть»

#### Brand

| Параметр | Значение |
|---|---|
| Padding | `8px 12px 24px` |
| Gap | `10px` |
| Иконка | 20×20, `currentColor` |
| Текст | 16px / 600 / `#112937` |

#### Nav item

| Параметр | Значение |
|---|---|
| Padding | `10px 12px` |
| Gap | `12px` |
| Радиус | `8px` |
| Иконка | 20×20 |
| Текст | 14px / 500 |
| Цвет (default) | `#6B7280` |
| Цвет (hover) | текст `#111827`, фон `#F3F4F6` |
| Цвет (active) | текст `#111827`, фон `#F3F4F6`, вес 600 |

Пункты меню (минимум):
- **Показатели** — иконка графика
- **Управление** — иконка power (активный по умолчанию)

#### Кнопка «Свернуть»

| Параметр | Значение |
|---|---|
| Позиция | В footer, отделена `border-top: 1px solid #E5E7EB` |
| Padding | `10px 12px` |
| Gap | `10px` |
| Радиус | `8px` |
| Иконка | Шеврон 18×18 |
| Текст | 14px / 400, «Свернуть» / «Развернуть» |
| Hover | фон `#F3F4F6`, текст `#111827` |

### 3.3. Состояния сайдбара

| Состояние | Ширина | Контент | Иконка шеврона |
|---|---|---|---|
| Expanded | 240px | Иконка + текст | Направлена влево |
| Collapsed | 64px | Только иконки, центрированы | Повёрнута на 180° (вправо) |

Поведение в collapsed:
- Текст скрывается (`opacity: 0; width: 0; overflow: hidden`).
- Все элементы центрируются (`justify-content: center; padding: 10px; gap: 0`).
- У nav-item появляется `title` с названием раздела.
- Кнопка меняет подпись на «Развернуть».

### 3.4. Сохранение состояния

Состояние сайдбара (свёрнут/развёрнут) хранится в `localStorage` под ключом `zigbee.sidebar.collapsed` и восстанавливается при загрузке.

---

## 4. Mobile topbar (≤ 640px)

| Параметр | Значение |
|---|---|
| Padding | `12px 16px` |
| Граница снизу | `1px solid #E5E7EB` |
| Позиция | sticky top: 0, z-index: 30 |
| Слева | Кнопка-гамбургер (36×36, радиус 8) + «Zigbee Home» (15px / 600 / `#112937`) |
| Справа | Статус-индикатор «Система онлайн» (12px) + аватар (36×36) |

### 4.1. Мобильный drawer сайдбара

- Сайдбар скрыт по умолчанию (`transform: translateX(-100%)`).
- Открывается по кнопке-гамбургеру: `translateX(0)`, ширина 240px (max 82vw).
- Появляется полупрозрачный backdrop: `rgba(17, 41, 55, 0.35)`, z-index 90.
- Закрытие: клик по backdrop, по пункту меню, по кнопке «Свернуть», клавиша **Esc**.
- При открытии блокируется скролл body (`no-scroll`).
- Фокус переходит на первый пункт меню; при закрытии — возвращается на гамбургер.

---

## 5. Экран «Управление»

### 5.1. Page header

| Элемент | Параметры |
|---|---|
| Заголовок «Управление» | 24px / 600 / `#112937`, `letter-spacing: -0.01em` |
| Подзаголовок | 14px / 400 / `#6B7280`, «Управляйте Zigbee-реле и следите за их состоянием» |
| Отступ снизу | `20px` |
| Справа | Статус-индикатор «Система онлайн» + аватар 36×36 (круг, `border: 1px solid #E5E7EB`) |

На мобильном header складывается в колонку, заголовок — 20px.

### 5.2. Легенда состояний

| Параметр | Значение |
|---|---|
| Отображение | Горизонтальный flex-контейнер, wrap |
| Gap | `10px` (mobile: 8px) |
| Отступ снизу | `24px` (mobile: 16px) |

Элемент легенды:

| Параметр | Значение |
|---|---|
| Padding | `6px 12px` (mobile: 5px 10px) |
| Радиус | `999px` |
| Граница | `1px solid #E5E7EB` |
| Фон | `#FFFFFF` |
| Текст | 13px / 400 / `#6B7280` (mobile: 12px) |
| Содержимое | StatusDot + подпись |

Пункты: «Включено» (зелёный), «Выключено» (белый), «Неизвестно» (серый).

---

## 6. Сетка плиток (Tiles grid)

| Параметр | Desktop | Mobile (≤640px) |
|---|---|---|
| Колонок | 6 | 2 |
| Gap | 24px | 16px |
| Промежуточные | 5 (≤1280) / 4 (≤1080) / 3 (≤860) | — |

Сетка: `grid-template-columns: repeat(N, minmax(0, 1fr))`.

---

## 7. Компонент «Плитка реле» (Tile)

### 7.1. Анатомия

```
┌──────────────────────────────┐
│  Имя реле          [Обновить]│  ← tile__head
│  ● Включено                  │  ← tile__status
│         ( ⏻ )                │  ← power-btn (ToggleZone)
└──────────────────────────────┘
```

### 7.2. Контейнер плитки

| Параметр | Desktop | Mobile |
|---|---|---|
| Padding | `16px` | `14px` |
| Gap внутри | `10px` | `8px` |
| Радиус | `12px` | `12px` |
| Граница | `1px solid #E5E7EB` | — |
| Фон | `#FFFFFF` | — |
| Hover | `border-color: #D1D5DB`, тень `0 1px 3px rgba(17,41,55,0.04)` | — |
| Transition | `border-color .18s, box-shadow .18s, background .18s` | — |

### 7.3. Имя реле (tile__name)

| Параметр | Desktop | Mobile |
|---|---|---|
| Размер | 16px / 500 / `#111827` | 15px |
| Line-height | 1.3 | — |
| Обрезка | `text-overflow: ellipsis`, `white-space: nowrap` | — |

### 7.4. Строка статуса (tile__status)

- Flex, gap `8px`, размер 14px (mobile: 13px), цвет `#6B7280`.
- Состав: `StatusDot` + текст состояния.
- Текст состояния обновляется в зависимости от `state`.

### 7.5. StatusDot

| Состояние | Фон | Граница |
|---|---|---|
| **on** (Включено) | `#22C55E` | нет |
| **off** (Выключено) | `#FFFFFF` | `1.5px solid #D1D5DB` |
| **unknown** (Неизвестно) | `#9CA3AF` | нет |

Размер: `8 × 8 px`, `border-radius: 50%`, `box-sizing: border-box`.

### 7.6. Кнопка «Обновить» (RefreshButton)

| Параметр | Desktop | Mobile |
|---|---|---|
| Размер | 28×28 | 26×26 |
| Радиус | `6px` | — |
| Иконка | 16×16 | 15×15 |
| Цвет (default) | `#9CA3AF` | — |
| Фон (default) | прозрачный | — |
| Hover | фон `#F3F4F6`, цвет `#374151` | — |
| Active | фон `#E5E7EB` | — |
| Loading | иконка вращается `spin 0.8s linear infinite`, кнопка disabled (`opacity: 0.45`) | — |

### 7.7. Кнопка питания / ToggleZone (power-btn)

| Параметр | Desktop | Mobile |
|---|---|---|
| Размер | 56×56, круг | 48×48 |
| Иконка ⏻ | 24×24 | 22×22 |
| Отступ сверху | `6px auto 0` (центрирование) | — |
| Active | `transform: scale(0.96)` | — |
| Transition | `background .18s, color .18s, border-color .18s, transform .1s` | — |

---

## 8. Состояния плитки

| Состояние | Граница плитки | Текст статуса | Power-кнопка |
|---|---|---|---|
| **tile--on** | `#BBF7D0` | `#16A34A` | фон `#DCFCE7`, граница `#BBF7D0`, иконка `#16A34A`; hover фон `#BBF7D0` |
| **tile--off** | `#E5E7EB` | `#6B7280` | фон `#FFFFFF`, граница `#E5E7EB`, иконка `#6B7280`; hover фон `#F9FAFB`, граница `#D1D5DB` |
| **tile--unknown** | пунктир `1px dashed #D1D5DB`, фон `#F9FAFB` | `#9CA3AF` | фон `#F3F4F6`, пунктир `#D1D5DB`, иконка `#9CA3AF`; hover фон `#E5E7EB` |
| **is-loading** | — | анимация `pulse 1.1s` (opacity 1 → 0.3 → 1) | disabled |

---

## 9. Логика взаимодействия

### 9.1. Клик по power-кнопке (ToggleZone)

1. Если реле занято (`busy`) — игнорируется.
2. Иначе состояние переключается: `on ↔ off`.
3. Из `unknown` переключается в `on`.
4. Обновляется `device` и `state`, перерисовывается плитка.

### 9.2. Клик по кнопке «Обновить»

1. Если реле занято — игнорируется.
2. Ставится флаг `busy = true`.
3. `state` становится `unknown` — индикатор сразу показывает «Неизвестно».
4. Включается режим `is-loading`: спиннер на кнопке, кнопки disabled, пульсация статуса.
5. Выполняется асинхронный запрос состояния (эмуляция 700–1200 мс).
6. По завершении `state` = фактическое состояние (или `unknown` при ошибке), режим loading снимается, плитка перерисовывается.

### 9.3. Клавиатура и доступность

- Управление доступно с клавиатуры (нативные `<button>`).
- `aria-pressed` на power-кнопке отражает `on/off`.
- `aria-live="polite"` на тексте состояния.
- `aria-busy` на кнопке обновления во время загрузки.
- Esc закрывает мобильный drawer.

---

## 10. Токены дизайна

### 10.1. Цвета

| Токен | HEX | Применение |
|---|---|---|
| `--white` | `#FFFFFF` | Основной фон |
| `--grey-50` | `#F9FAFB` | Фон unknown-плитки, hover off |
| `--grey-100` | `#F3F4F6` | Hover-фон элементов |
| `--grey-200` | `#E5E7EB` | Границы, разделители |
| `--grey-300` | `#D1D5DB` | Границы hover/пунктир |
| `--grey-400` | `#9CA3AF` | Иконки, unknown-индикатор |
| `--grey-500` | `#6B7280` | Вторичный текст |
| `--text-1` | `#112937` | Заголовки, бренд |
| `--text-2` | `#111827` | Основной текст, hover |
| `--text-3` | `#374151` | Hover иконок |
| `--text-4` | `#6B7280` | Вторичный текст |
| `--green` | `#22C55E` | Индикатор «Включено» |
| `--green-600` | `#16A34A` | Текст/иконка «Включено» |
| `--green-soft` | `#DCFCE7` | Фон power-кнопки on |
| `--green-border` | `#BBF7D0` | Граница плитки/кнопки on |

### 10.2. Типографика (Inter)

| Стиль | Размер | Вес | Применение |
|---|---|---|---|
| H1 | 24px (mobile 20px) | 600 | Заголовок страницы |
| Body | 14px | 400 | Подзаголовки, статусы |
| Tile name | 16px (mobile 15px) | 500 | Имя реле |
| Nav item | 14px | 500 | Пункты меню |
| Brand | 16px | 600 | Логотип |
| Legend | 13px (mobile 12px) | 400 | Легенда |

### 10.3. Радиусы

| Токен | Значение |
|---|---|
| `--radius-sm` | `8px` |
| `--radius-md` | `12px` |
| Круглые элементы | `50%` |
| Pill (легенда) | `999px` |

### 10.4. Тени

| Применение | Значение |
|---|---|
| Плитка hover | `0 1px 3px rgba(17, 41, 55, 0.04)` |
| Мобильный drawer | `0 10px 40px rgba(17, 41, 55, 0.18)` |

---

## 11. Чек-лист компонентов (для Figma)

- [ ] `Sidebar` — expanded / collapsed
- [ ] `SidebarItem` — default / hover / active
- [ ] `SidebarCollapseButton` — expanded / collapsed
- [ ] `MobileTopbar` — с гамбургером и статусом
- [ ] `Tile` — default / hover / on / off / unknown / loading
- [ ] `ToggleZone` (power-btn) — on / off / unknown / hover / active / disabled
- [ ] `RefreshButton` — default / hover / active / loading / disabled
- [ ] `StatusDot` — on / off / unknown
- [ ] `Legend` — три состояния
- [ ] `PageHeader` — desktop / mobile
- [ ] `Backdrop` — мобильный drawer
- [ ] `Avatar` — 36×36

---

## 12. Требования к вёрстке

1. Адаптив от 320px до 1920px+.
2. Плавные переходы сайдбара — `0.22s cubic-bezier(0.4, 0, 0.2, 1)`.
3. Все интерактивные элементы — нативные `<button>` с фокусом.
4. Состояние сайдбара сохраняется между сессиями.
5. Никаких горизонтальных скроллов на мобильных.
6. Сетка плиток перестраивается без разрывов на всех breakpoints.
7. Логика состояний (loading, unknown, busy) — обязательна к реализации в UI-ките.
8. Все цвета, типографика, радиусы и тени должны быть описаны в едином файле токенов
   (CSS custom properties / SCSS-переменные) и использоваться в компонентах только через них.
   Хардкод цветов, размеров шрифта, радиусов и теней в компонентах не допускается.

## 13. Компонентная архитектура Vue 3

### 13.1. Дерево компонентов

```text
App.vue
└── AdminLayout.vue
    ├── Sidebar.vue
    │   ├── SidebarBrand.vue
    │   │   └── BrandLogo.vue
    │   ├── SidebarNav.vue
    │   │   └── SidebarItem.vue (v-for)
    │   └── SidebarFooter.vue
    │       └── SidebarCollapseButton.vue
    ├── MobileTopbar.vue
    │   ├── MobileMenuButton.vue
    │   ├── BrandLogo.vue
    │   ├── SystemStatus.vue
    │   └── UserAvatar.vue
    ├── Backdrop.vue
    └── MainContent.vue
        └── RouterView
            └── ControlPage.vue
                ├── PageHeader.vue
                │   ├── SystemStatus.vue
                │   └── UserAvatar.vue
                ├── StatusLegend.vue
                │   └── LegendItem.vue (v-for)
                │       └── StatusDot.vue
                └── TilesGrid.vue
                    └── RelayTile.vue (v-for)
                        ├── TileHead.vue
                        │   ├── TileName.vue
                        │   └── RefreshButton.vue
                        ├── TileStatus.vue
                        │   └── StatusDot.vue
                        └── PowerButton.vue
```

### 13.2. Таблица компонентов

| Компонент | Родитель | Описание |
|---|---|---|
| `App.vue` | — | Корневой компонент. Подключает глобальные стили, токены, шрифт Inter, роутер и `AdminLayout`. |
| `AdminLayout.vue` | `App.vue` | Каркас приложения: сайдбар, mobile topbar, backdrop, контентная область. Управляет `sidebarCollapsed`, `mobileDrawerOpen`, блокировкой скролла и закрытием по Esc. |
| `Sidebar.vue` | `AdminLayout.vue` | Левый сайдбар. Ширина 240/64px, анимация `0.22s`, desktop/mobile drawer, z-index 20/100. Принимает `collapsed`, `mobileOpen`; emits `toggle-collapse`, `close`. |
| `SidebarBrand.vue` | `Sidebar.vue` | Бренд-блок сайдбара: логотип + «Zigbee Home». В collapsed скрывает текст. |
| `BrandLogo.vue` | `SidebarBrand.vue`, `MobileTopbar.vue` | Иконка логотипа 20×20 и, опционально, текст бренда. Принимает `showText`, `size`. |
| `SidebarNav.vue` | `Sidebar.vue` | Навигационный список пунктов меню. Содержит `SidebarItem` для «Показатели» и «Управление». |
| `SidebarItem.vue` | `SidebarNav.vue` | Пункт меню: иконка, текст, active/hover, `title` в collapsed. Принимает `label`, `icon`, `active`, `collapsed`; emits `select`. |
| `SidebarFooter.vue` | `Sidebar.vue` | Нижняя зона сайдбара с `border-top: 1px solid #E5E7EB`. Содержит кнопку сворачивания. |
| `SidebarCollapseButton.vue` | `SidebarFooter.vue` | Кнопка «Свернуть/Развернуть». Меняет иконку шеврона и подпись; emits `toggle`. |
| `MobileTopbar.vue` | `AdminLayout.vue` | Верхняя панель ≤640px: гамбургер, бренд, статус системы, аватар. Sticky, z-index 30. Emits `open-menu`. |
| `MobileMenuButton.vue` | `MobileTopbar.vue` | Кнопка-гамбургер 36×36. Открывает drawer; при закрытии фокус возвращается на неё. |
| `Backdrop.vue` | `AdminLayout.vue` | Полупрозрачная подложка мобильного drawer: `rgba(17, 41, 55, 0.35)`, z-index 90. Закрытие по клику. |
| `MainContent.vue` | `AdminLayout.vue` | Контентная область, занимает оставшееся пространство. Содержит `RouterView`. |
| `ControlPage.vue` | `MainContent.vue` / `RouterView` | Экран «Управление»: `PageHeader`, `StatusLegend`, `TilesGrid`. |
| `PageHeader.vue` | `ControlPage.vue` | Заголовок «Управление», подзаголовок, статус системы и аватар. На mobile складывается в колонку. Принимает `title`, `subtitle`. |
| `SystemStatus.vue` | `MobileTopbar.vue`, `PageHeader.vue` | Индикатор «Система онлайн» 12px с цветовой точкой. Принимает `online`, `label`. |
| `UserAvatar.vue` | `MobileTopbar.vue`, `PageHeader.vue` | Аватар 36×36, круг, `border: 1px solid #E5E7EB`. Принимает `src`, `alt`. |
| `StatusLegend.vue` | `ControlPage.vue` | Горизонтальный flex-контейнер легенды состояний. Содержит `LegendItem`. |
| `LegendItem.vue` | `StatusLegend.vue` | Pill-элемент легенды: `StatusDot` + подпись. Принимает `state`, `label`. |
| `StatusDot.vue` | `LegendItem.vue`, `TileStatus.vue` | Точка 8×8 для состояний `on` / `off` / `unknown`. Принимает `state`. |
| `TilesGrid.vue` | `ControlPage.vue` | Сетка плиток: 6/5/4/3/2 колонки по breakpoints, gap 24/16px. Принимает `devices`; emits `toggle`, `refresh`. |
| `RelayTile.vue` | `TilesGrid.vue` | Плитка реле. Состояния: `tile--on`, `tile--off`, `tile--unknown`, `is-loading`. Принимает `device`, `state`, `busy`, `loading`; emits `toggle`, `refresh`. |
| `TileHead.vue` | `RelayTile.vue` | Верхняя строка плитки: имя реле + кнопка обновления. |
| `TileName.vue` | `TileHead.vue` | Имя реле: 16px / 500 / `#111827`, mobile 15px, обрезка `ellipsis`. Принимает `name`. |
| `RefreshButton.vue` | `TileHead.vue` | Кнопка обновления 28×28 / 26×26. Состояния: default, hover, active, loading, disabled. Принимает `loading`, `disabled`; emits `refresh`. |
| `TileStatus.vue` | `RelayTile.vue` | Строка статуса: `StatusDot` + текст состояния. `aria-live="polite"`. Принимает `state`. |
| `PowerButton.vue` / `ToggleZone.vue` | `RelayTile.vue` | Круглая кнопка питания 56×56 / 48×48. Состояния on/off/unknown, hover/active/disabled. Принимает `state`, `busy`; emits `toggle`. `aria-pressed` отражает состояние. |
| `AppIcon.vue` | `SidebarItem.vue`, `SidebarCollapseButton.vue`, `MobileMenuButton.vue`, `RefreshButton.vue`, `PowerButton.vue` | Базовая SVG-иконка: принимает `name`, `size`, `color`. Используется для единообразия иконок. |

### 13.3. Краткие примечания по реализации

- Использовать Vue 3 `<script setup>` и Composition API.
- Состояние сайдбара хранить в `useSidebar` + `localStorage` (`zigbee.sidebar.collapsed`).
- Состояние реле и `busy`/`loading` удобно держать в `useRelays` или Pinia-сторе.
- `TilesGrid` отвечает только за раскладку, `RelayTile` — за состояние конкретного реле.
- Все интерактивные элементы — нативные `<button>`.
- Обязательные атрибуты доступности: `aria-pressed`, `aria-live`, `aria-busy`, закрытие drawer по Esc.
