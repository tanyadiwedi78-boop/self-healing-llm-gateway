from app.services import cost_service
from app.core.config import get_settings


def fake_prices():
    # Prices: 1 USD per 1M input tokens, 2 USD per 1M output tokens
    return {"test/model": {"input_per_million": 1.0, "output_per_million": 2.0}}


def test_cost_is_input_plus_output(monkeypatch):
    monkeypatch.setattr(cost_service, "load_prices", fake_prices)
    # 1,000,000 input + 500,000 output = 1.0 + 1.0 = 2.0
    assert cost_service.calculate_cost("test/model", 1_000_000, 500_000) == 2.0


def test_unknown_model_costs_zero(monkeypatch):
    monkeypatch.setattr(cost_service, "load_prices", fake_prices)
    assert cost_service.calculate_cost("no/such-model", 100, 100) == 0.0


def test_zero_tokens_cost_zero(monkeypatch):
    monkeypatch.setattr(cost_service, "load_prices", fake_prices)
    assert cost_service.calculate_cost("test/model", 0, 0) == 0.0

def test_every_price_entry_has_both_prices():
    cost_service.reload_prices()
    prices = cost_service.load_prices()
    assert prices, "pricing.json is missing, empty, or unreadable"
    for model, price in prices.items():
        for key in ("input_per_million", "output_per_million"):
            assert key in price, f"{model} is missing {key}"
            assert price[key] >= 0, f"{model} has a negative {key}"


def test_every_configured_model_has_a_price():
    cost_service.reload_prices()
    settings = get_settings()
    prices = cost_service.load_prices()
    assert prices, "pricing.json is missing, empty, or unreadable"
    for name in settings.provider_names:
        model = getattr(settings, f"{name}_model")
        assert model in prices, f"No price for {model} in pricing.json"


def test_real_file_math():
    cost_service.reload_prices()
    prices = cost_service.load_prices()
    assert prices, "pricing.json is missing, empty, or unreadable"
    model = next(iter(prices))
    expected = prices[model]["input_per_million"]
    assert cost_service.calculate_cost(model, 1_000_000, 0) == expected