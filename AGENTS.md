# Repository AI Engineering & Quality Standards

This document establishes the mandatory engineering standards, architectural principles, security guidelines, and coding practices for all AI assistants and developers modifying this codebase.

---

## 1. Core Directive: Pragmatic Software Engineering

Always apply engineering principles with **pragmatism**. The goal is clean, maintainable, scalable, and resilient software—**not** unnecessary complexity.

*   **KISS (Keep It Simple, Stupid):** Prefer the simplest solution that correctly and robustly solves the problem. Simple code is easier to read, test, debug, and maintain.
*   **YAGNI (You Aren't Gonna Need It):** Implement only what is required now. Do not add speculative features, preemptive abstractions, or generic layers for hypothetical future use cases.
*   **Pragmatic DRY (Don't Repeat Yourself):** Eliminate harmful logic duplication. However, remember: *duplicate code is far cheaper than the wrong abstraction*. Do not force disparate logic into a single generic function if it creates coupling.
*   **Pragmatic SOLID:**
    *   **Single Responsibility:** Each class/function should have one well-defined reason to change.
    *   **Open/Closed:** Make code extensible (e.g., portal scrapers) without modifying core orchestration, but avoid excessive boilerplate.
    *   **Liskov Substitution & Interface Segregation:** Keep interfaces small and contracts predictable.
    *   **Dependency Inversion:** Decouple high-level orchestration from low-level I/O (e.g., inject HTTP sessions or state managers) to enable unit testing.
*   **Anti-Over-Engineering Rule:** If applying a pattern (e.g., factory of factories, multi-tier inheritance, complex metaclasses) increases cognitive load without tangible benefit, **do not use it**.

---

## 2. Security Standards & OWASP Guidelines

Security is paramount in automated pipelines, web crawlers, and API integrations.

### 2.1. SSRF & Network Security
*   **URL Validation:** Always validate URLs before fetching. Restrict protocols strictly to `http://` and `https://`.
*   **Internal Network Protection:** Block requests targeting private/internal network ranges (`127.0.0.1`, `localhost`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254` cloud metadata endpoints).
*   **Timeouts:** **Every** network call must specify an explicit timeout (`timeout=(connect_timeout, read_timeout)` or `timeout=REQUEST_TIMEOUT`). Never allow indefinite hanging requests.
*   **TLS/SSL:** Always verify SSL certificates (`verify=True`). Never disable SSL verification in production code.

### 2.2. Injection & ReDoS Defense
*   **Regular Expression Safety (ReDoS):** Avoid nested quantifiers (e.g., `(a+)+`, `([a-zA-Z0-9]+)*`) that cause catastrophic backtracking on malformed inputs. Use bounded repetitions and test regexes on adversarial inputs.
*   **Safe Parsing & Deserialization:**
    *   Never use `eval()`, `exec()`, or untrusted `pickle.loads()`.
    *   Use `json.loads()` for JSON and `yaml.safe_load()` for YAML.
    *   Sanitize and validate parsed schema before accessing nested keys (`dict.get()` with defaults or typed models).
*   **Command Injection:** Never pass raw, unsanitized user or scraped input into shell execution functions (`subprocess.Popen(..., shell=True)` is forbidden).

### 2.3. Path Traversal & File Safety
*   **Safe File Paths:** Prevent directory traversal (`../`). When writing outputs (e.g., `output/*.xlsx`, state files), validate and resolve absolute paths, ensuring they remain inside the intended target directory.
*   **Filename Sanitization:** Strip invalid filesystem characters, path separators, and null bytes (`\0`) from company names or user inputs when generating file names.

### 2.4. Secrets & Sensitive Data
*   **Zero Hardcoded Secrets:** Never hardcode API keys, passwords, bearer tokens, or sensitive webhook URLs in code.
*   **Environment Variables:** Load credentials securely from environment variables or `.env` using standard utilities (`os.getenv()`).
*   **Log Sanitization:** Ensure tokens, passwords, authorization headers, and PII are redacted from logs and exception messages.

---

## 3. Error Handling, Resilience & State Integrity

The pipeline runs as scheduled background jobs; it must be self-healing, defensive, and fault-tolerant.

### 3.1. Defensive Exception Handling
*   **No Bare Except:** Never use bare `except:` or catch `BaseException`.
*   **No Silent Failures:** Never write `except Exception: pass` without structured logging. When catching general exceptions, log the context (module, target company, URL, and stack trace at `DEBUG` or `WARNING` level).
*   **Specific Exception Hierarchy:** Catch specific errors first (e.g., `requests.exceptions.Timeout`, `requests.exceptions.HTTPError`, `json.JSONDecodeError`, `KeyError`) before falling back to generic handlers.

### 3.2. Fault Isolation & Graceful Degradation
*   **Batch Isolation:** A failure while scraping or parsing one company or job must **never** crash the entire execution run. Isolate errors at the item/company level and continue processing remaining items.
*   **Retries with Backoff:** Implement retries with exponential backoff and jitter for transient network failures (e.g., HTTP 429, 500, 502, 503, 504, connection timeouts). Do not retry permanent client errors (400, 401, 403, 404) unless specific token refresh logic exists.

### 3.3. Atomic State Persistence
*   **Atomic Writes:** When persisting state (e.g., `scraper_state.json`) or export files, write to a temporary file (`.tmp`) first and use atomic rename (`os.replace` or `shutil.move`) to prevent state corruption if interrupted or killed mid-write.
*   **Backup / Recovery:** Preserve previous state validly if serialization fails.

---

## 4. Scalability & Performance

*   **HTTP Session Reuse:** Reuse `requests.Session()` (or `httpx.Client`) across requests to take advantage of TCP connection pooling, keep-alive, and DNS caching.
*   **Streaming & Memory Management:** For large files, downloads, or datasets, use streaming (`response.iter_content()`) rather than reading entire payloads into memory.
*   **Polite Scraping & Rate Limiting:** Enforce configurable rate limiting (`RATE_LIMIT_DELAY`) between external requests to respect portal infrastructure and avoid IP bans.
*   **Concurrency Readiness:** Design components with thread-safety and concurrency in mind (avoid shared mutable global state).

---

## 5. Code Quality, Maintainability & Python Standards

*   **Type Hinting:** Use explicit Python type annotations (`typing.Optional`, `typing.List`, `typing.Dict`, `typing.Tuple`, `typing.Callable`, `dataclasses`, or `TypedDict`) on all public function signatures, parameters, and return types.
*   **Docstrings & Comments:**
    *   Provide clear docstrings explaining the **purpose**, **parameters**, **return values**, and **exceptions raised**.
    *   Write comments that explain *why* non-obvious logic exists (e.g., workarounds for portal idiosyncrasies), not just *what* the code does.
*   **Meaningful Naming:** Use descriptive snake_case for functions and variables, PascalCase for classes, and UPPER_CASE for configuration constants.
*   **Separation of Concerns:**
    *   `scraper.py`: Network fetching and portal-specific DOM/API parsing.
    *   `filters.py`: Pure business rules, criteria evaluation, and data normalization.
    *   `state_manager.py`: Persistence, deduplication, and state lifecycle.
    *   `exporter.py`: Output generation and formatting.
    *   `config.py`: Centralized configuration and constants.
*   **Testability:** Keep business logic (filtering, normalization, parsing) pure and decoupled from network calls so it can be verified with fast, deterministic unit tests.

---

## 6. Pre-Generation AI Checklist

Before outputting or committing any code changes, verify:
1. [ ] **Simplicity Check:** Is this the simplest, most readable way to achieve the goal without over-engineering?
2. [ ] **Security Check:** Are all external inputs sanitized, URLs validated, timeouts set, and secrets kept out of code?
3. [ ] **Error Handling:** Are exceptions specific, logged with context, and isolated so batch jobs do not crash?
4. [ ] **State Safety:** Are file writes atomic and state files protected from corruption?
5. [ ] **Typing & Tests:** Are type annotations complete and the code easily testable?
