# Creating Order Format

## Order Format

---
Orders must be placed inside a 'orders' = [ ... ]" block.

```python
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
```
Orders must be grouped together in a pure JSON block. 

For example, here's a correct output:
```python
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
      "rationale": "Initiate position in a leading AI and cloud tech stock to capture growth and diversify portfolio exposure.",
      "confidence": 0.75
    }
    ...
  ]
}
</ORDERS_JSON>
```
*Note: Null or missing required order data will result in a failed trade and logged accordingly, however missing data for unnecessary columns is expected and ignored.* 

---

## Parsing 

To parse said (or any) JSON block, feel free to use the dedicated function `parse_json()` in `libb.other.parse`. 

#### Params

text_block: str, full block of text from a model

tag: str, specific JSON tag

example useage: 

```python
from libb.other.parse import parse_json

text: """
      abc..
    <EXAMPLE>
    {
    xyz...
    }
    </EXAMPLE>
    abc...
    """
tag = "EXAMPLE"

result = parse_json(text, tag)
print(result)
```

Output:

```python
    {
    xyz...
    }
```
Result is now completely normal to save to orders.



