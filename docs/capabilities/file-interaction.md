# File Interaction

LIBB manages a structured on-disk file system for each run.  
This includes portfolio state, metrics, research outputs, and logs.

File interaction is explicit, destructive when misused, and intentionally
low-level. Users are expected to understand the consequences of invoking these
methods.

---

## ensure_file_system

```python
libb.ensure_file_system() -> None
```

Create and initialize all required directories and files for a run.

This method ensures that the expected file system layout exists and that all
required files are present with appropriate default contents.

It is **automatically called during construction** of the `LIBBmodel` object and
should not normally be invoked manually.

---

### Behavior

The following directories are created if missing:

- root run directory
- portfolio directory
- metrics directory
- research directory
- daily report folder
- deep research folder

The following files are created if missing:

#### Portfolio Files
- portfolio history (CSV)
- pending trades (JSON)
- current portfolio (CSV)
- trade log (CSV)
- position history (CSV)

#### Metrics Files
- behavior metrics (JSON)
- performance metrics (JSON)
- sentiment metrics (JSON)

If a file already exists, it is **not overwritten**.

---

### Intended Usage

This function exists to guarantee a valid processing environment before any
portfolio logic or metric computation occurs.

Users should rely on the constructor to handle this automatically.

---

### Notes

- This function does not validate file contents
- Corrupt or malformed files will not be repaired
- Manual edits to generated files may cause undefined behavior
- This method is safe to call repeatedly but unnecessary outside initialization

---

## reset_run

```python
libb.reset_run(cli_check: bool = True) -> None

```

Delete **all files and folders** within the run root directory.

This method is destructive and irreversible.

If `ensure_file_system()` is not called afterward, all subsequent processing
will fail silently or raise errors.

---

### Parameters

- `cli_check` (`bool`, optional)  
  Require interactive confirmation before deleting files.  
  Defaults to `True`.

- `auto_ensure` (`bool`, optional): 
  Automatically calls `ensure_file_system()` after deletion.
  Defaults to False.

---

### Safety Checks

- Requires explicit user confirmation when `cli_check=True`
- Refuses to delete system roots such as `/` or `C:/`
- Deletes both files and directories within the run root

---

### Intended Usage

`reset_run()` is intended for:

- wiping a run entirely
- restarting experiments from a clean slate
- development and debugging workflows

It should **never** be used in automated production pipelines without careful
guarding.

---

### Warnings

- This operation permanently deletes all run data
- There is no undo
- Removing files mid-workflow may corrupt state
- Calling this inside a workflow loop is almost always a mistake

If you are unsure whether you need this function, you probably do not.
