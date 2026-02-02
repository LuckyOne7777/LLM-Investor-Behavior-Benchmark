from typing import TypedDict, Literal, Optional
from enum import Enum
from dataclasses import dataclass
import pandas as pd
from copy import deepcopy
import os

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

class TradeStatus(Enum):
    FILLED = "FILLED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class MarketConfig:
    alpha_vantage_key: str | None = None
    finnhub_key: str | None = None

    @classmethod
    def from_env(cls):
        return cls(
            alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY"),
            finnhub_key=os.getenv("FINNHUB_API_KEY"),
        )
    
@dataclass(slots=True)
class Log:
    date: str
    weekday: str
    started_at: str
    finished_at: str
    nyse_open_on_date: bool
    created_after_close: bool
    eligible_for_execution: bool
    processing_status: str
    orders_processed: int
    orders_failed: int
    orders_skipped: int
    portfolio_value: float
    error: str | Exception | None = None