# File Interaction

LIBB manages a structured on-disk file system for each run.  
This includes portfolio state, metrics, research outputs, logs, and cash state.

File interaction is explicit, destructive when misused, and intentionally low-level. Users are expected to understand the consequences of invoking these methods.

---

## ensure_file_system

```python
libb.ensure_file_system() -> None
```

Ensure all required directories and files exist for a run.

Missing directories and files are created with default contents.  
Existing files are never overwritten.

This method is **automatically called during construction** of the `LIBBmodel` object and should not normally be invoked manually.

---

### Behavior

The following directories are created if missing:

- Root run directory  
- Portfolio directory  
- Metrics directory  
- Research directory  
- Daily report directory  
- Deep research directory  
- Logging directory  

The following files are created if missing:

#### Portfolio Files

- Portfolio history (CSV)  
  ```
  date,equity,cash,positions_value,daily_return_pct,overall_return_pct
  ```

- Pending trades (JSON)  
  ```json
  {"orders": []}
  ```

- Cash state (JSON)  
  Initialized as:
  ```json
  {"cash": STARTING_CASH}
  ```

- Current portfolio (CSV)  
  ```
  ticker,shares,buy_price,cost_basis,stop_loss,market_price,market_value,unrealized_pnl
  ```

- Trade log (CSV)  
  ```
  date,ticker,action,shares,price,cost_basis,PnL,rationale,confidence,status,reason
  ```

- Position history (CSV)  
  ```
  date,ticker,shares,avg_cost,stop_loss,market_price,market_value,unrealized_pnl
  ```

#### Metrics Files

All metrics files are initialized as empty JSON arrays:

- Behavior metrics (JSON) → `[]`
- Performance metrics (JSON) → `[]`
- Sentiment metrics (JSON) → `[]`

---

### Important Notes

- This function does **not** validate file contents.
- Corrupt or malformed files are not repaired.
- Manual edits to generated files may cause undefined behavior.
- This method is safe to call repeatedly but unnecessary outside initialization.
- This method only affects the filesystem — it does not reset in-memory runtime state.

---

### Intended Usage

This function exists to guarantee a valid processing environment before any portfolio logic or metric computation occurs.

Users should rely on the constructor to handle this automatically.

---

## reset_run

```python
libb.reset_run(cli_check: bool = True, auto_ensure: bool = False) -> None
```

Delete **all files and folders inside the run root directory**.

This method is destructive and irreversible.

By default, it only deletes on-disk artifacts.  
The current `LIBBmodel` instance remains alive, but its runtime state is marked invalid until reinitialized.

---

### Parameters

- `cli_check` (`bool`, optional)  
  Require interactive confirmation before deleting files.  
  Defaults to `True`.

- `auto_ensure` (`bool`, optional)  
  If `True`, performs a full logical reset after deletion:
  - Recreates required filesystem structure
  - Rehydrates disk-backed state into memory
  - Resets runtime-only state (counters, timestamps, snapshots)
  - Establishes a new startup disk snapshot
  - Marks the instance as valid again

  Defaults to `False`.

---

### Behavior

When called:

1. The instance is immediately marked invalid.
2. If `cli_check=True`, interactive confirmation is required.
3. The method refuses to delete filesystem root paths (e.g., `/`, `C:\`, drive roots, UNC share roots).
4. All files and directories within the run root are deleted.
5. The root directory itself is never deleted — only its contents.

If `auto_ensure=False` (default):

- Filesystem state is deleted.
- Runtime state is NOT reset.
- The instance remains invalid until explicitly reinitialized.

If `auto_ensure=True`:

- Filesystem state is deleted.
- `ensure_file_system()` is called.
- Disk-backed state is rehydrated.
- Runtime-only state is reset.
- A new startup disk snapshot is created.
- The instance becomes equivalent to a freshly constructed `LIBBmodel`
  pointing to the same root path (without restarting the Python process).

---

### Safety Guarantees

- Requires explicit confirmation when `cli_check=True`
- Refuses to delete filesystem root paths
- Deletes both files and directories within the run root
- Never deletes the root directory itself — only its contents

---

### Intended Usage

`reset_run()` is intended for:

- Wiping a run entirely
- Restarting experiments from a clean slate
- Development and debugging workflows

Use of `auto_ensure=True` is appropriate when a full logical reset is required without reconstructing the object.

---

### Warnings

- This operation permanently deletes all run data.
- There is no undo.
- Removing files mid-workflow may corrupt state.
- Calling this inside a workflow loop is almost always a mistake.
- Using `cli_check=False` removes interactive protection and should only be done in tightly controlled development contexts.

If you are unsure whether you need this function, you probably do not.
