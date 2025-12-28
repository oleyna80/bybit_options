# Bybit Options Portfolio Risk Analyzer - Frontend

React-based web interface для анализа опционного портфеля на Bybit с real-time обновлениями и визуализацией рисков.

## Функциональность

- **Доска опционов**: Просмотр и фильтрация доступных опционов по экспирации, типу и параметрам
- **Портфель**: Отображение текущих позиций с детальными Greek'ами и метриками риска
- **Графики P&L**: Интерактивные графики payoff при изменении цены актива
- **Метрики риска**: Агрегированные дельта, гамма, вега, тета для портфеля
- **Экспорт данных**: Экспорт портфеля в JSON, Markdown, CSV форматы
- **Real-time обновления**: WebSocket соединение для получения live обновлений

## Требования

- Node.js 18+
- npm или yarn
- Backend API на `http://localhost:8000`

## Установка

```bash
# Установка зависимостей
npm install

# Или с yarn
yarn install
```

## Development

### Запуск dev сервера

```bash
npm run dev
# или
yarn dev
```

Приложение будет доступно по адресу `http://localhost:3001`

### Конфигурация API

По умолчанию frontend подключается к API на `http://localhost:8000/api/v1`.

Для изменения URL API, отредактируйте переменную в [`src/services/api.ts`](src/services/api.ts):

```typescript
const API_BASE_URL = 'http://ваш-backend:8000/api/v1';
```

Или используйте переменную окружения `VITE_API_URL`:

```bash
VITE_API_URL=http://api.example.com npm run dev
```

## Build для Production

```bash
# Сборка оптимизированного bundle
npm run build

# Проверка bundle размера
npm run preview
```

Build результаты будут в папке `dist/`.

## Структура проекта

```
frontend/
├── src/
│   ├── components/          # React компоненты
│   │   ├── Charts/          # Графики (Recharts)
│   │   ├── Common/          # Общие компоненты (UI)
│   │   ├── OptionsBoard/    # Доска опционов
│   │   ├── Portfolio/       # Портфель и метрики
│   │   └── TradeLog/        # История сделок
│   ├── services/            # API и WebSocket клиенты
│   │   ├── api.ts           # REST API клиент
│   │   ├── websocket.ts     # WebSocket клиент
│   │   └── export.ts        # Экспорт данных
│   ├── stores/              # State management (Zustand)
│   │   └── portfolioStore.ts
│   ├── types/               # TypeScript типы
│   ├── App.tsx              # Главный компонент
│   ├── index.tsx            # Entry point
│   └── index.css            # Глобальные стили
├── public/                  # Статические файлы
├── Dockerfile               # Docker конфигурация
├── vite.config.ts           # Vite конфигурация
├── tailwind.config.js       # Tailwind CSS конфигурация
├── tsconfig.json            # TypeScript конфигурация
├── package.json
└── README.md
```

## Компоненты

### OptionsBoard
Таблица с доступными опционами. Поддерживает:
- Фильтрацию по экспирации и типу
- Сортировку по страйку, цене, дельте и IV
- Отображение bid/ask спреда и ликвидности

### Portfolio
Список текущих позиций с:
- Греческими параметрами (Delta, Gamma, Vega, Theta)
- Выручкой/убытками (PnL)
- Процентом использованной маржи

### PayoffChart
Интерактивный график P&L портфеля при различных ценах:
- Точки безубыточности (breakeven)
- Максимальная прибыль и убытки
- С учетом theta decay

### MetricsCards
Карточки с агрегированными метриками:
- Total Delta, Gamma, Vega, Theta
- Маржин ratio
- Текущий PnL

## State Management

Используется **Zustand** для управления состоянием. Store находится в [`src/stores/portfolioStore.ts`](src/stores/portfolioStore.ts).

### Actions

- `fetchPortfolio()` - Загрузить портфель
- `fetchPositions()` - Загрузить позиции
- `subscribeToWebSocket()` - Подписаться на real-time обновления
- `setSelectedExpiry()` - Выбрать экспирацию
- `exportData()` - Экспортировать данные

## API Integration

Frontend общается с backend через:

### REST Endpoints
- `GET /api/v1/risk/portfolio` - Портфель с Greeks
- `GET /api/v1/positions` - Список позиций
- `GET /api/v1/options-board` - Доска опционов
- `GET /api/v1/payoff-chart` - Данные для графика P&L
- `GET /api/v1/trade-log` - История сделок
- `GET /api/v1/export?format=json|md|csv` - Экспорт данных

### WebSocket
- `ws://localhost:8000/ws/portfolio` - Real-time обновления портфеля

## Стили

Проект использует **Tailwind CSS** для стилизации.

Конфигурация: [`tailwind.config.js`](tailwind.config.js)

Глобальные стили: [`src/index.css`](src/index.css)

## Тестирование

```bash
# Запуск тестов (если есть)
npm run test
```

## Производительность

- Кэширование API запросов на клиенте (10-60 сек TTL)
- Debouncing WebSocket обновлений
- Code splitting с lazy loading компонентов
- Optimized bundle с tree-shaking

## Проблемы и решения

### WebSocket не подключается
- Проверьте, что backend запущен на `http://localhost:8000`
- Убедитесь, что CORS настроен правильно

### API возвращает 404
- Проверьте, что API endpoint правильно настроен в `src/services/api.ts`
- Используйте правильный формат URL

## Docker

Для запуска в Docker контейнере:

```bash
docker build -t bybit-frontend .
docker run -p 3001:3001 bybit-frontend
```

Или через docker-compose:

```bash
docker-compose up frontend
```

## Переменные окружения

Поддерживаемые переменные для development и production:

```bash
# API endpoint
VITE_API_URL=http://localhost:8000/api/v1

# Node environment
NODE_ENV=development|production
```

## Версионирование

- Frontend: v1.0.0
- React: 18.x
- Vite: 5.x
- TypeScript: 5.x

## Лицензия

MIT

## Контакты

Для вопросов и предложений обратитесь к разработчикам проекта.
