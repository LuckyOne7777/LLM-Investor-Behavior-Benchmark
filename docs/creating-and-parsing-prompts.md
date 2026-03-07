# Creating and Parsing Prompts

LIBB does not prescribe how prompts are written.
The only **hard requirement** is that the model outputs a correctly formatted
`ORDERS_JSON` block. The tag does not have to use the convention `ORDERS_JSON`,
as long as you parse accordingly.

Everything else — tone, reasoning style, rules — is user-controlled.

---

## Required Output

All trade instructions must be returned inside a single JSON block.

The block must contain an `orders` array. Each element in the array represents
one order.

No additional text is allowed inside the JSON block.

---

## Order Format

Each order must conform to the following schema:

```python
class Order(TypedDict):
    action: Literal["b", "s", "u"]          # "b" = buy, "s" = sell, "u" = update stop-loss
    ticker: str                             # uppercase
    shares: int
    order_type: Literal["LIMIT", "MARKET", "UPDATE"]
    limit_price: Optional[float]
    time_in_force: Optional[str]            # "DAY"
    date: str                               # YYYY-MM-DD
    stop_loss: Optional[float]
    rationale: str                          # short reasoning message (currently not enforced)
    confidence: float                       # 0–1 (currently not enforced)
```

---

### Field Notes

- `action`
  - `"b"` → buy
  - `"s"` → sell
  - `"u"` → update stop-loss only

- `order_type`
  - `"LIMIT"` or `"MARKET"` for buy/sell orders
  - `"UPDATE"` for stop-loss updates

- `limit_price`
  - Required when `order_type == "LIMIT"`
  - Should be `null` otherwise

- `shares`
  - Must always be an integer
  - For update orders (`action == "u"`), shares is not read by the system —
    any integer value is acceptable, including 0

- `stop_loss`
  - Required for update orders — this is the value being changed
  - For buy orders, defaults to 0 if omitted

- `date`
  - Must be formatted as `YYYY-MM-DD`
  - Only orders matching the current processing date will be executed
  - Orders with a past date will be rejected and logged

- `time_in_force`
  - Recorded in the trade log but not currently enforced by the system
  - GTC behavior is not implemented — all orders effectively behave as DAY orders

- `rationale` / `confidence`
  - Currently recorded in the trade log but not enforced
  - Included for auditing and future extensibility

---

## Example: Valid ORDERS_JSON Output

### Buy Order

```
<ORDERS_JSON>
{
  "orders": [
    {
      "action": "b",
      "ticker": "MSFT",
      "shares": 40,
      "order_type": "LIMIT",
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
```

### Sell Order

```
<ORDERS_JSON>
{
  "orders": [
    {
      "action": "s",
      "ticker": "MSFT",
      "shares": 40,
      "order_type": "LIMIT",
      "limit_price": 270.00,
      "time_in_force": "DAY",
      "date": "2025-12-17",
      "stop_loss": null,
      "rationale": "Take profit at target price.",
      "confidence": 0.80
    }
  ]
}
</ORDERS_JSON>
```

### Stop-Loss Update

```
<ORDERS_JSON>
{
  "orders": [
    {
      "action": "u",
      "ticker": "MSFT",
      "shares": 0,
      "order_type": "UPDATE",
      "limit_price": null,
      "time_in_force": null,
      "date": "2025-12-17",
      "stop_loss": 240.00,
      "rationale": "Trail stop-loss up after recent move.",
      "confidence": 0.70
    }
  ]
}
</ORDERS_JSON>
```

### No Trade

```
<ORDERS_JSON>
{
  "orders": []
}
</ORDERS_JSON>
```

---

## Validation Behavior

- Missing or invalid required fields will cause the trade to fail and be logged
  accordingly.
- Extra fields are ignored.
- Missing data for optional fields is expected and safely handled.

LIBB favors explicit failure over silent correction.

---

## Parsing JSON Blocks

LIBB provides a helper function for extracting tagged JSON blocks from raw model
output.

Import path: `libb.other.parse.parse_json`

---

### Parameters

- `text_block` (`str`)
  The full text returned by the model.

- `tag` (`str`)
  The name of the JSON tag to extract (e.g. `"ORDERS_JSON"`).

---

### Example Usage

```python
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
```

### Output

```python
{
  "orders": [
    { "ticker": "ABC" }
  ]
}
```

The parsed result is a standard Python dict and can be passed directly to
`libb.save_orders(...)`.

---

## Design Notes

- LIBB does not attempt to repair malformed JSON
- Prompt writers are responsible for enforcing structure
- Parsing is explicit and deterministic
