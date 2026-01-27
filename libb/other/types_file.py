from typing import TypedDict, Literal, Optional
from dataclasses import dataclass
import pandas as pd
from copy import deepcopy

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

@dataclass (frozen=True)
class ModelSnapshot:
    cash: float

    portfolio_history: pd.DataFrame
    portfolio: pd.DataFrame
    trade_log: pd.DataFrame
    position_history: pd.DataFrame

    pending_trades: dict[str, list[dict]]
    performance: list[dict]
    behavior: list[dict]
    sentiment: list[dict]

    def __post_init__(self):
        object.__setattr__(self, "portfolio_history", self.portfolio_history.copy(deep=True))
        object.__setattr__(self, "portfolio", self.portfolio.copy(deep=True))
        object.__setattr__(self, "trade_log", self.trade_log.copy(deep=True))
        object.__setattr__(self, "position_history", self.position_history.copy(deep=True))

        object.__setattr__(self, "pending_trades", deepcopy(self.pending_trades))
        object.__setattr__(self, "performance", deepcopy(self.performance))
        object.__setattr__(self, "behavior", deepcopy(self.behavior))
        object.__setattr__(self, "sentiment", deepcopy(self.sentiment))
