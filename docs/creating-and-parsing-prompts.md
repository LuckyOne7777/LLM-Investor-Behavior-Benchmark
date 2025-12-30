# Creating and Parsing Prompts

LIBB does not prescribe how prompts are written.
The only **hard requirement** is that the model outputs a correctly formatted
`ORDERS_JSON` block. The tag does *not* have to use the convention `ORDERS_JSON`,
as long as you parse accordingly.

Everything else, tone, reasoning style, rules, is user-controlled.

---

## Required Output: ORDERS_JSON

All trade instructions must be returned inside a single JSON block.

The block must contain an `orders` array. Each element in the array represents
one order.

No additional text is allowed inside the JSON block.

---

## Order Format

Each order must conform to the following schema:

```python
class Order(TypedDict):
    action: Literal["b", "s", "u"]     # "b" = buy, "s" = sell, "u" = update stop-loss
    ticker: str
    shares: int
    order_type: Literal["limit", "market", "update"]
    limit_price: Optional[float]
    time_in_force: Optional[str]
    date: str                               # YYYY-MM-DD
    stop_loss: Optional[float]
    rationale: str                          # short reasoning message (currently not enforced)
    confidence: float                       # 0–1 (currently not enforced)
```
---

### Field Notes

- action  
  - "b" → buy  
  - "s" → sell  
  - "u" → update stop-loss only  

- order_type  
  - "limit" or "market" for buy/sell  
  - "update" for stop-loss updates  

- limit_price  
  - required when order_type == "limit"  
  - must be null otherwise  

- shares  
  - must always be an integer  
  - use 0 when action == "u" if shares are not relevant  

- date  
  - must be formatted as YYYY-MM-DD  
  - only orders with the same date as the processing will be processed  

- rationale and confidence  
  - currently recorded but not enforced  
  - included for future extensibility and auditing  

---

## Example: Valid ORDERS_JSON Output

<ORDERS_JSON>
{
  "orders": [
    {
      "action": "b",
      "ticker": "MSFT",
      "shares": 40,
      "order_type": "limit",
      "limit_price": 250.00,
      "time_in_force": "DAY",
      "date": "2025-12-16",
      "stop_loss": 225.00,
      "rationale": "Initiate position in a leading AI and cloud technology company.",
      "confidence": 0.75
    }
  ]
}
</ORDERS_JSON>

---

## Validation Behavior

- Missing or invalid required fields will cause the trade to fail and be logged
  accordingly.
- Extra fields are ignored.
- Missing data for optional fields is expected and safely ignored.

LIBB favors explicit failure over silent correction.

---

## Parsing JSON Blocks

LIBB provides a helper function for extracting tagged JSON blocks from raw model
output.

Import path:
libb.other.parse.parse_json

---

### Parameters

- text_block: str  
  The full text returned by the model.

- tag: str  
  The name of the JSON tag to extract (e.g. "ORDERS_JSON").

---

## Example Usage

text = """
Some commentary above.

<EXAMPLE>
{
  "orders": [
    { "ticker": "ABC" }
  ]
}
</EXAMPLE>

Some commentary below.
"""

tag = "EXAMPLE"

result = parse_json(text, tag)

---

### Output

{
  "orders": [
    { "ticker": "ABC" }
  ]
}

The parsed result is now a standard Python object and may be passed directly to
libb.save_orders(...).

---

## Design Notes

- LIBB does not attempt to repair malformed JSON
- Prompt writers are responsible for enforcing structure
- Parsing is explicit and deterministic
