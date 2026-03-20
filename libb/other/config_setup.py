_CONFIG_TYPES = {
    "risk_free_rate": (float, int),
    "trading_days_per_year": int,
    "starting_cash": (float, int),
    "slippage_pct_per_trade": (float, int),
}

_DEFAULT_CONFIG = {
    "risk_free_rate": 0.045,
    "trading_days_per_year": 252,
    "starting_cash": 10_000,
    "slippage_pct_per_trade": 0.0,
}

def _is_valid_type(key: str, value) -> bool:
    return isinstance(value, _CONFIG_TYPES[key])

def verifiy_config(config: dict | None) -> dict:
    if config is None:
        return _DEFAULT_CONFIG.copy()

    verified = {}
    for key, default_value in _DEFAULT_CONFIG.items():
        custom_value = config.get(key)
        if custom_value is not None and _is_valid_type(key, custom_value):
            verified[key] = custom_value
        else:
            verified[key] = default_value

    return verified

_active_config = {}

def get_config():
    return _active_config

def set_config(config):
    global _active_config
    _active_config = config