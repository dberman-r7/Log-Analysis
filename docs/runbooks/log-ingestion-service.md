# Runbook: Rapid7 InsightOps Log Ingestion Service

**Service Name**: log-ingestion-service  
**Version**: 0.1.0  
**Owner**: Development Team  
**Last Updated**: 2026-02-10

---

## Service Overview

### Purpose

The Log Ingestion Service pulls logs from the Rapid7 InsightOps API and stores them in Apache Parquet format for analytics. It provides:
- Automated log extraction from Rapid7
- Dynamic CSV schema detection
- Efficient Parquet file storage with compression
- Structured logging and metrics

### Architecture

```
[Rapid7 API] → [API Client] → [CSV Parser] → [Parquet Writer] → [File System]
                    ↓               ↓              ↓
                 [Structured Logs & Metrics]
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| API Client | Fetch logs from Rapid7 | requests library |
| Parser | Parse CSV with dynamic schema | pandas |
| Parquet Writer | Write compressed Parquet files | pyarrow |
| Configuration | Manage settings | pydantic |
| Logging | Structured observability | structlog |

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
python -m src.log_ingestion.main

# Start service (background)
nohup python -m src.log_ingestion.main > /var/log/log-ingestion/service.log 2>&1 &

# Stop service
kill -SIGTERM <PID>

# Check configuration
python -c "from src.log_ingestion.config import LogIngestionConfig; print(LogIngestionConfig())"
```

---

## Configuration Reference

### Required Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `RAPID7_API_KEY` | API authentication key | `abc123...` | ✅ Yes |
| `RAPID7_API_ENDPOINT` | Base API URL | `https://api.rapid7.com/v1` | ✅ Yes |
| `OUTPUT_DIR` | Directory for Parquet files | `/data/logs` | ✅ Yes |

### Optional Environment Variables

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `BATCH_SIZE` | Records per batch | `1000` | `100` - `10000` |
| `RATE_LIMIT` | Max API requests/minute | `60` | `1` - `1000` |
| `RETRY_ATTEMPTS` | Max retry attempts | `3` | `1` - `10` |
| `PARQUET_COMPRESSION` | Compression algorithm | `snappy` | `snappy`, `gzip`, `brotli`, `none` |

### Configuration File: `.env`

```bash
# Required
RAPID7_API_KEY=your_api_key_here
RAPID7_API_ENDPOINT=https://api.rapid7.com/v1
OUTPUT_DIR=/data/logs

# Optional
LOG_LEVEL=INFO
BATCH_SIZE=1000
RATE_LIMIT=60
RETRY_ATTEMPTS=3
PARQUET_COMPRESSION=snappy
```

**Important**: Never commit `.env` file to git! Use `.env.example` as template.

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment tool (venv or virtualenv)
- Write access to output directory
- Network access to Rapid7 API

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/your-org/Log-Analysis.git
cd Log-Analysis

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Create output directory
mkdir -p /data/logs

# 6. Test configuration
python -c "from src.log_ingestion.config import LogIngestionConfig; LogIngestionConfig()"
```

---

## Operations

### Starting the Service

#### One-Time Execution

For manual, one-time log extraction:

```bash
# Activate virtual environment
source venv/bin/activate

# Run service
python -m src.log_ingestion.main
```

#### Background Service

For continuous operation:

```bash
# Start in background
nohup python -m src.log_ingestion.main > /var/log/log-ingestion/service.log 2>&1 &

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
ExecStart=/opt/log-analysis/venv/bin/python -m src.log_ingestion.main
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
0 * * * * /opt/log-analysis/venv/bin/python -m src.log_ingestion.main >> /var/log/log-ingestion/cron.log 2>&1
```

### Stopping the Service

```bash
# If running in foreground: Ctrl+C

# If running in background with PID file
kill -SIGTERM $(cat /var/run/log-ingestion.pid)

# With systemd
sudo systemctl stop log-ingestion

# Force kill (not recommended)
pkill -f "python -m src.log_ingestion.main"
```

### Restarting the Service

```bash
# Systemd
sudo systemctl restart log-ingestion

# Manual
kill -SIGTERM $(cat /var/run/log-ingestion.pid)
sleep 2
python -m src.log_ingestion.main &
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
- `parse_start`: CSV parsing started
- `parse_complete`: Parsing finished
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
python -c "from src.log_ingestion.config import LogIngestionConfig; LogIngestionConfig()"

# Check environment variables
env | grep RAPID7
env | grep OUTPUT_DIR
```

**Solutions**:
1. Verify all required environment variables are set
2. Check API key is not empty
3. Verify API endpoint is valid URL
4. Ensure output directory exists and is writable
5. Check Python version is 3.9+

---

### Issue: Authentication Failures (401/403)

**Symptoms**:
- API calls return 401 Unauthorized or 403 Forbidden
- Logs show authentication errors

**Diagnosis**:
```bash
# Test API key manually
curl -H "Authorization: Bearer $RAPID7_API_KEY" $RAPID7_API_ENDPOINT/test
```

**Solutions**:
1. Verify API key is correct and not expired
2. Check API key has required permissions
3. Rotate API key in Rapid7 console
4. Update `.env` file with new key
5. Restart service

**Prevention**:
- Set up API key rotation schedule (quarterly)
- Monitor for approaching expiration dates

---

### Issue: High Parse Error Rate

**Symptoms**:
- `parse_errors_total` metric increasing
- Logs show "Parse Error" events
- Incomplete data in Parquet files

**Diagnosis**:
```bash
# Check error logs
grep "parse_error" /var/log/log-ingestion/service.log | jq .

# Review sample of failed data
grep "parse_error" /var/log/log-ingestion/service.log | jq -r .raw_data | head -5
```

**Solutions**:
1. **Schema Changed**: Update parser to handle new fields
2. **Malformed CSV**: Contact Rapid7 support, add validation
3. **Encoding Issues**: Check character encoding in parser
4. **Special Characters**: Improve CSV parsing options

**Temporary Mitigation**:
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Reduce batch size to isolate problematic records
- Skip malformed records (log for manual review)

---

### Issue: Disk Space Exhaustion

**Symptoms**:
- Service fails with "No space left on device"
- Disk usage > 90%
- File write errors

**Diagnosis**:
```bash
# Check disk usage
df -h /data/logs

# Check file sizes
du -sh /data/logs/*

# Count files
find /data/logs -name "*.parquet" | wc -l
```

**Solutions**:
1. **Immediate**: Delete old files
   ```bash
   find /data/logs -name "*.parquet" -mtime +30 -delete
   ```

2. **Short-term**: Archive to cold storage
   ```bash
   tar -czf logs-archive-$(date +%Y%m).tar.gz /data/logs/2026/01/
   aws s3 cp logs-archive-*.tar.gz s3://bucket/archives/
   ```

3. **Long-term**: 
   - Implement automated retention policy
   - Increase disk size
   - Add file rotation to service

**Prevention**:
- Set up disk space monitoring
- Implement automated archival (cron job)
- Configure retention policy in service

---

### Issue: API Rate Limiting (429)

**Symptoms**:
- API returns 429 Too Many Requests
- Logs show rate limit backoff
- Slow data ingestion

**Diagnosis**:
```bash
# Check rate limit metrics
grep "rate_limit" /var/log/log-ingestion/service.log | jq .

# Count API calls per minute
grep "api_request" /var/log/log-ingestion/service.log | \
  jq -r .timestamp | cut -d: -f1-2 | uniq -c
```

**Solutions**:
1. **Reduce Rate**: Lower `RATE_LIMIT` environment variable
   ```bash
   RATE_LIMIT=30  # Reduce from 60 to 30 requests/min
   ```

2. **Increase Batch Size**: Fetch more logs per request
   ```bash
   BATCH_SIZE=5000  # Increase from 1000 to 5000
   ```

3. **Contact Rapid7**: Request rate limit increase

**Prevention**:
- Monitor Retry-After headers from API
- Implement adaptive rate limiting

---

### Issue: Memory Usage High

**Symptoms**:
- Process memory > 1GB
- Out of memory errors
- System slowdown

**Diagnosis**:
```bash
# Check process memory
ps aux | grep log_ingestion

# Monitor memory over time
watch -n 5 'ps aux | grep log_ingestion'
```

**Solutions**:
1. **Reduce Batch Size**:
   ```bash
   BATCH_SIZE=500  # Reduce from 1000
   ```

2. **Process in Smaller Chunks**: Modify code to process incrementally

3. **Increase System Memory**: Add RAM or adjust limits

**Prevention**:
- Profile memory usage with benchmark tests
- Set memory limits with systemd:
  ```ini
  [Service]
  MemoryMax=512M
  ```

---

### Issue: Parquet Files Not Readable

**Symptoms**:
- Pandas/Spark cannot read Parquet files
- File corruption errors
- Schema mismatch errors

**Diagnosis**:
```bash
# Validate Parquet file
parquet-tools meta /data/logs/file.parquet

# Try reading with pandas
python -c "import pandas as pd; print(pd.read_parquet('/data/logs/file.parquet').head())"
```

**Solutions**:
1. **Corruption**: Delete and regenerate
2. **Schema Issues**: Check schema consistency
3. **Compression Issues**: Try different compression algorithm

**Prevention**:
- Add file validation after write
- Use checksums for integrity verification

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
|------------|---------|---------------|
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

python -c "
from src.log_ingestion.config import LogIngestionConfig
try:
    config = LogIngestionConfig()
    print('✅ Configuration valid')
    print(f'API Endpoint: {config.rapid7_api_endpoint}')
    print(f'Output Dir: {config.output_dir}')
    print(f'Batch Size: {config.batch_size}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"
```

---

**Runbook Version**: 1.0  
**Last Updated**: 2026-02-10  
**Next Review**: 2026-05-10
