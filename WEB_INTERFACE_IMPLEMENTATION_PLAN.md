# План реализации веб-интерфейса для анализа опционного портфеля Bybit

## 🎯 Цель проекта
Создать веб-приложение для визуализации опционного портфеля, отображения доски опционов и анализа позиций с интеграцией существующей backend-инфраструктуры.

## 📊 Текущее состояние

### Реализованные компоненты (backend):
1. **`option_board_utils.py`** - Утилиты для работы с опционами
2. **`get_option_board.py`** - CLI для доски опционов
3. **`get_option_board_json.py`** - JSON экспорт для ИИ-агента
4. **Существующая инфраструктура**:
   - `bybit_connector.py` - API клиент Bybit
   - `risk_engine.py` - Расчет Greeks
   - `live_state_keeper.py` - Real-time обновления
   - `trade_logger.py` - Логирование в Google Sheets

### Требуется реализовать (согласно ТЗ):
1. **Веб-интерфейс** (React + TypeScript)
2. **Real-time WebSocket** обновления
3. **Графики P&L** (payoff diagrams)
4. **Интеграция всех компонентов**

## 🏗️ Архитектура системы

### Backend (Python/FastAPI)
```
bybit-options-risk-engine/
├── api_example.py              # Существующий API (расширить)
├── websocket_manager.py        # Новый: WebSocket broadcast
├── payoff_calculator.py        # Новый: Расчет P&L графиков
├── option_board_utils.py       # ✅ Готово
├── bybit_connector.py          # ✅ Готово
├── risk_engine.py              # ✅ Готово
├── live_state_keeper.py        # ✅ Готово (модифицировать)
└── trade_logger.py             # ✅ Готово
```

### Frontend (React/TypeScript)
```
frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── OptionsBoard/       # Доска опционов
│   │   ├── Portfolio/          # Портфель и метрики
│   │   ├── Charts/             # Графики P&L
│   │   ├── TradeLog/           # Журнал сделок
│   │   └── Common/             # Общие компоненты
│   ├── services/
│   │   ├── api.ts              # REST API клиент
│   │   ├── websocket.ts        # WebSocket клиент
│   │   └── export.ts           # Экспорт данных
│   ├── stores/
│   │   └── portfolioStore.ts   # State management
│   ├── types/
│   │   └── index.ts            # TypeScript типы
│   └── utils/
│       └── formatters.ts       # Форматирование данных
```

## 📋 Детальный план реализации

### Этап 1: Backend расширение (Неделя 1)

#### 1.1 Создать `payoff_calculator.py`
```python
"""
Модуль для расчета P&L графиков портфеля
"""

import numpy as np
from typing import List, Dict, Any
from data_models import PositionModel, PositionSide, PositionType, OptionType

def calculate_payoff_at_expiry(
    positions: List[PositionModel],
    price_range: np.ndarray,
    include_theta: bool = False
) -> Dict[str, Any]:
    """
    Рассчитывает P&L портфеля при различных ценах на экспирацию
    
    Args:
        positions: Список позиций
        price_range: Массив цен для расчета
        include_theta: Учитывать временной распад
        
    Returns:
        Словарь с данными для графика
    """
    pnl = np.zeros_like(price_range)
    
    for pos in positions:
        if pos.pos_type == PositionType.OPTION:
            # Расчет intrinsic value опциона
            if pos.option_type == OptionType.CALL:
                intrinsic = np.maximum(0, price_range - pos.strike)
            else:  # PUT
                intrinsic = np.maximum(0, pos.strike - price_range)
            
            # Учет стороны позиции (Buy/Sell)
            if pos.side == PositionSide.BUY:
                position_pnl = (intrinsic - pos.entry_price) * pos.size
            else:  # SELL
                position_pnl = (pos.entry_price - intrinsic) * pos.size
            
            # Учет временного распада (theta)
            if include_theta and pos.theta:
                days_to_expiry = pos.days_to_expiry
                theta_effect = pos.theta * days_to_expiry
                position_pnl -= theta_effect
            
            pnl += position_pnl
        
        elif pos.pos_type == PositionType.LINEAR:
            # Позиции в фьючерсах/споте
            price_change = price_range - pos.entry_price
            if pos.side == PositionSide.BUY:
                position_pnl = price_change * pos.size
            else:  # SELL
                position_pnl = -price_change * pos.size
            
            pnl += position_pnl
    
    # Найти точки безубыточности
    breakeven_points = find_breakeven_points(price_range, pnl)
    
    return {
        "price_range": price_range.tolist(),
        "pnl": pnl.tolist(),
        "breakeven_points": breakeven_points,
        "max_profit": float(np.max(pnl)),
        "max_loss": float(np.min(pnl)),
        "current_price_index": np.argmin(np.abs(price_range - get_current_price()))
    }
```

#### 1.2 Создать `websocket_manager.py`
```python
"""
WebSocket менеджер для real-time обновлений
"""

import asyncio
from typing import Set, Dict, Any
from fastapi import WebSocket
from live_state_keeper import LiveStateKeeper

class WebSocketManager:
    """Управление WebSocket соединениями"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.live_state_keeper = LiveStateKeeper()
    
    async def connect(self, websocket: WebSocket):
        """Подключение нового клиента"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Отправить текущее состояние
        portfolio = self.live_state_keeper.get_portfolio_snapshot()
        await websocket.send_json(portfolio.dict())
    
    def disconnect(self, websocket: WebSocket):
        """Отключение клиента"""
        self.active_connections.remove(websocket)
    
    async def broadcast_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """Рассылка обновления портфеля всем клиентам"""
        if not self.active_connections:
            return
        
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(portfolio_data)
            except Exception:
                dead_connections.add(connection)
        
        # Очистка отключенных соединений
        for connection in dead_connections:
            self.disconnect(connection)
    
    async def start_broadcast_loop(self):
        """Запуск цикла рассылки обновлений"""
        while True:
            portfolio = self.live_state_keeper.get_portfolio_snapshot()
            await self.broadcast_portfolio_update(portfolio.dict())
            await asyncio.sleep(5)  # Обновление каждые 5 секунд
```

#### 1.3 Расширить `api_example.py`
```python
# Добавить новые endpoints

@app.get("/api/v1/options-board")
async def get_options_board(
    base_coin: str = "BTC",
    expiry: Optional[str] = None,
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """
    Возвращает доску опционов с фильтрацией по экспирации
    
    Формат ответа соответствует требованиям ТЗ для ИИ-агента
    """
    # Получить все опционы для базового актива
    tickers = await orchestrator.market_data.fetch_option_greeks({base_coin})
    
    # Фильтрация по экспирации
    if expiry:
        tickers = {
            sym: data for sym, data in tickers.items()
            if expiry in sym
        }
    
    # Получить текущую цену underlying
    underlying_price = await orchestrator.market_data.get_underlying_price(base_coin)
    
    # Форматировать данные
    board_data = format_options_board(tickers, underlying_price)
    
    return board_data


@app.get("/api/v1/payoff-chart")
async def get_payoff_chart(
    days_to_expiry: Optional[int] = None,
    price_range_pct: float = 20.0,
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator)
):
    """
    Возвращает данные для графика P&L на экспирацию
    
    Args:
        days_to_expiry: Дней до экспирации (None = ближайшая)
        price_range_pct: Диапазон цен в % от текущей
    """
    # Получить портфель
    portfolio = await orchestrator.run_full_analysis()
    
    # Текущая цена underlying
    current_price = portfolio.underlying_prices.get("BTC", 0)
    
    # Диапазон цен для расчета
    min_price = current_price * (1 - price_range_pct / 100)
    max_price = current_price * (1 + price_range_pct / 100)
    price_range = np.linspace(min_price, max_price, 100)
    
    # Расчет P&L
    from payoff_calculator import calculate_payoff_at_expiry
    payoff_data = calculate_payoff_at_expiry(
        positions=portfolio.positions,
        price_range=price_range,
        include_theta=True
    )
    
    return {
        "current_price": current_price,
        "payoff_data": payoff_data,
        "portfolio_summary": {
            "total_delta": portfolio.total_delta,
            "total_theta": portfolio.total_theta,
            "total_vega": portfolio.total_vega
        }
    }


@app.websocket("/ws/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    """
    WebSocket для real-time обновлений портфеля
    """
    # Подключение клиента
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket)
    
    try:
        # Подписка на обновления
        while True:
            # Ожидание сообщений от клиента (опционально)
            data = await websocket.receive_text()
            # Обработка сообщений...
            pass
    except Exception:
        # Отключение клиента
        ws_manager.disconnect(websocket)
```

#### 1.4 Модифицировать `live_state_keeper.py`
```python
class LiveStateKeeper:
    def __init__(self, ...):
        # Существующий код...
        
        # Новые атрибуты для WebSocket
        self._ws_manager = None
    
    def set_websocket_manager(self, ws_manager):
        """Установка WebSocket менеджера"""
        self._ws_manager = ws_manager
    
    async def _recalculate_risk(self):
        """Перерасчет рисков с broadcast обновлений"""
        # Существующий расчет...
        portfolio = self._calculate_portfolio_risk()
        
        # Broadcast через WebSocket
        if self._ws_manager:
            await self._ws_manager.broadcast_portfolio_update(portfolio.dict())
        
        return portfolio
```

### Этап 2: Frontend разработка (Недели 2-3)

#### 2.1 Настройка проекта
```bash
# Создание React приложения
npx create-react-app frontend --template typescript
cd frontend

# Установка зависимостей
npm install @tanstack/react-table recharts date-fns
npm install @radix-ui/react-tabs @radix-ui/react-dropdown-menu
npm install zustand socket.io-client
npm install -D tailwindcss postcss autoprefixer
npm install -D @types/socket.io-client
```

#### 2.2 Компонент `OptionsBoard.tsx`
```typescript
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, ExpiryFilter, ExportButton } from './components';

interface OptionsBoardProps {
  baseCoin?: string;
}

const OptionsBoard: React.FC<OptionsBoardProps> = ({ baseCoin = 'BTC' }) => {
  const [selectedExpiry, setSelectedExpiry] = useState<string>('19DEC25');
  
  // Запрос данных доски опционов
  const { data, isLoading, error } = useQuery({
    queryKey: ['options-board', baseCoin, selectedExpiry],
    queryFn: () => fetchOptionsBoard(baseCoin, selectedExpiry),
    refetchInterval: 10000, // Обновление каждые 10 секунд
  });
  
  // Экспорт для ИИ-агента
  const handleExport = async () => {
    const exportData = {
      metadata: {
        timestamp: new Date().toISOString(),
        underlying_symbol: `${baseCoin}USDT`,
        underlying_price: data?.underlying_price,
        expiry: selectedExpiry,
        days_to_expiry: calculateDaysToExpiry(selectedExpiry),
        atm_strike: findATMStrike(data?.options),
        atm_iv: calculateATMIV(data?.options),
      },
      options: data?.options || [],
      portfolio_positions: [], // Будет из store
      ai_summary: generateAISummary(data),
    };
    
    // Скачивание JSON файла
    downloadJSON(exportData, `options_board_${selectedExpiry}.json`);
    
    // Генерация Markdown
    const markdown = generateMarkdownTable(exportData);
    downloadMarkdown(markdown, `options_board_${selectedExpiry}.md`);
  };
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <div className="options-board">
      <div className="board-header">
        <h2>Options Board - {baseCoin} {selectedExpiry}</h2>
        <div className="controls">
          <ExpiryFilter
            value={selectedExpiry}
            onChange={setSelectedExpiry}
            expiries={['19DEC25', '26DEC25', '2JAN26', 'All']}
          />
          <ExportButton onClick={handleExport} />
        </div>
      </div>
      
      <div className="board-table">
        <Table
          data={data?.options || []}
          columns={[
            { header: 'Strike', accessor: 'strike' },
            { header: 'Type', accessor: 'type' },
            { header: 'Bid/Ask', accessor: 'bid_ask' },
            { header: 'Mark', accessor: 'mark_price' },
            { header: 'IV', accessor: 'iv' },
            { header: 'Delta', accessor: 'delta' },
            { header: 'Gamma', accessor: 'gamma' },
            { header: 'Vega', accessor: 'vega' },
            { header: 'Theta', accessor: 'theta' },
            { header: 'OI', accessor: 'open_interest' },
          ]}
          onRowClick={(option) => showOptionDetails(option)}
        />
      </div>
      
      <div className="board-footer">
        <div className="stats">
          <span>Underlying: ${data?.underlying_price?.toLocaleString()}</span>
          <span>ATM IV: {calculateATMIV(data?.options)}%</span>
          <span>Total Options: {data?.options?.length || 0}</span>
        </div>
      </div>
    </div>
  );
};
```

#### 2.3 Компонент `PayoffChart.tsx`
```typescript
import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';
import { useWebSocket } from '../services/websocket';

interface PayoffChartProps {
  daysToExpiry?: number;
}

const PayoffChart: React.FC<PayoffChartProps> = ({ daysToExpiry }) => {
  const [payoffData, setPayoffData] = useState<any[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const { portfolio } = useWebSocket();
  
  // Загрузка данных графика
  useEffect(() => {
    const loadPayoffData = async () => {
      const response = await fetch(`/api/v1/payoff-chart?days_to_expiry=${daysToExpiry}`);
      const data = await response.json();
      
      setPayoffData(data.payoff_data.pnl.map((pnl: number, index: number) => ({
        price: data.payoff_data.price_range[index],
        pnl,
      })));
      
      setCurrentPrice(data.current_price);
    };
    
    loadPayoffData();
    const interval = setInterval(loadPayoffData, 30000); // Обновление каждые 30 секунд
    
    return () => clearInterval(interval);
  }, [daysToExpiry]);
  
  // Найти точки безубыточности
  const breakevenPoints = payoffData.filter(
    (point) => Math.abs(point.pnl) < currentPrice * 0.001
  );
  
  return (
    <div className="pay