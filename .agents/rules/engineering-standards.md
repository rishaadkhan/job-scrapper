# Engineering, Security, and Code Quality Standards

This rule governs all code generation, refactoring, and bug fixes in this repository.

## Guiding Tenets
1. **Pragmatic Simplicity:** Apply design patterns (SOLID, DRY) only when they simplify the system. Avoid premature abstraction, unnecessary layers, or speculative features (KISS & YAGNI).
2. **OWASP & Secure Coding:**
   - Always enforce explicit network timeouts on `requests` / HTTP clients.
   - Validate and restrict URL schemes (`http://`, `https://`) and prevent SSRF to local/private addresses.
   - Avoid catastrophic backtracking in regex (ReDoS).
   - Zero hardcoded credentials; use environment variables.
   - Prevent path traversal when saving output files.
   - Never use `eval()`, `exec()`, or untrusted `pickle`.
3. **Resilience & Fault Isolation:**
   - Isolate per-company and per-job scraping failures so batch runs proceed uninterrupted.
   - No bare `except:` or silent `except Exception: pass`. Always log meaningful context.
   - Use exponential backoff for transient network issues.
   - Perform atomic file writes for state persistence (`.tmp` + `os.replace`).
4. **Clean Code & Python Typing:**
   - Type annotate all public function arguments and return types.
   - Separate network I/O from pure data filtering/transformation logic for testability.
