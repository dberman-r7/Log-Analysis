# Runbook: Rapid7 InsightOps Log Ingestion Service

**Service Name**: log-ingestion-service  
**Version**: 0.1.0  
**Owner**: Development Team  
**Last Updated**: 2026-02-10

---

## Service Overview

### Purpose

The Log Ingestion Service pulls logs from the Rapid7 InsightOps **Log Search** API and stores them in Apache Parquet format for analytics. It provides:
- Automated log extraction from Rapid7
- Efficient Parquet file storage with compression
- Structured logging and metrics

### Architecture

```
[Rapid7 Log Search API] → [API Client] → [(JSON→tabular) Transformation] → [Parquet Writer] → [File System]
           ↑
   (submit query → poll Self link → follow Next page)
```

### Key Components

| Component | Purpose | Technology |
|----------|---------|------------|
| API Client | Fetch logs from Rapid7 Log Search (query/poll/pages) | requests library |
| Parser/Transform | Convert Log Search JSON events to a tabular structure | pandas |
| Parquet Writer | Write compressed Parquet files | pyarrow |
| Configuration | Manage settings | pydantic |
| Logging | Structured observability | structlog |

---

## Running from IntelliJ IDEA (Run Configurations)

These steps work in IntelliJ IDEA (with the Python plugin) and PyCharm. They’re the most reliable way to run the service and utilities without fighting shell/env differences.

### Prerequisites

- A configured Python interpreter for the project (recommended: a virtualenv).
- A `.env` file in the repository root (or another path you control).

> Tip: In the IDE, open *Settings → Project → Python Interpreter* and confirm the interpreter has the project dependencies installed.

### Recommended: create a shared “Common” template

If you’ll run this often, keep the following consistent across configs:
- **Working directory**: repo root (`.../Log-Analysis-Working`)
- **Interpreter**: the project venv/interpreter
- **Environment**: either load from `.env` (preferred) or set env vars explicitly

### Run the main ingestion pipeline

Create a **Python** Run Configuration:

1. **Run → Edit Configurations… → + → Python**
2. Set:
   - **Name**: `Log Ingestion (main)`
   - **Module name**: `src.log_ingestion.main`
     - (Equivalent to: `python3 -m src.log_ingestion.main`)
   - **Working directory**: the repo root (`.../Log-Analysis-Working`)
   - **Parameters** (example):
     - `--start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z"`
     - Optional: `--partition-date "2026-02-10"`
3. **Environment variables** (choose one):

   **Option A (preferred): load from `.env`**
   - If your IDE supports an “EnvFile”/“.env file” field, point it at the repo root `.env`.

   **Option B: set environment variables directly**
   - Paste key=val pairs into the Run Configuration’s **Environment variables**.

Required variables for a real ingestion run:
- `RAPID7_API_KEY`
- `RAPID7_DATA_STORAGE_REGION`
- `RAPID7_LOG_KEY`

Optional:
- `OUTPUT_DIR` (defaults to `./data/logs`)

Optional variables:
- `RAPID7_QUERY`
- `LOG_LEVEL`, `BATCH_SIZE`, `RATE_LIMIT`, `RETRY_ATTEMPTS`, `PARQUET_COMPRESSION`

### Run the “Select Log” utility (writes `RAPID7_LOG_KEY` into `.env`)

This is an interactive helper that:
1) lists **log sets** from the Rapid7 management endpoint,
2) prompts you to pick a log set,
3) lists the **logs within that log set**,
4) prompts you to pick a log, and
5) updates `RAPID7_LOG_KEY` in your chosen `.env` file.

Create a second **Python** Run Configuration:

- **Name**: `Log Ingestion (select log)`
- **Module name**: `src.log_ingestion.main`
- **Working directory**: repo root
- **Parameters** (example):
  - `--select-log --env-file .env --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T00:00:01Z"`

Notes:
- `--start-time/--end-time` are required by the CLI argument parser, but are ignored when `--select-log` is provided.
- The IDE Run tool window is interactive here and will prompt for input (choose a log set number/id, then a log number/id).
- If you run in an IDE that can’t provide stdin to the process, run the same command from a terminal instead.

---

## Quick Reference

### Service Status

```bash
# Check if service is running
ps aux | grep log_ingestion

# Check recent logs
tail -f /var/log/log-ingestion/service.log

# Check output files
ls -lh /data/logs/*.parquet
```

### Common Commands

```bash
# Start service (one-time run)
python3 -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z"

# Start service (background)
nohup python3 -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z" > /var/log/log-ingestion/service.log 2>&1 &

# Stop service
kill -SIGTERM <PID>

# Check configuration
python3 -c "from src.log_ingestion.config import LogIngestionConfig; print(LogIngestionConfig())"
```

---

## Configuration Reference

### Required Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `RAPID7_API_KEY` | API authentication key (sent as `x-api-key`) | `abc123...` | ✅ Yes |
| `RAPID7_DATA_STORAGE_REGION` | Rapid7 data storage region used to construct the Log Search base URL | `us` | ✅ Yes |
| `RAPID7_LOG_KEY` | Log key used in the Log Search endpoint path | `your-log-key` | ✅ Yes |

Optional:
- `OUTPUT_DIR` (defaults to `./data/logs`)

### Optional Environment Variables

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `RAPID7_QUERY` | Log Search query filter (provider query language) | *(empty / provider default)* | provider-specific string |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `BATCH_SIZE` | Records per batch | `1000` | `100` - `10000` |
| `RATE_LIMIT` | Max API requests/minute | `60` | `1` - `1000` |
| `RETRY_ATTEMPTS` | Max retry attempts | `3` | `1` - `10` |
| `PARQUET_COMPRESSION` | Compression algorithm | `snappy` | `snappy`, `gzip`, `brotli`, `none` |

### Configuration File: `.env`

```bash
# Required
RAPID7_API_KEY=your_api_key_here
RAPID7_DATA_STORAGE_REGION=us
RAPID7_LOG_KEY=your_log_key_here

# Optional (defaults to ./data/logs)
OUTPUT_DIR=./data/logs

# Optional
RAPID7_QUERY=where(message contains \"error\")
LOG_LEVEL=INFO
BATCH_SIZE=1000
RATE_LIMIT=60
RETRY_ATTEMPTS=3
PARQUET_COMPRESSION=snappy
```

**Important**:
- Never commit `.env` to git.
- Don’t hardcode API keys in scripts or shell history. Prefer loading from `.env` or your secret manager.

> Note (macOS/dev): `OUTPUT_DIR` now defaults to `./data/logs` to avoid writing to read-only paths like `/data`.
> You can still override it (for example, `OUTPUT_DIR=/tmp/logs`).

---

## Operations

### Rapid7 Log Search request lifecycle (operational model)

The provider Log Search API is asynchronous and link-driven.

**Base URL** (derived from region):
- `https://{region}.rest.logs.insight.rapid7.com`

**Query endpoint** (derived from region + log key):
- `GET https://{region}.rest.logs.insight.rapid7.com/query/logs/{log_key}`

**Management endpoints**:
- List log sets: `GET https://{region}.rest.logs.insight.rapid7.com/management/logsets`
- List logs (legacy / flat): `GET https://{region}.rest.logs.insight.rapid7.com/management/logs`
- List logs in a log set: `GET https://{region}.rest.logs.insight.rapid7.com/management/logsets/{logSetId}/logs`

**Auth**:
- Requests include `x-api-key: $RAPID7_API_KEY`

**Lifecycle**:
1. **Submit** a query request with query params (`from`, `to`, `query`).
2. The response includes a `links` array.
   - `rel=Self`: continuation link used for **polling** while the query is still running.
   - `rel=Next`: link to the **next page** of results.
3. The client polls the `Self` link with bounded exponential backoff until the query completes.
4. When a page is complete, the client follows `Next` (if present) to fetch subsequent pages.
5. If the API returns **HTTP 429**, the client waits for the number of seconds in the `X-RateLimit-Reset` header, then retries.

### Starting the Service

#### One-Time Execution

For manual, one-time log extraction:

```bash
# Activate virtual environment
source venv/bin/activate

# Run service
python3 -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z"
```

#### Background Service

For continuous operation:

```bash
# Start in background
nohup python3 -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z" > /var/log/log-ingestion/service.log 2>&1 &

# Save PID
echo $! > /var/run/log-ingestion.pid
```

#### Systemd Service (Recommended for Production)

Create `/etc/systemd/system/log-ingestion.service`:

```ini
[Unit]
Description=Rapid7 Log Ingestion Service
After=network.target

[Service]
Type=simple
User=logservice
Group=logservice
WorkingDirectory=/opt/log-analysis
Environment="PATH=/opt/log-analysis/venv/bin"
EnvironmentFile=/opt/log-analysis/.env
ExecStart=/opt/log-analysis/venv/bin/python -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z"
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/log-ingestion/service.log
StandardError=append:/var/log/log-ingestion/error.log

[Install]
WantedBy=multi-user.target
```

Then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start log-ingestion

# Enable on boot
sudo systemctl enable log-ingestion

# Check status
sudo systemctl status log-ingestion
```

#### Cron Job (Scheduled Execution)

For periodic execution (e.g., hourly):

```bash
# Edit crontab
crontab -e

# Add entry (runs every hour)
0 * * * * /opt/log-analysis/venv/bin/python -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z" >> /var/log/log-ingestion/cron.log 2>&1
```

### Stopping the Service

```bash
# If running in foreground: Ctrl+C

# If running in background with PID file
kill -SIGTERM $(cat /var/run/log-ingestion.pid)

# With systemd
sudo systemctl stop log-ingestion

# Force kill (not recommended)
pkill -f "python3 -m src.log_ingestion.main"
```

### Restarting the Service

```bash
# Systemd
sudo systemctl restart log-ingestion

# Manual
kill -SIGTERM $(cat /var/run/log-ingestion.pid)
sleep 2
python3 -m src.log_ingestion.main --start-time "2026-02-10T00:00:00Z" --end-time "2026-02-10T01:00:00Z" &
```

---

## Monitoring

### Key Metrics

| Metric | Description | Normal Range | Alert Threshold |
|--------|-------------|--------------|-----------------|
| `api_calls_total{status="200"}` | Successful API calls | Varies | N/A |
| `api_calls_total{status="4xx"}` | Client errors | 0 | > 0 |
| `api_calls_total{status="5xx"}` | Server errors | 0 | > 3 in 5 min |
| `api_call_duration_seconds` | API latency | 0.5-3s | > 5s (P95) |
| `logs_fetched_total` | Logs successfully fetched | Varies | N/A |
| `parse_errors_total` | Parse failures | 0 | > 5% of total |
| `parquet_files_written_total` | Files created | Varies | N/A |
| `disk_usage_bytes` | Output directory size | Varies | > 90% full |

### Structured Logs

Logs are written in JSON format to stdout/stderr:

```json
{
  "timestamp": "2026-02-10T10:00:00Z",
  "level": "INFO",
  "service": "log-ingestion",
  "version": "0.1.0",
  "environment": "production",
  "trace_id": "abc123",
  "event": "logs_fetched",
  "record_count": 1000,
  "duration_ms": 450
}
```

**Key Log Events**:
- `service_started`: Service initialization
- `config_loaded`: Configuration loaded successfully
- `api_request`: API call initiated
- `api_response`: API call completed
- `logs_fetched`: Logs retrieved from API
- `transform_start`: JSON-to-tabular transformation started
- `transform_complete`: Transformation finished
- `file_write_start`: Parquet write started
- `file_write_complete`: File written successfully
- `batch_complete`: Batch processing finished
- `service_complete`: Service run completed
- `error`: Error occurred (includes details)

### Health Checks

```bash
# Check if process is running
pgrep -f "log_ingestion.main"

# Check recent activity (logs in last 5 minutes)
find /data/logs -mmin -5 -name "*.parquet"

# Check for errors in logs
tail -n 100 /var/log/log-ingestion/service.log | grep '"level":"ERROR"'

# Disk space check
df -h /data/logs
```

---

## Alerting

### Critical Alerts (Page Immediately)

**Alert 1: Authentication Failure**
- **Condition**: API returns 401/403 status > 3 times in 5 minutes
- **Action**: Check API key validity, rotate if needed
- **Escalation**: Security team if credential compromise suspected

**Alert 2: Service Down**
- **Condition**: Process not running for > 5 minutes
- **Action**: Check logs, restart service
- **Escalation**: On-call engineer after 15 minutes

**Alert 3: Disk Full**
- **Condition**: Output directory > 95% full
- **Action**: Archive old files, expand disk
- **Escalation**: Infrastructure team

### Warning Alerts (Investigate During Business Hours)

**Alert 4: High Parse Error Rate**
- **Condition**: Parse errors > 5% of total logs over 15 minutes
- **Action**: Check for log format changes, review error logs
- **Escalation**: Development team if persists

**Alert 5: API Latency High**
- **Condition**: P95 API latency > 5 seconds for 10 minutes
- **Action**: Check Rapid7 API status, adjust rate limits
- **Escalation**: Rapid7 support if API issue

**Alert 6: No Logs Fetched**
- **Condition**: Zero logs fetched for 1 hour (if continuous mode)
- **Action**: Check API connectivity, verify there are logs to fetch
- **Escalation**: Development team

---

## Troubleshooting

### Issue: Service Fails to Start

**Symptoms**:
- Process exits immediately
- Configuration error in logs

**Diagnosis**:
```bash
# Check configuration
python3 -c "from src.log_ingestion.config import LogIngestionConfig; LogIngestionConfig()"

# Check environment variables
env | grep RAPID7
env | grep OUTPUT_DIR
```

**Solutions**:
1. Verify all required environment variables are set
2. Ensure `RAPID7_DATA_STORAGE_REGION` and `RAPID7_LOG_KEY` are present
3. Ensure output directory exists and is writable
4. Check Python version is 3.9+

---

### Issue: Authentication Failures (401/403)

**Symptoms**:
- API calls return 401 Unauthorized or 403 Forbidden
- Logs show authentication errors

**Diagnosis**:
```bash
# Example endpoint shape (region + log key)
ENDPOINT="https://${RAPID7_DATA_STORAGE_REGION}.rest.logs.insight.rapid7.com/query/logs/${RAPID7_LOG_KEY}"

# Submit a minimal query (adjust body per your org/query needs)
curl -sS \
  -H "x-api-key: ${RAPID7_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"from":"2026-02-10T00:00:00Z","to":"2026-02-10T00:05:00Z","query":""}' \
  "$ENDPOINT" | head
```

**Solutions**:
1. Verify API key is correct and not expired
2. Check API key has required permissions
3. Rotate API key in Rapid7 console
4. Update `.env` (or secret manager) with the new key
5. Restart service

---

### Issue: API Rate Limiting (429)

**Symptoms**:
- API returns 429 Too Many Requests
- Logs show rate limit backoff
- Slow data ingestion

**What the client does**:
- Waits the number of seconds provided in the `X-RateLimit-Reset` header, then retries.

**Operator actions**:
1. Reduce request pressure by narrowing the queried time window (smaller from/to)
2. Ensure query filters are selective (add `RAPID7_QUERY`)
3. If available, tune polling/backoff settings via service configuration (without violating provider guidance)
4. Contact Rapid7 if you need a higher rate limit

---

### Issue: Region misconfiguration / wrong base URL

**Symptoms**:
- DNS failures (cannot resolve `https://{region}.rest.logs.insight.rapid7.com`)
- HTTP 404 on the query endpoint

**Diagnosis**:
```bash
# Sanity check the derived endpoint
echo "https://${RAPID7_DATA_STORAGE_REGION}.rest.logs.insight.rapid7.com/query/logs/${RAPID7_LOG_KEY}"
```

**Solutions**:
1. Confirm the correct Rapid7 data storage region for your account
2. Update `RAPID7_DATA_STORAGE_REGION`
3. Restart the service

---

### Issue: `python` command not found on macOS (use `python3`)

**Symptoms**:
- Running `python -m ...` fails with: `bash: python: command not found`

**Root cause**:
- On modern macOS installs, `python` is often not installed, or it’s intentionally absent.

**Fix**:
- Use `python3` explicitly for all commands.
- In IntelliJ IDEA Run Configurations, pick the correct interpreter and run the module (not a shell command).

---

### Issue: urllib3 LibreSSL warning (`NotOpenSSLWarning`)

You may see:
- `urllib3 v2 only supports OpenSSL 1.1.1+ ... LibreSSL ...`

**What it means**:
- Your Python’s `ssl` module is linked against LibreSSL, which urllib3 warns about. This is common on Apple-system Python.

**Mitigations** (choose one):
1. Prefer a virtualenv created from a modern Python distribution (e.g., python.org installer) that links against OpenSSL.
2. If this is dev-only and everything works, you can treat it as a warning (it doesn’t necessarily break functionality).

---

### Issue: 404 on `GET /management/logs`

**Symptoms**:
- Running `--select-log` fails with:
  - `404 Client Error: Not Found for url: https://{region}.rest.logs.insight.rapid7.com/management/logs`

**Likely causes**:
1. Wrong `RAPID7_DATA_STORAGE_REGION` for your account.
2. Base URL differs for your Rapid7 product/tenant (Rapid7 has multiple APIs and older docs sometimes show different paths).
3. Network proxy / SSL interception rewriting traffic.

**How to diagnose**:
- Confirm the derived URL:

```bash
echo "https://${RAPID7_DATA_STORAGE_REGION}.rest.logs.insight.rapid7.com/management/logs"
```

- If you have Rapid7 docs for your tenant, verify the correct host and path for the **management** API.

**What to do next**:
- Try the same region in a browser (expect 401/403 without auth, but not 404).
- If you have multiple regions, try `eu`, `us`, `ca`, `ap`, `au`.
- If you can fetch logs via the Rapid7 UI/API Explorer, copy the exact management/logs URL shape and we’ll align the client.

---

## Maintenance

### Routine Maintenance Tasks

#### Daily
- [ ] Check service is running
- [ ] Review error logs for anomalies
- [ ] Verify new Parquet files are being created
- [ ] Check disk space

#### Weekly
- [ ] Review metrics and trends
- [ ] Archive old log files
- [ ] Check for dependency updates
- [ ] Review parse error patterns

#### Monthly
- [ ] Update dependencies (security patches)
- [ ] Review and optimize configuration
- [ ] Performance tuning based on metrics
- [ ] Rotate API credentials

#### Quarterly
- [ ] Full service review
- [ ] Update documentation
- [ ] Review and adjust alerting thresholds
- [ ] Disaster recovery drill

### Log Rotation

```bash
# Logrotate configuration: /etc/logrotate.d/log-ingestion
/var/log/log-ingestion/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 logservice logservice
    sharedscripts
    postrotate
        systemctl reload log-ingestion > /dev/null 2>&1 || true
    endscript
}
```

### Backup and Recovery

**Backup**:
```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup Parquet files (to S3)
aws s3 sync /data/logs s3://backup-bucket/logs/

# Backup with retention
find /data/logs -name "*.parquet" -mtime -7 | \
  xargs tar -czf backup-$(date +%Y%m%d).tar.gz
```

**Recovery**:
```bash
# Restore from backup
aws s3 sync s3://backup-bucket/logs/ /data/logs/

# Verify integrity
find /data/logs -name "*.parquet" -exec parquet-tools meta {} \;
```

---

## Performance Tuning

### Optimization Strategies

**For High Throughput**:
```bash
# Increase batch size
BATCH_SIZE=5000

# Increase rate limit (if API allows)
RATE_LIMIT=120

# Use faster compression
PARQUET_COMPRESSION=snappy  # Faster than gzip
```

**For Low Memory**:
```bash
# Decrease batch size
BATCH_SIZE=500

# Process one batch at a time
# (Default behavior)
```

**For Better Compression**:
```bash
# Use better compression (slower)
PARQUET_COMPRESSION=gzip
```

### Benchmarking

```bash
# Run performance benchmark
python tests/benchmark.py

# Expected results:
# - Parse rate: > 10,000 entries/second
# - Write rate: > 5,000 entries/second
# - Memory: < 500 MB
# - Compression: > 70%
```

---

## Security

### Credential Management

**Best Practices**:
- ✅ Store credentials in `.env` file (not in code)
- ✅ Set file permissions: `chmod 600 .env`
- ✅ Rotate API keys quarterly
- ✅ Use separate keys for dev/staging/prod
- ✅ Never commit `.env` to git

**Rotation Procedure**:
1. Generate new API key in Rapid7 console
2. Test new key in development
3. Update production `.env` file
4. Restart service
5. Verify service is working
6. Revoke old API key

### Access Control

**File Permissions**:
```bash
# Output directory
chmod 750 /data/logs
chown logservice:analytics /data/logs

# Parquet files
chmod 640 /data/logs/*.parquet

# Configuration file
chmod 600 .env
chown logservice:logservice .env
```

---

## Disaster Recovery

### Scenarios and Procedures

**Scenario 1: Complete Service Failure**
1. Check service status and logs
2. Restore from backup if needed
3. Restart service
4. Verify operation
5. Review root cause

**Scenario 2: Data Corruption**
1. Identify corrupted files
2. Delete corrupted files
3. Re-fetch data from Rapid7 API for time period
4. Verify integrity

**Scenario 3: API Credential Compromise**
1. Immediately revoke compromised credentials
2. Generate new API key
3. Update service configuration
4. Audit access logs
5. Report to security team

**Recovery Time Objectives**:
- Service restart: < 5 minutes
- Configuration recovery: < 15 minutes
- Data re-ingestion: Variable (depends on time range)

---

## Support Contacts

| Issue Type | Contact | Response Time |
|----------|---------|------------|
| Service Down | On-Call Engineer | 15 minutes |
| Configuration | Development Team | 1 business day |
| API Issues | Rapid7 Support | 4 hours (SLA) |
| Disk Space | Infrastructure Team | 1 hour |
| Security | Security Team | Immediate |

**Escalation Path**:
1. On-Call Engineer
2. Tech Lead
3. Engineering Manager
4. CTO

---

## Appendix

### Useful Scripts

**Check Service Health**:
```bash
#!/bin/bash
# health-check.sh

if pgrep -f "log_ingestion.main" > /dev/null; then
    echo "Service is running"
    exit 0
else
    echo "Service is NOT running"
    exit 1
fi
```

**Archive Old Files**:
```bash
#!/bin/bash
# archive-logs.sh

ARCHIVE_DIR="/archive/logs"
DAYS_TO_KEEP=30

find /data/logs -name "*.parquet" -mtime +$DAYS_TO_KEEP -exec mv {} $ARCHIVE_DIR \;
echo "Archived $(ls -1 $ARCHIVE_DIR | wc -l) files"
```

**Test Configuration**:
```bash
#!/bin/bash
# test-config.sh

python3 -c "
from src.log_ingestion.config import LogIngestionConfig
try:
    config = LogIngestionConfig()
    print('✅ Configuration valid')
    print(f'Region: {config.rapid7_data_storage_region}')
    print(f'Log Key: {config.rapid7_log_key}')
    print(f'Output Dir: {config.output_dir}')
    print(f'Batch Size: {config.batch_size}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"
```

### Selecting a Log (setting `RAPID7_LOG_KEY`)

Use the built-in helper to select a log set and then a log, and persist the chosen log id to your `.env` file.

**Command**:

```bash
python3 -m src.log_ingestion.main \
  --select-log \
  --env-file .env \
  --start-time "2026-02-10T00:00:00Z" \
  --end-time "2026-02-10T00:00:01Z"
```

Notes:
 - `--start-time/--end-time` are still required by the CLI parser, but are ignored when `--select-log` is provided.
 - The helper calls:
   - `GET https://{region}.rest.logs.insight.rapid7.com/management/logsets`
 - It resolves log membership from embedded `logs_info` in the logsets response (no per-logset membership endpoints).

Failure modes:
 - **401/403**: API key invalid or lacks access. Confirm `RAPID7_API_KEY`.
 - **429**: Rate limit exceeded; wait for reset and retry.
 - **No log sets/logs shown**: Account/region mismatch; verify `RAPID7_DATA_STORAGE_REGION`.

---

**Runbook Version**: 1.0  
**Last Updated**: 2026-02-10  
**Next Review**: 2026-05-10
