
# 🧠 Bybit Options Options: Deep Research

**Status:** Verified (Specs as of Feb 2025)
**Context:** Bybit Unified Trading Account (UTA) Environment.

## 1. Specification Basics (Техническая часть)
Bybit Options — это **European-style Cash-Settled Options**.

| Параметр | Значение | Комментарий |
| :--- | :--- | :--- |
| **Тип** | **European** | Исполнение *только* в дату экспирации. Нельзя исполнить досрочно (но можно продать в стакан). |
| **Расчет (Settlement)** | **Cash (Наличные)** | Физической поставки BTC/ETH нет. Вы получаете разницу между Strike и Settlement Price в стейблкоинах (USDT/USDC). |
| **Валюта (Coin)** | **USDT / USDC** | Основная ликвидность переходит в USDT. USDC опционы (новые) прекращены с Feb 2025 (Legacy only). |
| **Settlement Price** | **30-min TWAP** | Средняя цена индекса (Index Price) за последние 30 минут до экспирации (08:00 UTC). Это защита от манипуляций в последнюю секунду. |
| **Trading Hours** | **24/7** | Криптовалютные опционы торгуются круглосуточно. |

### Серии (Expirations)
Bybit предлагает стандартную линейку:
*   **Daily:** Экспирация каждый день (для 0DTE/1DTE гэмблинга/хеджа).
*   **Weekly:** Пятничные экспирации (основная ликвидность).
*   **Monthly:** Конец месяца (Last Friday).
*   **Quarterly:** Квартальные (MAR, JUN, SEP, DEC).

---

## 2. Маржирование (Мathematics of Margin)
Опционы на Bybit торгуются *только* внутри **Unified Trading Account (UTA)**.

### Режимы Маржи
1.  **Isolated Margin:**
    *   Риск изолирован.
    *   *Long Option:* Платите премию целиком (Fully Paid). Маржа не нужна.
    *   *Short Option:* Маржа замораживается под конкретную позу.
2.  **Cross Margin:**
    *   Весь баланс аккаунта обеспечивает все позиции.
    *   P&L от фьючерсов может покрывать убыток по опционам.
3.  **Portfolio Margin (PM) — (Режим Профи)**
    *   **Суть:** Риск считается по всему портфелю в целом (Net Risk).
    *   **Пример:** Если у вас Short Call + Long Future (Covered Call), обычный маржин потребует залог за Short Call. **PM** увидит, что риск закрыт, и маржа будет близка к нулю.
    *   **Требование:** > 1000 USDC Equity.
    *   **Liquidation:** Происходит, когда MMR (Maintenance Margin Rate) аккаунта достигает 100%.

### Нюансы Ликвидации
*   **Long Options:** Никогда не ликвидируются (вы не можете потерять больше, чем заплатили).
*   **Short Options:** Ликвидируются при MMR = 100%. Опцион откупается системой по рынку (Mark Price).

### Маржируемые vs Premium-Style Опционы
Существует два типа расчета опционов:

| Характеристика | **Premium-Style** (Классические) | **Margined / Futures-Style** |
| :--- | :--- | :--- |
| **Оплата при покупке** | Полная премия сразу (Fully Paid) | Только маржа (Initial Margin) |
| **Расчет P&L** | При закрытии/экспирации | Ежедневно (Mark-to-Market) |
| **Маржа для Long** | Не нужна (макс. убыток = премия) | Нужна (вариационная маржа) |
| **Пример** | CME Equity Options, SPX | Eurex, Deribit |

**На Bybit:**
Опционы — **гибридная модель**, ближе к Premium-Style:
*   **Long Options:** Не требуют маржи. Вы платите премию — и всё.
*   **Short Options:** Требуют Maintenance Margin (~10-15% от underlying).
*   **P&L:** Отражается real-time (Mark-to-Market), но не списывается до закрытия (Unrealized).
*   **Важно:** На Bybit *купленный* опцион **не может быть ликвидирован** (в отличие от Deribit Futures-Style).

---

## 3. Особенности Данных (Data Specs)
Как читать тикеры и данные API:

*   **Symbol Format:** `BTC-27MAR26-80000-P-USDT`
    *   `BTC`: Underlying Index.
    *   `27MAR26`: Expiry (DDMMMYY).
    *   `80000`: Strike Price.
    *   `P`: Put (или `C` for Call).
    *   `USDT`: Settlement Currency.

*   **Mark Price:** Рассчитывается на основе Black-Scholes с использованием:
    *   Index Price (Spot).
    *   Interest Rate (r).
    *   Trading Implied Volatility (из стакана).
    *   *Важно:* Ликвидации идут по Mark Price, а не по Last Price.

---

## 5. Роллирование на Маржируемых Опционах (CRITICAL)

> [!IMPORTANT]
> На Bybit **нет Debit/Credit при роллировании** в классическом понимании американского рынка.

### Что происходит при ролле:
1.  **Закрытие старой позиции:** Unrealized P&L становится Realized. Деньги не "уходят" — они были уже отражены в балансе.
2.  **Открытие новой позиции:** Резервируется новая маржа (может измениться вверх/вниз).

### Реальные затраты:
| Затрата | Описание |
| :--- | :--- |
| **Комиссия** | ~0.02% от notional (минимум) |
| **Спред (Bid/Ask)** | Проскальзывание при исполнении |
| **Изменение маржи** | Если новый страйк ближе — маржа растет |

### Правило для Trading Expert:
**НЕ считать "стоимость ролла" как Debit/Credit.**
Сравнивать только:
1.  **Theta decay rate** — сколько собираем в день
2.  **Gamma risk** — насколько opасна позиция
3.  **Margin change** — сколько заморозится/освободится

---
**Location:** `docs/knowledge/bybit-options-mechanics.md`
