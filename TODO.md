# Security Fixes TODO

Tasks are worked one at a time via `/security-fix`. After each fix is marked `[done]`, clear context and run `/security-fix` again.

Status: `[pending]` → `[in-progress]` → `[done]`

---

## Task 1 [done] — XSS: unsanitized course titles in innerHTML

**File:** `frontend/script.js:215-220`

**Vulnerability:** Course title strings are interpolated directly into `innerHTML`, allowing a malicious course title to inject arbitrary HTML/JS.

**Fix:** Replace the innerHTML-based rendering with DOM methods. Find where course titles are inserted via innerHTML (look for template literals or string concatenation assigned to `.innerHTML` involving title or course name). Replace with:
```js
const el = document.createElement('div');
el.textContent = courseTitle;  // safe — no HTML interpretation
parent.appendChild(el);
```
Apply the same pattern wherever course titles (or any server-returned string) are written to `.innerHTML`.

---

## Task 2 [done] — XSS: raw HTML concatenation for source URLs/labels

**File:** `frontend/script.js:169-172`

**Vulnerability:** Source URLs and labels from the API response are concatenated into HTML strings and assigned to `.innerHTML`, enabling XSS if a source URL or label contains `<script>` or event handlers.

**Fix:** Build source link elements using DOM methods instead of string concatenation:
```js
const a = document.createElement('a');
a.href = source.url;          // browsers sanitize href assignment
a.textContent = source.label; // safe text
a.target = '_blank';
a.rel = 'noopener noreferrer';
container.appendChild(a);
```
Remove any HTML string building (backtick template literals or `+` concatenation) that feeds into `.innerHTML` for sources.

---

## Task 3 [done] — CORS misconfiguration

**File:** `backend/app.py:20,23-30`

**Vulnerability:** CORS is configured with `allow_origins=["*"]` (wildcard), which combined with `allow_credentials=True` is both a security risk and a spec violation (browsers reject credentialed requests to wildcard origins). There is also a no-op `TrustedHostMiddleware` that doesn't actually restrict anything useful here.

**Fix:**
1. Change `allow_origins` from `["*"]` to `["http://localhost:8000", "http://127.0.0.1:8000"]`.
2. Remove `allow_credentials=True` (or keep `False`) since this app uses no cookies/auth headers.
3. Remove the `TrustedHostMiddleware` lines — they add no value for a localhost dev server and create confusion.

---

## Task 4 [done] — Unchecked `response.content[0]` access

**File:** `backend/ai_generator.py:88,131,141`

**Vulnerability:** Code does `response.content[0]` without checking if `content` is non-empty. If the API returns an empty content list (e.g., due to a filtered response or API change), this raises an `IndexError` with no useful context.

**Fix:** Before each `response.content[0]` access, add a guard:
```python
if not response.content:
    raise ValueError("Claude API returned empty content — possible safety filter or API error")
```
Apply this guard at all three line locations (88, 131, 141).

---

## Task 5 [done] — Unsafe `json.loads()` calls

**File:** `backend/vector_store.py:250,288,306`

**Vulnerability:** `json.loads()` is called on data retrieved from ChromaDB without exception handling. If a stored metadata field is malformed or truncated, this raises an unhandled `json.JSONDecodeError` that propagates as a 500.

**Fix:** Wrap each `json.loads()` call in a try/except:
```python
try:
    value = json.loads(raw)
except json.JSONDecodeError:
    value = []  # or appropriate fallback (empty list, empty dict, etc.)
```
Use a sensible fallback for each location (e.g., empty list for arrays, empty dict for objects).

---

## Task 6 [done] — `str(e)` leaking internals in 500 responses

**File:** `backend/app.py:76,89`

**Vulnerability:** Exception handlers return `str(e)` directly to the client in the HTTP response body. This can expose internal file paths, library versions, database schema details, or other implementation information useful to attackers.

**Fix:**
1. Replace `str(e)` in the response with a generic message: `"An internal error occurred. Please try again."`.
2. Add server-side logging before the generic response: `import logging; logger = logging.getLogger(__name__)` at the top of the file, then `logger.exception("Unhandled error in /api/query")` (or similar) inside the except block so the real error is still visible in server logs.

---

## Task 7 [done] — Unbounded session memory

**File:** `backend/session_manager.py` + `backend/config.py`

**Vulnerability:** Sessions are stored in a plain dict with no eviction policy. A client (or attacker) can create unlimited sessions, eventually exhausting server memory.

**Fix:**
1. In `config.py`, add two new fields to the `Config` dataclass:
   - `max_sessions: int = 1000` — maximum number of concurrent sessions
   - `session_ttl_seconds: int = 3600` — session idle timeout (1 hour)
2. In `session_manager.py`:
   - Switch the session store from `dict` to `collections.OrderedDict`.
   - Track last-access timestamps in a parallel dict.
   - On each `get_history` / `add_message` call: first prune sessions older than `session_ttl_seconds`, then if session count exceeds `max_sessions`, evict the oldest (first) entry from the OrderedDict.

---

## Task 8 [done] — Inconsistent chunk context prefix

**File:** `backend/document_processor.py:192-245`

**Vulnerability:** Not all text chunks are prefixed with course/lesson context. Chunks without context produce weaker vector search matches and can return irrelevant results, degrading RAG quality.

**Fix:** Ensure every chunk stored in the vector DB is prefixed uniformly:
```python
chunk_text = f"Course {course_title} Lesson {lesson_number} content: {chunk}"
```
Audit the chunk-building loop in lines 192-245 and make sure this prefix is applied to every chunk before it is added to the ChromaDB collection, with no exceptions.

---

## Task 9 [done] — Fragile `../docs` relative path

**File:** `backend/app.py:101`

**Vulnerability:** The docs directory is resolved with a relative path like `"../docs"`. This breaks if the server is started from any directory other than `backend/`, which is easy to do accidentally.

**Fix:** Replace the relative path with an absolute path anchored to the source file's location:
```python
import os
DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
DOCS_DIR = os.path.normpath(DOCS_DIR)
```
This works regardless of the current working directory when the server is launched.
