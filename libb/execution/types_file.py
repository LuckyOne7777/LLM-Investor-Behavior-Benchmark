from typing import TypedDict, Literal, Optional

class Order(TypedDict):
    action: Literal["b", "s", "u"]     # "u" = update stop-loss
    ticker: str
    shares: int
    order_type: Literal["limit", "market", "update"]
    limit_price: Optional[float]
    time_in_force: Optional[str]
    date: str                               # YYYY-MM-DD
    stop_loss: Optional[float]
    rationale: str
    confidence: float                       # 0-1

class MarketDataObject(TypedDict):
     Low: float
     High: float
     Close: float
     Open: float
     Volume: int
     Ticker: str