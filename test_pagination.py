import asyncio
import logging
import os
from bybit_options.services.bybit_connector import BybitConnector
from option_board_utils import parse_option_symbol # Добавляем импорт для парсинга символов

# --- Настройка логирования для получения информации о пагинации ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# Установим уровень для коннектора, чтобы видеть его INFO-логи
logging.getLogger('bybit_connector').setLevel(logging.INFO)

async def run_test():
    # Используем заглушки для ключей, так как get_instruments_info использует _public_request
    api_key = os.environ.get("BYBIT_API_KEY", "DUMMY_KEY")
    api_secret = os.environ.get("BYBIT_API_SECRET", "DUMMY_SECRET")
    
    logger.info("Starting pagination test for BTC options...")
    
    async with BybitConnector(api_key, api_secret) as connector:
        try:
            instruments = await connector.get_instruments_info(
                category="option",
                base_coin="BTC"
            )
            
            # Проверка результатов: используем parse_option_symbol, чтобы извлечь expiry из symbol
            unique_expiries = set()
            for inst in instruments:
                symbol = inst.get('symbol')
                if symbol:
                    try:
                        parsed = parse_option_symbol(symbol)
                        unique_expiries.add(parsed['expiry'])
                    except ValueError:
                        # Игнорируем символы, которые не удалось распарсить
                        continue
            
            print("===================================================")
            print(f"Total instruments fetched: {len(instruments)}")
            print(f"Number of unique expiries (series): {len(unique_expiries)}")
            print("===================================================")

        except Exception as e:
            logger.error(f"An error occurred during the test: {e}", exc_info=True)

if __name__ == "__main__":
    # Убедимся, что asyncio.run доступен (Python 3.7+)
    asyncio.run(run_test())
