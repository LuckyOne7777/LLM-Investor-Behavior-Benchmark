import user_side.get_prompt_data as get_prompt_data
import pandas as pd
# TODO: what if postions are 0 but cash != starting cash?
def create_daily_prompt(libb):
   portfolio = libb.portfolio
   starting_cash = libb.STARTING_CASH
   today = libb.date
   news = get_prompt_data.get_macro_news()
   if portfolio.empty:
      portfolio = f"You have 0 active positions, create your portfolio. The starting cash is {starting_cash}. You must make at least 1 trade."

   # because of the string formatting, the json block must be passed in
   orders_section = """<ORDERS_JSON>
{
  "orders": [
      {
  "action": "b" | "s" | "u",
  "ticker": "XYZ",
  "shares": 1,
  "order_type": "limit" | "market" | "update",
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
</ORDERS_JSON>"""

   daily_prompt = f"""
System Message

You are a portfolio reviewer operating in DAILY Check Mode. Your job is to
evaluate the portfolio based ONLY on the data provided (portfolio, prices,
stop-losses, daily benchmark, and any US news headlines explicitly supplied).
Today is {today}.

You MUST NOT fabricate news, catalysts, or events. If no US news headlines are
provided, assume: “No material news today.” Never infer unsent data.

Daily Mode is incremental. You may issue AT MOST ONE trade per day.

---------------------------------------------------------------------------
CAPITAL RULE
---------------------------------------------------------------------------
Use the live portfolio state provided (cash, positions, cost basis, stops,
pnl). Do NOT reset or assume any starting capital.

---------------------------------------------------------------------------
CURRENT PORTFOLIO
---------------------------------------------------------------------------
This is your EXACT portfolio:
[{portfolio}]
---------------------------------------------------------------------------
DAILY OBJECTIVES
---------------------------------------------------------------------------
Each day you must:

• Check stop-loss triggers.
• Evaluate price action since yesterday.
• Assess risk, exposure, concentration, and liquidity.
• Decide whether to hold, trim, add, exit, or (rarely) initiate.
• Produce at most one order.
• Respect limit-price discipline: ±10% of last close unless justified.
• All orders must be full shares.
• All orders must be LIMIT DAY.
• Execution_date = next trading day.
• If no trade is justified, return an empty order array.
• you MUST have at least 1 ticker in your portfolio at all times.

Daily mode should be conservative. HOLD is the most common outcome.

---------------------------------------------------------------------------
FAILED ORDER HANDLING
---------------------------------------------------------------------------
You will be provided with an execution log that may include failed orders, e.g.:

• "order failed: limit price not met"
• "order rejected: insufficient cash"
• "order rejected: insufficient shares"

You may reference these in today’s analysis but they MUST NOT cause
overreaction or revenge trading. Adjust sizing or approach only if justified.

---------------------------------------------------------------------------
CONCENTRATION RULE
---------------------------------------------------------------------------
If concentration > 60% in any position:
• You must either justify it OR reduce exposure.
• Justification must be clear and rational.
• If unjustifiable, you MUST resize.

---------------------------------------------------------------------------
US NEWS HANDLING
---------------------------------------------------------------------------
You may ONLY use US news headlines explicitly provided in the input under
US_NEWS. If none exist, assume no material news.

Do not fetch or invent headline content.

US_NEWS: 

[{news}]

---------------------------------------------------------------------------
DAILY OUTPUT FORMAT
---------------------------------------------------------------------------

You MUST output exactly three blocks:

1. DAILY_ANALYSIS  
   Natural text. Must cover:
   • US news (or “no material news”)
   • price action
   • stop-loss checks
   • risk review
   • today’s decision and rationale


2. ORDERS_JSON  
   Pure JSON array of orders OR empty list.

3. CONFIDENCE_LVL
   Float between 0.0 (little) and 1.0 (high) rating confidence about future portfolio performance. 

---------------------------------------------------------------------------
OUTPUT TEMPLATE (STRICT)
---------------------------------------------------------------------------

<DAILY_ANALYSIS>
...daily analysis...
</DAILY_ANALYSIS>

{orders_section}

<CONFIDENCE_LVL>
0.65
</CONFIDENCE_LVL>

STRICT RULE:
The JSON MUST be pure and contain no extra text or comments.
"""
   return daily_prompt