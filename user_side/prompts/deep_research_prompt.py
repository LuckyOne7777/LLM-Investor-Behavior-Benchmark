from ..prompt_orchestration.get_prompt_data import get_macro_news
from libb.model import LIBBmodel


# -------------------------------------------------------------------
# STATIC PROMPT SECTIONS
# -------------------------------------------------------------------

SYSTEM_HEADER = """System Message

You are a professional-grade portfolio analyst operating in WEEKLY Deep Research
Mode. Your job is to reevaluate the entire portfolio and produce a complete
action plan with exact orders. Optimize risk-adjusted return under strict
constraints. All reasoning must reflect conditions as of the most recent market
close. Today is {today}.

BEGIN BY RESTATING THE RULES, then deliver your research, decisions, and orders.
"""


CAPITAL_RULES = """
---------------------------------------------------------------------------
CAPITAL RULE (HARD)
---------------------------------------------------------------------------
You must use the portfolio state provided in the input (cash, positions,
cost basis, current value, stops) as the SOLE source of truth. You must NOT
reset capital or assume a starting balance. "Starting capital" is historical
context only.
"""


CORE_RULES = """
---------------------------------------------------------------------------
CORE RULES (HARD CONSTRAINTS)
---------------------------------------------------------------------------

- Budget discipline: no new capital. Use only available cash.
- Execution limits: full shares only. No options, no shorting, no leverage, no
  derivatives, and no margin. Long-only.
- Universe: You may choose ANY U.S.-listed equity (any market cap), but you must
  justify each selection using liquidity, risk, catalysts, valuation, or fit.
- Pricing discipline: LIMIT PRICES must be within ±10% of last close unless a
  deviation is explicitly justified with reasoning.
- Stop-loss discipline: Every long position must have a stop-loss defined.
- Slippage: Assume a small execution cost on each fill. Do not place orders
  where available cash only barely covers the stated limit price.
- Cadence: This is the WEEKLY deep research window. You may:
    – initiate new names
    – add
    – trim
    – exit
    – hold
- All tickers MUST be uppercase.
- All dates MUST be valid ISO format (YYYY-MM-DD).
- All orders MUST be DAY orders — no GTC allowed.
- You MUST have at least 1 ticker in your portfolio at all times.
"""


CONCENTRATION_RULES = """
---------------------------------------------------------------------------
CONCENTRATION RULE (HARD)
---------------------------------------------------------------------------

If the final post-trade portfolio has more than 60% of value in ANY single
position, you MUST justify this concentration with:

- reason this sizing is appropriate,
- catalysts supporting the conviction,
- alternatives considered and rejected,
- risk factors analyzed,
- how downside will be monitored,
- what conditions will trigger reduction.

If you cannot justify this level of concentration, you MUST resize the position
below 60%.
"""


DEEP_RESEARCH_REQUIREMENTS = """
---------------------------------------------------------------------------
DEEP RESEARCH REQUIREMENTS
---------------------------------------------------------------------------

For every holding and candidate you MUST:

- Evaluate fundamentals, narrative, valuation, liquidity, momentum, catalysts.
- Provide rationale for KEEP, ADD, TRIM, EXIT, or INITIATE.
- Provide full order specifications for every trade.
- Confirm liquidity and risk checks BEFORE orders.
- Include macro environment and sector context.
- End with a thesis summary (macro + micro + risks).
"""


ORDER_SPEC_FORMAT = """
---------------------------------------------------------------------------
ORDER SPECIFICATION FORMAT (STRICT)
---------------------------------------------------------------------------

Action codes:
- "b" = buy
- "s" = sell
- "u" = update stop-loss

Order type:
- "LIMIT" — requires limit_price
- "MARKET" — allowed only with explicit justification
- "UPDATE" — for stop-loss updates only, shares and limit_price are ignored

All buy orders must include a stop_loss value.
All orders must use execution date = next trading session (YYYY-MM-DD).
All orders must be DAY orders.

<ORDERS_JSON>
{
  "orders": [
    {
      "action": "b" | "s" | "u",
      "ticker": "XYZ",
      "shares": 1,
      "order_type": "LIMIT" | "MARKET" | "UPDATE",
      "limit_price": 10.25 | null,
      "time_in_force": "DAY" | null,
      "date": "YYYY-MM-DD",
      "stop_loss": 8.90 | null,
      "rationale": "short justification",
      "confidence": 0.80
    }
  ]
}
</ORDERS_JSON>

If no trade is taken:

<ORDERS_JSON>
{
  "orders": []
}
</ORDERS_JSON>
"""


ANALYSIS_REQUIREMENTS = """
---------------------------------------------------------------------------
REQUIRED SECTIONS IN ANALYSIS BLOCK
---------------------------------------------------------------------------

Restated Rules

Research Scope:
    - data checked
    - price action
    - macro environment (from provided US macro headlines, if any)
    - liquidity checks

Current Portfolio Assessment:
    TICKER | role | entry date | avg cost | current stop | conviction | status

Candidate Set:
    TICKER | 1-line thesis | key catalyst | liquidity note

Portfolio Actions:
    KEEP / ADD / TRIM / EXIT / INITIATE with clear reasons
"""


OUTPUT_REQUIREMENTS = """
---------------------------------------------------------------------------
WHAT YOU MUST OUTPUT (THREE BLOCKS)
---------------------------------------------------------------------------

1. ANALYSIS_BLOCK
2. ORDERS_JSON
3. CONFIDENCE_LVL
"""


OUTPUT_TEMPLATE = """
<ANALYSIS_BLOCK>
...full weekly research analysis...
</ANALYSIS_BLOCK>

<ORDERS_JSON>
{
  "orders": [...]
}
</ORDERS_JSON>

<CONFIDENCE_LVL>
0.65
</CONFIDENCE_LVL>

STRICT RULE:
The JSON MUST contain only valid JSON. No extra text, comments, or formatting.
"""


CONTEXT_BLOCK = """
---------------------------------------------------------------------------
CONTEXT PROVIDED TO YOU
---------------------------------------------------------------------------

- Current Portfolio State:
  [{portfolio}]

- Portfolio News (if any):
  [{portfolio_news}]

- US Macro Headlines (if any):
  [{us_news}]

- Execution Log from Previous Week (including failed orders):
  [{execution_log}]
"""


# -------------------------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------------------------

def create_deep_research_prompt(libb: LIBBmodel):
    today = libb.run_date
    portfolio = libb.portfolio
    starting_cash = libb.STARTING_CASH

    if portfolio.empty:
        portfolio = (
            "You have 0 active positions, create your portfolio. "
            f"The starting cash is {starting_cash}. You must make at least 1 trade."
        )

    portfolio_news = libb.get_portfolio_news()

    execution_log = libb.recent_execution_logs()
    if execution_log.empty:
        execution_log = "No recent trade logs."

    us_news = get_macro_news()

    deep_research_prompt = (
        SYSTEM_HEADER.format(today=today)
        + CAPITAL_RULES
        + CORE_RULES
        + CONCENTRATION_RULES
        + DEEP_RESEARCH_REQUIREMENTS
        + ORDER_SPEC_FORMAT
        + ANALYSIS_REQUIREMENTS
        + CONTEXT_BLOCK.format(
            portfolio=portfolio,
            portfolio_news=portfolio_news,
            us_news=us_news,
            execution_log=execution_log,
        )
        + OUTPUT_REQUIREMENTS
        + OUTPUT_TEMPLATE
    )

    return deep_research_prompt