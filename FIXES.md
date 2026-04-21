FIXES

1. API (`api/main.py`)

# Hardcoded Redis Host
File: api/main.py, line 6
Problem: Redis connection hardcoded to `localhost:6379`. Inside Docker, localhost resolves to the API container itself, not the Redis service, causing all Redis operations to fail with ConnectionRefusedError.
Fix: Changed to read from environment variables: `redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=int(os.getenv("REDIS_PORT", 6379)), password=os.getenv("REDIS_PASSWORD", None))`

# No Redis Connection Validation on Startup
File: api/main.py, line 6
Problem: Redis client is created at module load time with no connection test. If Redis is not yet ready, the app crashes with an unhelpful traceback and no recovery path.
*Fix: Added a FastAPI startup event that calls `r.ping()` and raises `RuntimeError` with a clear message if the connection fails.

# Wrong Redis Queue Key Name
File: api/main.py, line 9
Problem: Jobs pushed to Redis queue key `"job"` (singular). The worker consumes from `"jobs"` (plural), so jobs are enqueued but never picked up.
The entire pipeline is silently broken end to end.
*Fix: Changed `r.lpush("job", job_id)` to `r.lpush("jobs", job_id)`.

# Missing Job Returns HTTP 200 Instead of HTTP 404
File: api/main.py, lines 15-16
Problem: When a job is not found, the endpoint returns HTTP 200 with `{"error": "not found"}` in the body. The frontend polling logic treats this as a successful response and never surfaces the error to the user.
*Fix: Replaced `return {"error": "not found"}` with `raise HTTPException(status_code=404, detail="Job not found")`.

# No /health Endpoint
File: api/main.py (missing route)
Problem: No health check endpoint exists. Required for the Docker HEALTHCHECK instruction and for Compose `depends_on: condition: service_healthy` to work correctly.
*Fix: Added `GET /health` route returning `{"status": "ok"}`.

# decode_responses Not Set on Redis Client
File: api/main.py, line 6
Problem: Redis client created without `decode_responses=True`, so allvalues returned from Redis are raw bytes. The original code manually calls `.decode()` which works, but is error-prone and inconsistent.
*Fix: Added `decode_responses=True` to the Redis client constructor, removing the need for manual `.decode()` calls throughout.


2. WORKER (`worker/worker.py`)

Hardcoded Redis Host
File: worker/worker.py, line 5
Problem: Redis connection hardcoded to `localhost:6379`. Fails inside Docker for the same reason identified in the API. localhost resolves to the worker container itself, not the Redis service.
*Fix: Changed to use `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` environment variables with sensible defaults.

Wrong Redis Queue Key Name
File: worker/worker.py, line 12
Problem: Worker calls `r.brpop("job")` (singular) but the API pushes to `"jobs"` (plural). Jobs are enqueued by the API and never consumed by the worker. No error is raised — they simply accumulate in the queue silently.
*Fix: Changed `brpop("job", timeout=5)` to `brpop("jobs", timeout=5)`.

Signal Imported But Graceful Shutdown Never Implemented
File: worker/worker.py, line 4
Problem: `signal` is imported but never used (Flake8: F401). More critically, without SIGTERM handling, `docker stop` sends SIGTERM which Python ignores by default. Docker then waits 10 seconds and sends SIGKILL, potentially killing a job mid-processing and leaving it in a broken state.
*Fix: Implemented `handle_shutdown` function registered for both SIGTERM and SIGINT that exits cleanly via `sys.exit(0)`.

# No Error Handling in Main Loop
*File: worker/worker.py, lines 11-14
Problem: The `while True` loop has no try/except. Any Redis disconnection raises an unhandled exception that crashes the worker permanently. There is no reconnection or recovery logic.
*Fix: Wrapped loop body in try/except catching `redis.exceptions.ConnectionError` separately from general exceptions, with a 5-second retry wait on connection failures.

# No Error Handling in process_job
File: worker/worker.py, lines 7-10
Problem: If the `r.hset` call inside `process_job` fails for any reason, the job status is never updated. The job stays as `"queued"` forever but has already been popped off the queue and is unrecoverable.
*Fix: Wrapped body in try/except. On failure, attempts to set job status to `"failed"` so the frontend can surface the error.

# .decode() Called on Already-Decoded String
File: worker/worker.py, line 14
Problem: `job_id.decode()` is called after `brpop` returns, but with `decode_responses=True` set on the Redis client, `brpop` already returns a plain string. Calling `.decode()` on a string raises `AttributeError` at runtime.
*Fix: Removed `.decode()` — `job_id` is passed directly to `process_job`.

# No Redis Startup Connection Check
File: worker/worker.py (missing)
Problem: Worker starts processing immediately with no validation that Redis is reachable. Crashes with an unhelpful traceback if Redis is not yet available.
*Fix: Added `wait_for_redis()` function that loops calling `r.ping()` every 2 seconds until Redis responds, then proceeds to the main loop.



3. Frontend Server (`frontend/app.js`)

# Hardcoded API URL
File: frontend/app.js, line 5
Problem: `API_URL` hardcoded as `http://localhost:8000`. Inside Docker, localhost resolves to the frontend container itself just like we pointed out earlier, not the API service. Every proxied request fails with ECONNREFUSED.
*Fix: Changed to `process.env.API_URL || "http://api:8000"` so the service name is resolved correctly within the Docker network.

# Request Body Not Forwarded in /submit
File: frontend/app.js, line 10
Problem: The `/submit` handler calls `axios.post(API_URL/jobs)` without passing `req body`. Any parameters sent by the client are silently dropped and never reach the API.
*Fix: Changed to `axios.post(\`${API_URL}/jobs\`, req.body)`.

# Errors Swallowed With No Logging
File: frontend/app.js, lines 12 and 18
Problem: Both catch blocks return a generic 500 response with no server-side logging. When the service fails inside a container, there is no diagnostic output to help debug the issue.
Fix: Added `console.error(err?.response?.data || err.message)` at the start of both catch blocks.

# No /health Endpoint
File: frontend/app.js (missing route)
Problem: No health check endpoint exists. Required for Docker HEALTHCHECK and Compose `depends_on: condition: service_healthy`.
*Fix: Added `GET /health` route returning `{"status": "ok"}`.

# Missing Explicit Host Binding
File: frontend/app.js, line 22
Problem: `app.listen(3000)` binds to `127.0.0.1` by default on some Node.js versions, making the service unreachable from outside the container.
*Fix: Changed to `app.listen(3000, '0.0.0.0', ...)`.



4. Views (`frontend/views/index.html`)

# submitJob Has No Error Handling
File: frontend/views/index.html, submitJob function
Problem: No try/catch around the fetch call. Any network error or non-JSON response throws an unhandled promise rejection. The user sees no feedback and the UI freezes silently.
Fix: Wrapped entire function body in try/catch. Error message is displayed in the `#result` div on failure.

# data.job_id Accessed Without Existence Check
File: frontend/views/index.html, submitJob function
Problem: `data.job_id` is used directly without checking if it exists. If the API returns an error object, `data.job_id` is `undefined`, `pollJob(undefined)` is called, and the client polls `/status/undefined` indefinitely.
*Fix: Added guard: `if (!data.job_id) throw new Error(data.error || 'No job_id returned')`.

# POST Request Missing Content-Type Header
File: frontend/views/index.html, submitJob function
Problem: The fetch POST request has no `Content-Type: application/json` header and no body. The Express backend's `express.json()` middleware requires this header to parse request bodies correctly.
*Fix: Added `headers: { 'Content-Type': 'application/json' }` and `body: JSON.stringify({})` to the fetch options.

# pollJob Has No Error Handling
File: frontend/views/index.html, pollJob function
Problem: No try/catch around the fetch call. A 404 or network errorcauses `data.status` to be `undefined`. `renderJob` displays `"undefined"`, and since `undefined !== 'completed'` is always true, polling loops forever hammering the server.
*Fix: Wrapped in try/catch, added `res.ok` check before parsing JSON, renders an error state on failure.

# Polling Never Stops on Failed Status
File: frontend/views/index.html, pollJob function
Problem: The polling condition only stops on `"completed"`. If the worker sets a job to `"failed"`, the client polls indefinitely.
*Fix: Changed condition to `data.status !== 'completed' && data.status !== 'failed'`.

# jobIds Array Is Dead Code
File: frontend/views/index.html
Problem: `const jobIds = []` is declared and `.push()` is called on it, but the array is never read anywhere. ESLint will flag this as an unused variable. Likely intended for a page-reload restore feature that was never implemented.
*Fix: Removed the `jobIds` array entirely.


5. Dependencies

# api/requirements.txt
File: api/requirements.txt, lines 1-3
Problem: `fastapi`, `uvicorn`, and `redis` are all unpinned. Every build may pull different versions making builds non-reproducible. FastAPI has frequent breaking changes between minor versions Bare `uvicorn` is missing the `[standard]` extra which provides `uvloop` and `httptools` needed for production performance.
*Fix: Pinned all versions: `fastapi==0.111.0`, `uvicorn[standard]==0.29.0`,
`redis==5.0.1`. Added `hiredis==2.3.2` for C-accelerated Redis parsing.

# worker/requirements.txt
File: worker/requirements.txt, line 1
Problem: `redis` is completely unpinned. Builds are not reproducible and Trivy cannot accurately scan unversioned dependencies.
*Fix: Pinned to `redis==5.0.1`. Added `hiredis==2.3.2`.

# frontend/package.json
File: frontend/package.json
Problem: No `engines` field. The container could be built with any Node.js version leading to inconsistent behaviour across environments.
*Fix: Added `"engines": { "node": ">=18.0.0" }`.

# frontend/package.json
File: frontend/package.json
Problem: The CI pipeline lint stage runs ESLint against `app.js` but ESLint is not listed in `devDependencies`. The lint stage will fail immediately on a clean install.
*Fix: Added `"eslint": "^8.57.0"` to `devDependencies`.
