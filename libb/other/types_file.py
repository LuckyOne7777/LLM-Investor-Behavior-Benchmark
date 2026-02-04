from typing import TypedDict, Literal, Optional
from enum import Enum
from dataclasses import dataclass
import pandas as pd
from copy import deepcopy
import os
from pathlib import Path

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

@dataclass(frozen=True)
class DiskLayout:
    # root
    root: Path

    # directories
    portfolio_dir: Path
    metrics_dir: Path
    research_dir: Path
    logging_dir: Path

    deep_research_dir: Path
    daily_reports_dir: Path

    # portfolio files
    portfolio_path: Path
    portfolio_history_path: Path
    trade_log_path: Path
    position_history_path: Path
    pending_trades_path: Path
    cash_path: Path

    # metrics files
    performance_path: Path
    behavior_path: Path
    sentiment_path: Path

    @classmethod
    def from_root(cls, root: Path) -> "DiskLayout":
        portfolio_dir = root / "portfolio"
        metrics_dir = root / "metrics"
        research_dir = root / "research"
        logging_dir = root / "logging"

        deep_research_dir = research_dir / "deep_research"
        daily_reports_dir = research_dir / "daily_reports"

        return cls(
            root=root,

            portfolio_dir=portfolio_dir,
            metrics_dir=metrics_dir,
            research_dir=research_dir,
            logging_dir=logging_dir,

            deep_research_dir=deep_research_dir,
            daily_reports_dir=daily_reports_dir,

            portfolio_path=portfolio_dir / "portfolio.csv",
            portfolio_history_path=portfolio_dir / "portfolio_history.csv",
            trade_log_path=portfolio_dir / "trade_log.csv",
            position_history_path=portfolio_dir / "position_history.csv",
            pending_trades_path=portfolio_dir / "pending_trades.json",
            cash_path=portfolio_dir / "cash.json",

            performance_path=metrics_dir / "performance.json",
            behavior_path=metrics_dir / "behavior.json",
            sentiment_path=metrics_dir / "sentiment.json",
        )
