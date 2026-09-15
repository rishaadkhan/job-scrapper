---
name: engineering-standards
description: >-
  Enforces pragmatic software engineering, design principles (SOLID/KISS/YAGNI), OWASP security guidelines, robust error handling, fault isolation, and maintainable code standards across the repository. Use whenever generating, modifying, reviewing, or refactoring code.
---

# Code Engineering & Quality Standards Skill

This skill guides AI models and developers through writing clean, pragmatic, secure, and resilient code for the repository.

---

## 1. When Modifying or Generating Code

Follow this 4-phase workflow on every task:

```
[ 1. Assess & Plan ] ──► [ 2. Implement Pragmatically ] ──► [ 3. Apply Security & Resilience ] ──► [ 4. Validate & Type-Check ]
```

### Phase 1: Assess & Plan
1. **Identify the Core Problem:** What is the simplest change that satisfies the requirement?
2. **Check YAGNI & KISS:** Are you introducing classes, interfaces, or layers that aren't strictly necessary? If yes, simplify.
3. **Respect Module Boundaries:**
   - **`scraper.py`**: Web scraping, HTTP requests, HTML/JSON parsing.
   - **`filters.py`**: Pure filtering, keyword matching, experience extraction, location checks.
   - **`state_manager.py`**: State persistence, tracking seen jobs, atomic writes.
   - **`exporter.py`**: Output generation (Excel/CSV formatting).
   - **`config.py`**: Constants, keywords, thresholds.

### Phase 2: Implement Pragmatically
1. **Prefer Simple Functions over Heavy OOP:** Unless state encapsulation or polymorphism is genuinely needed, favor straightforward pure functions.
2. **Pragmatic DRY:** Do not create convoluted abstractions just to share 2 lines of code across unrelated modules.
3. **Explicit Type Hints:** Annotate all parameters and return types using Python `typing` (`Optional`, `List`, `Dict`, `Tuple`, `Any`, `Callable`).
4. **Self-Documenting Code:** Choose clear, descriptive names for variables and functions. Add docstrings detailing parameters, return values, and failure modes.

### Phase 3: Apply Security & Resilience (OWASP & Defensiveness)
1. **Network & HTTP Calls:**
   - Always set `timeout=REQUEST_TIMEOUT` (e.g., 15s) on every request.
   - Always validate that URLs use `http://` or `https://`.
   - Never disable TLS verification (`verify=False`).
   - Reuse `requests.Session()` to enable connection pooling and header consistency.
2. **Injection & ReDoS Defense:**
   - Avoid nested regex quantifiers.
   - Never use `eval()`, `exec()`, or untrusted `pickle`.
   - Use `json.loads` / `yaml.safe_load`.
3. **Fault Isolation:**
   - Isolate errors at the company/job level using try-except blocks so one broken portal does not crash the pipeline.
   - Catch specific exceptions (`requests.exceptions.RequestException`, `json.JSONDecodeError`, `KeyError`) instead of silent bare `except:`.
   - Never swallow exceptions with `pass` without at least logging a warning with context.
4. **Atomic File Persistence:**
   - When updating state files (`scraper_state.json`), write to a temporary file (`.tmp`) first and atomically replace the target using `os.replace()`.

### Phase 4: Validate & Verify
1. **Syntax & Static Check:** Ensure code is syntactically valid and lint-free.
2. **Test Decoupled Logic:** Run existing tests or add unit tests for any new filtering/parsing logic in `tests/`.

---

## 2. Reference Implementation Patterns

### Pattern A: Safe Network Request with Retries & Timeout
```python
import time
import requests
from typing import Optional, Dict, Any

def safe_fetch(
    session: requests.Session, 
    url: str, 
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 15,
    max_retries: int = 3
) -> Optional[requests.Response]:
    """Fetch URL with timeout, retry backoff, and scheme validation."""
    if not (url.startswith("http://") or url.startswith("https://")):
        return None

    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response
            elif response.status_code in (429, 500, 502, 503, 504):
                time.sleep(attempt * 1.5)  # Backoff
            else:
                break  # Permanent client error (404, 403, etc.)
        except requests.exceptions.RequestException:
            if attempt == max_retries:
                break
            time.sleep(attempt * 1.5)
    return None
```

### Pattern B: Atomic File Write
```python
import json
import os
import tempfile
from typing import Any, Dict

def atomic_save_json(filepath: str, data: Dict[str, Any]) -> None:
    """Safely write JSON data to file using atomic rename to prevent corruption."""
    dir_name = os.path.dirname(filepath) or "."
    os.makedirs(dir_name, exist_ok=True)
    
    # Write to temp file in the same filesystem directory
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as temp_file:
        json.dump(data, temp_file, indent=2)
        temp_name = temp_file.name
    
    # Atomic rename replaces target safely
    os.replace(temp_name, filepath)
```

---

## 3. Verification & AI Self-Check Checklist

Before presenting or applying any code changes, verify:
* [ ] Is this solution the simplest approach (KISS) without unnecessary indirection?
* [ ] Are network timeouts explicitly specified?
* [ ] Are errors isolated so batch scraping continues on isolated failures?
* [ ] Are state files written atomically?
* [ ] Are all types annotated and imports clean?
