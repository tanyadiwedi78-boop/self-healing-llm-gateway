import json
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)

ONE_MILLION = 1_000_000

PROJECT_ROOT = Path(__file__).resolve().parents[2]

prices = {}            
loaded = False         
warned_models = set()   


def get_pricing_path():

    path = Path(get_settings().pricing_file)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def read_price_file():
    
    path = get_pricing_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        logger.warning(f"pricing_file_unusable path={path} reason={error}")
        return {}


    return {name: price for name, price in data.items() if not name.startswith("_")}


def load_prices():
    
    global prices, loaded
    if not loaded:
        prices = read_price_file()
        if prices:
            loaded = True
    return prices


def reload_prices():
    global loaded
    loaded = False


def calculate_cost(model, prompt_tokens, completion_tokens):
    
    price = load_prices().get(model)

    if price is None:
        
        if model not in warned_models:
            warned_models.add(model)
            logger.warning(f"pricing_missing model={model}")
        return 0.0

    input_cost = prompt_tokens * price.get("input_per_million", 0) / ONE_MILLION
    output_cost = completion_tokens * price.get("output_per_million", 0) / ONE_MILLION
    return round(input_cost + output_cost, 8)