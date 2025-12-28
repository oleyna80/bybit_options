# ПРОМТ ДЛЯ РАЗРАБОТЧИКА: Multi-Agent Analyzer for Risk Analysis

## 📌 ЦЕЛЬ

Переписать файл `Multi-Agent Discussion.py` с React/JSX на **чистый Python** класс `MultiAgentAnalyzer`, который будет интегрирован в архитектуру проекта и работать с реальными данными анализа рисков опционов Bybit.

**Критическое требование**: Многоагентная дискуссия - это **ВАЖНЫЙ компонент проекта**, должна быть полностью функциональна и готова к использованию.

---

## 🎯 ТРЕБОВАНИЯ

### 1. АРХИТЕКТУРА И СТРУКТУРА

#### Основной класс
```python
class MultiAgentAnalyzer:
    """
    Multi-agent discussion engine for portfolio risk analysis
    
    Coordinates discussion between AI agents with different expertise:
    - Technical Risk Analyst: Analyzes Greeks, margin risks
    - Options Strategist: Evaluates hedging opportunities
    - Market Conditions Expert: Considers volatility, market trends
    - Risk Officer: Flags critical alerts and compliance issues
    
    Design principles:
    - Async-first (compatible with project's async architecture)
    - Integrates with PortfolioRiskModel data
    - Pure Python (no React/JSX)
    - Extensible agent system
    """
```

#### Интеграция в проект
- **Где размещать**: `multi_agent_analyzer.py` (переименовать из текущего файла)
- **Импорты**: `AnalysisOrchestrator`, `PortfolioRiskModel`, `data_models`
- **API**: Вызывается из `main.py` после выполнения анализа
- **Результаты**: Сохраняет отчет в `reports/multi_agent_analysis_*.md`

---

### 2. ОСНОВНАЯ ФУНКЦИОНАЛЬНОСТЬ

#### 2.1 Агенты (Agents)
```python
# Определить 4-5 агентов с разными ролями (на русском или английском):

@dataclass
class Agent:
    id: str                    # "risk_analyst"
    name: str                  # "Аналитик Рисков" / "Risk Analyst"
    role: str                  # Описание роли и фокуса анализа
    system_prompt: str         # Системный промт для LLM
    model: str = "claude-3-5-sonnet-20241022"  # или из конфига
    max_tokens: int = 500
    temperature: float = 0.7

# Агенты должны быть:
# 1. Risk Analyst - фокусируется на греках, хеджировании, маржине
# 2. Strategist - предлагает торговые решения
# 3. Market Expert - анализирует волатильность, тренды рынка
# 4. Compliance Officer - проверяет риски и ограничения
# (5.) Optional: Performance Reviewer - анализирует результаты
```

#### 2.2 Процесс дискуссии

```python
async def run_discussion(
    self,
    portfolio: PortfolioRiskModel,
    topic: str = None,
    rounds: int = 2
) -> DiscussionResult:
    """
    Запустить многоагентную дискуссию по анализу портфолио
    
    Процесс:
    1. Подготовить контекст из PortfolioRiskModel
    2. Цикл N раундов:
        - Каждый агент высказывает мнение (с учетом предыдущих мнений)
        - Собрать все высказывания
    3. Модератор составляет итоговый отчет
    4. Вернуть DiscussionResult с полной историей
    """
```

#### 2.3 Формирование контекста (Context Building)

Каждому агенту передается контекст:
```
📊 КОНТЕКСТ ПОРТФОЛИО:
- Equity: $100,000
- Margin Used: 45% / Warning at 60%
- Delta: +5.2 BTC
- Gamma: +0.0023 BTC/$ 
- Vega: +$2,500 (USD volatility exposure)
- Theta: -$150/day (daily decay)

⚠️ РИСКИ И АЛЕРТЫ:
- [HIGH] Margin below warning threshold
- [MEDIUM] High vega exposure
- [LOW] Gamma rent opportunity detected

🎯 ПОЗИЦИИ:
[Таблица позиций с греками]

📈 РЫНОЧНЫЕ ДАННЫЕ:
- BTC Price: $98,500
- IV Percentile: 65%
- Volatility: 35%
```

---

### 3. РАБОТА С API

#### 3.1 Anthropic API Integration
```python
async def _call_agent(
    self,
    agent: Agent,
    prompt: str,
    discussion_history: List[Message] = None
) -> str:
    """
    Обратиться к LLM для получения ответа агента
    
    Требования:
    - Получить API ключ из environment (ANTHROPIC_API_KEY)
    - Использовать корректный Authorization header
    - Включить discussion history в контекст (если > 0 раундов)
    - Обработать ошибки: timeout, rate limit, API errors
    - Retry logic для временных ошибок
    - Логировать все запросы (для debug)
    """
```

#### 3.2 Обработка ошибок
- Graceful degradation если API недоступен
- Retry с exponential backoff
- Timeout protection (не ждать > 60 сек на один запрос)
- Логирование всех ошибок в logger

#### 3.3 Конфигурация
Добавить в `config.py`:
```python
class AnthropicConfig(BaseSettings):
    api_key: str = Field(..., description="Anthropic API Key")
    model: str = Field(default="claude-3-5-sonnet-20241022")
    timeout: int = Field(default=60)
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=1.0)
```

---

### 4. СТРУКТУРА ДАННЫХ

#### 4.1 Модели Pydantic
```python
# В data_models.py добавить:

class Message(BaseModel):
    """Сообщение в дискуссии"""
    agent_id: str
    agent_name: str
    timestamp: datetime
    round: int
    content: str
    token_count: int  # для отслеживания usage

class DiscussionRound(BaseModel):
    """Раунд дискуссии"""
    round_number: int
    messages: List[Message]
    duration_seconds: float

class DiscussionResult(BaseModel):
    """Результат полной дискуссии"""
    portfolio_snapshot: PortfolioRiskModel
    topic: str
    rounds: List[DiscussionRound]
    moderator_summary: str
    key_insights: List[str]
    recommendations: List[str]
    discussion_start: datetime
    discussion_end: datetime
    total_tokens_used: int
    
    class Config:
        json_schema_extra = {
            "description": "Complete multi-agent discussion output"
        }
```

---

### 5. ИНТЕГРАЦИЯ С ПРОЕКТОМ

#### 5.1 Вызов из main.py
```python
# After portfolio analysis completes:

from multi_agent_analyzer import MultiAgentAnalyzer

analyzer = MultiAgentAnalyzer(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

discussion_result = await analyzer.run_discussion(
    portfolio=portfolio,
    rounds=2
)

# Сохранить отчет
report_path = analyzer.save_report(discussion_result)
logger.info(f"Multi-agent analysis saved to: {report_path}")
```

#### 5.2 Сохранение отчетов
```python
def save_report(
    self,
    result: DiscussionResult,
    output_dir: str = "reports"
) -> str:
    """
    Сохранить отчет дискуссии в Markdown
    
    Файл: reports/multi_agent_analysis_2025-12-16_14-30-45.md
    
    Формат:
    # Multi-Agent Risk Analysis
    
    **Discussion Date**: 2025-12-16 14:30:45
    **Rounds**: 2
    **Total Tokens**: 2,450
    
    ## Portfolio Snapshot
    [Краткая сводка портфолио]
    
    ## Discussion Rounds
    
    ### Round 1
    - Agent: Risk Analyst
      - [Message 1]
    - Agent: Strategist
      - [Message 2]
    
    ### Round 2
    [...]
    
    ## Moderator Summary
    [Итоговые выводы]
    
    ## Key Insights
    - [Insight 1]
    - [Insight 2]
    
    ## Recommendations
    - [Rec 1]
    - [Rec 2]
    """
```

---

### 6. ДОПОЛНИТЕЛЬНЫЕ ВОЗМОЖНОСТИ

#### 6.1 Streaming (Optional для демо)
```python
async def run_discussion_stream(self, ...):
    """
    Вариант с streaming output для интерактивного просмотра
    Может быть полезно для будущего фронтенда
    """
```

#### 6.2 Persistent Storage (Optional)
```python
async def save_discussion_json(self, result: DiscussionResult):
    """
    Сохранить полную дискуссию в JSON для последующего анализа
    """
```

#### 6.3 Agent Customization (Optional)
```python
def add_custom_agent(
    self,
    id: str,
    name: str,
    role: str,
    system_prompt: str
):
    """Добавить кастомного агента"""
```

---

## 7. ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Example 1: Базовый анализ
```python
# Простой запуск после получения портфолио
analyzer = MultiAgentAnalyzer()
result = await analyzer.run_discussion(portfolio)
print(result.moderator_summary)
```

### Example 2: С кастомной темой
```python
# Обсудить специфичный вопрос
result = await analyzer.run_discussion(
    portfolio=portfolio,
    topic="Как хеджировать высокую гамму при повышении BTC выше $100k?",
    rounds=3
)
```

### Example 3: Получить рекомендации
```python
result = await analyzer.run_discussion(portfolio)
for rec in result.recommendations:
    print(f"✓ {rec}")
```

---

## 8. ТРЕБОВАНИЯ К КОДУ

### Style & Quality
- ✅ Type hints для всех функций
- ✅ Docstrings на английском с примерами
- ✅ Async/await паттерны
- ✅ Логирование на key points
- ✅ Error handling с specific exceptions
- ✅ Unit tests готовность (чистые функции)

### Testing
```python
# Примеры для тестирования:
- Mock Anthropic API responses
- Test context building
- Test report generation
- Test error handling
```

### Performance
- ⚠️ Параллельные запросы к агентам в одном раунде (asyncio.gather)
- ⏱️ Таймауты на каждый запрос
- 💾 Минимизировать duplicate data передачу

---

## 9. ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ

1. ✅ **multi_agent_analyzer.py** (переименовать текущий)
   - Полная переработка на Python
   - Класс MultiAgentAnalyzer
   - Все вспомогательные функции

2. 📝 **data_models.py** 
   - Добавить Message, DiscussionRound, DiscussionResult

3. ⚙️ **config.py**
   - Добавить AnthropicConfig

4. 🔧 **main.py** (опционально)
   - Добавить вызов analyzer.run_discussion()

5. 📋 **requirements.txt** (если нужны новые пакеты)
   - Проверить что есть: aiohttp, pydantic

---

## 10. ЭДЖ-КЕЙСЫ И ОБРАБОТКА

### Edge Cases
- ❌ Если нет позиций в портфолио → использовать пустой контекст
- ❌ Если API key отсутствует → выкинуть исключение или вернуть stub
- ❌ Если API timeout → retry или fallback к кешированному ответу
- ❌ Если agent crashes → log и перейти к следующему

### Fallback Strategies
```python
# Если Anthropic API недоступен, например:
class FallbackAnalyzer:
    """Возвращает базовый анализ без LLM"""
```

---

## 11. ПРИОРИТЕТЫ РЕАЛИЗАЦИИ

**Phase 1 (MUST HAVE)** - Core functionality
1. Класс MultiAgentAnalyzer с 4 базовыми агентами
2. run_discussion() с 2 раундами
3. Правильная работа с Anthropic API
4. Сохранение в Markdown отчет
5. Интеграция с main.py

**Phase 2 (SHOULD HAVE)** - Polish & Robustness
1. Параллельные запросы агентов (asyncio.gather)
2. Retry logic с exponential backoff
3. Streaming output
4. Unit тесты

**Phase 3 (NICE TO HAVE)** - Advanced features
1. Кастомные агенты
2. Persistent JSON storage
3. Фронтенд интеграция (websocket streaming)
4. Database logging

---

## 12. ОЦЕНКА УСПЕХА

✅ Код успешно реализован если:

- [ ] Файл переписан на Python (NO React/JSX)
- [ ] Класс MultiAgentAnalyzer работает асинхронно
- [ ] 4 агента с разными ролями успешно дискутируют
- [ ] Результаты сохраняются в Markdown отчет
- [ ] Интегрировано с PortfolioRiskModel
- [ ] Работает с реальным Anthropic API (с правильным Auth header)
- [ ] Обработаны ошибки и edge cases
- [ ] Код протестирован и готов к production
- [ ] Документация актуальна (docstrings)
- [ ] Можно вызвать из main.py и получить результат

---

## 13. СПРАВОЧНЫЕ МАТЕРИАЛЫ

### Текущая архитектура проекта
- `main.py` - CLI entry point
- `analysis_orchestrator.py` - главный оркестратор
- `risk_engine.py` - чистые вычисления (zero I/O)
- `bybit_connector.py` - API к Bybit
- `data_models.py` - Pydantic models
- `market_data_service.py` - сервис для маркет-данных

### Примеры интеграции
- Используй `PortfolioRiskModel` как источник данных
- Формируй контекст как в `display_manager.py`
- Следуй async паттернам как в `analysis_orchestrator.py`

### API References
- Anthropic API: https://docs.anthropic.com/
- Python AsyncIO: https://docs.python.org/3/library/asyncio.html
- Pydantic: https://docs.pydantic.dev/

---

## 📞 ВОПРОСЫ ДЛЯ УТОЧНЕНИЯ

Перед началом уточни:

1. **API Key Management**: Где будет храниться ANTHROPIC_API_KEY?
   - В `.env` файле (как BYBIT_API_KEY)?
   - В environment variables?
   - В Vault/Secrets Manager?

2. **Agent Language**: На каком языке писать промты агентов?
   - Русский (для русскоязычного вывода)?
   - Английский (для consistency)?

3. **Model Choice**: Какую модель Claude использовать?
   - claude-3-5-sonnet-20241022 (default)?
   - Другую?

4. **Интеграция с UI**: Нужен ли streaming output для будущего фронтенда?

5. **Storage**: Где хранить исторические анализы?
   - Только в Markdown файлах?
   - Или еще и в базе данных?

---

**Статус**: ✅ Готово для разработки  
**Приоритет**: HIGH (Critical Feature)  
**Сложность**: MEDIUM-HIGH  
**Примерное время**: 4-6 часов для Phase 1
