# Impact Assessment: CR-2026-02-10-001

**Change Request**: CR-2026-02-10-001 - Rapid7 InsightOps Log Ingestion Service  
**Assessment Date**: 2026-02-10  
**Assessed By**: Development Team

---

## 1. Code Impact

### Scope
- **Files to Create**: 23 files
  - 6 implementation files in `/src/log_ingestion/`
  - 8 test files in `/tests/`
  - 3 configuration files
  - 6 documentation files
- **Files to Modify**: 2 files
  - `README.md` - Add service description and usage
  - `/docs/requirements/rtm.md` - Add requirements REQ-004 through REQ-011
- **Files to Delete**: 0 files

### Complexity Estimate
**MEDIUM**
- Moderate API integration complexity
- Standard file I/O operations
- Well-established libraries (requests, pyarrow, pandas)
- Clear separation of concerns

### Dependencies Affected

**New Dependencies**:
- `requests>=2.31.0` - HTTP client for API calls
- `pyarrow>=14.0.0` - Parquet file handling
- `pandas>=2.1.0` - Data manipulation and CSV parsing
- `pydantic>=2.5.0` - Configuration validation
- `python-dotenv>=1.0.0` - Environment variable management
- `structlog>=23.2.0` - Structured logging

**Development Dependencies**:
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking support
- `ruff>=0.1.0` - Linting and formatting
- `bandit>=1.7.5` - Security scanning

### API Surface Changes
- **No API changes** - New standalone service
- **Breaking Changes**: NO
- **Backward Compatibility**: N/A (new service)

---

## 2. Security Impact

### Security Assessment
**MEDIUM RISK**

### Authentication/Authorization
- New credentials required: Rapid7 API key/token
- Service authenticates to external Rapid7 InsightOps API
- Credentials stored in environment variables only
- No hardcoded secrets permitted

### Data Exposure
- Service fetches logs from external API (Rapid7)
- Logs may contain PII depending on customer configuration
- Parquet files inherit same sensitivity as source logs
- File system access controls required

### Secret Management Strategy
✅ **Approved Approach**:
- Environment variables via `.env` file (development)
- System environment variables (production)
- `.env.example` template provided (no real secrets)
- `.gitignore` configured to exclude `.env` file
- No secrets in code, configuration files, or git history

❌ **Prohibited**:
- Hardcoded API keys in code
- Secrets in git commits
- Secrets in configuration files committed to git

### Threat Model

| Threat | Probability | Impact | Mitigation |
|--------|-------------|--------|------------|
| API credentials exposure | Low | Critical | Environment variables, .gitignore, access controls |
| Log data exposure via files | Low | High | File permissions, encryption at rest (recommended) |
| API rate limiting / DoS | Medium | High | Rate limiting, exponential backoff, configurable delays |
| Malicious log injection | Low | Medium | Input validation, schema enforcement, sanitization |

### Security Controls

**Input Validation**:
- Validate API responses before processing
- Sanitize CSV data during parsing
- Enforce schema constraints
- Handle malformed data gracefully

**Access Controls**:
- Restrict file system permissions on Parquet files
- Document recommended access control policies
- Audit logging for security events

**Compliance Considerations**:
- GDPR: Log data may contain PII - document data handling
- SOC2: Audit logging required - implement structured logs
- Data retention: Configurable retention policies needed

### Security Review
**Status**: APPROVED  
**Reviewer**: Security Team  
**Date**: 2026-02-10  
**Notes**: Approved with conditions - implement all security controls as documented

---

## 3. Performance Impact

### Performance Assessment
**POSITIVE** - New capability, no impact on existing systems

### Resource Requirements

**CPU Usage**: Low to Moderate
- API calls: Minimal CPU
- CSV parsing: Moderate CPU (pandas)
- Parquet writing: Moderate CPU (compression)

**Memory Usage**: 100-500 MB
- API response buffering: ~10-50 MB
- Pandas DataFrame: ~50-200 MB
- Parquet writer buffer: ~50-100 MB
- Peak memory: ~500 MB for large batches

**Disk I/O**: Moderate
- Parquet file writes: Sequential writes, compressed
- Expected compression ratio: 70-90% vs raw logs
- File rotation to manage disk usage

**Network I/O**: Depends on Configuration
- API call frequency
- Log volume per request
- Configurable batch sizes

### Scalability Design

**Horizontal Scaling**:
- Multiple instances with time-based partitioning
- Each instance handles different time ranges
- No shared state between instances

**Vertical Scaling**:
- Configurable batch sizes (memory vs throughput trade-off)
- Buffer size tuning
- Compression level adjustment

**File Partitioning**:
- Partition by date/time for manageable file sizes
- Recommended: One file per hour or day
- Enables parallel processing downstream

### Target Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| API call latency | < 5 seconds | Prometheus histogram |
| Parse + write latency | < 100ms per 1000 entries | In-process timing |
| Throughput | 1000-10000 entries/minute | Counter metrics |
| Memory footprint | < 500 MB | Process monitoring |
| Parquet compression | > 70% vs JSON | File size comparison |

### Performance Testing Plan
- Benchmark with various log volumes (1K, 10K, 100K entries)
- Measure memory usage under load
- Test compression ratios with real log data
- Validate sustained throughput over time

---

## 4. Testing Impact

### Test Strategy
**Comprehensive TDD Approach**: Unit → Integration → Manual

### New Tests Required

**Unit Tests** (15-20 tests):

`test_config.py`:
- Environment variable loading
- Configuration validation (required fields)
- Default values
- Invalid configuration handling
- Pydantic model validation

`test_api_client.py`:
- Authentication header construction
- Successful log fetch
- HTTP error handling (401, 403, 404, 429, 500)
- Retry logic with exponential backoff
- Rate limiting behavior
- Timeout handling
- Connection error recovery

`test_parser.py`:
- CSV header detection
- First-row schema detection
- Data type inference
- Malformed CSV handling
- Empty data handling
- Schema caching
- Edge cases (special characters, quotes)

`test_parquet_writer.py`:
- Schema creation from parsed data
- Single batch writing
- Multiple batch writing
- File partitioning by date
- Compression verification
- File validation (readable)
- Buffer management

`test_main.py`:
- End-to-end orchestration
- Error propagation
- Graceful shutdown
- Signal handling (SIGINT, SIGTERM)
- Logging integration

**Integration Tests** (3-5 tests):

`test_integration.py`:
- Complete pipeline: Mock API → Parser → Parquet writer
- Error scenarios with rollback
- File output validation (schema, data integrity)
- Multi-batch processing
- Performance under load

### Test Coverage Goals
- **Overall Coverage**: ≥ 80%
- **Critical Path Coverage**: 100% (API → Parse → Write)
- **Error Handling Coverage**: ≥ 90%

### Test Data & Fixtures

**Mock API Responses**:
```python
# Sample JSON response from Rapid7 API
{
  "logs": [
    {"timestamp": "2026-02-10T10:00:00Z", "level": "INFO", "message": "Test"},
    {"timestamp": "2026-02-10T10:00:01Z", "level": "ERROR", "message": "Error"}
  ],
  "next_page": null
}
```

**Sample CSV Structures**:
```csv
timestamp,level,message,host
2026-02-10T10:00:00Z,INFO,Test log,server1
2026-02-10T10:00:01Z,ERROR,Error log,server2
```

**Expected Parquet Schema**:
- timestamp: timestamp[ns]
- level: string
- message: string
- host: string

### Test Execution
- Local: `pytest tests/ -v --cov=src/log_ingestion --cov-report=term-missing`
- CI/CD: Same command in GitHub Actions
- Expected duration: 10-30 seconds

---

## 5. Documentation Impact

### Documentation Updates Required

**Critical Documentation** (Must Complete):

1. **README.md** (+150 lines)
   - Service overview and purpose
   - Installation instructions
   - Configuration guide
   - Usage examples
   - Troubleshooting section

2. **RTM** (`/docs/requirements/rtm.md`) (+200 lines)
   - REQ-004: API authentication
   - REQ-005: Log fetching
   - REQ-006: CSV parsing
   - REQ-007: Parquet writing
   - REQ-008: Configuration management
   - REQ-009: [NFR-SEC] Secure credential handling
   - REQ-010: [NFR-OBS] Structured logging
   - REQ-011: [NFR-PERF] Efficient batching

3. **ADR-0001** (`/docs/arch/adr/0001-log-ingestion-tech-stack.md`) (150 lines)
   - Technology choices (Python, PyArrow, Pandas, etc.)
   - Rationale for each decision
   - Alternatives considered
   - Consequences and trade-offs

4. **Architecture Diagrams** (`/docs/arch/diagrams/log-ingestion.mmd`) (80 lines)
   - System context diagram
   - Component diagram
   - Data flow diagram
   - Deployment diagram

5. **Runbook** (`/docs/runbooks/log-ingestion-service.md`) (200 lines)
   - Service overview
   - Configuration reference
   - Starting/stopping service
   - Monitoring and alerting
   - Common issues and solutions
   - Troubleshooting guide

**Supporting Documentation**:

6. **Configuration Template** (`.env.example`) (15 lines)
   - All required environment variables
   - Example values (non-sensitive)
   - Comments explaining each variable

7. **CHANGELOG.md** (30 lines)
   - Version 0.1.0 entry
   - Initial release notes
   - Feature list

### Documentation Standards
- Use Markdown format for all documents
- Include diagrams using Mermaid.js syntax
- Add code examples with syntax highlighting
- Include troubleshooting sections
- Link between related documents
- Keep documentation in sync with code

---

## 6. Operational Impact

### Deployment Model

**Standalone Service**:
- No dependencies on existing systems
- Can run as one-time script or scheduled job
- Containerization optional (Docker support future enhancement)

**Deployment Options**:
1. **Cron Job**: Scheduled periodic execution
2. **Systemd Service**: Continuous daemon with restarts
3. **Manual Execution**: On-demand log extraction
4. **Container**: Docker/Kubernetes (future)

### Configuration Management

**Environment Variables** (Required):
- `RAPID7_API_KEY` - API authentication key
- `RAPID7_API_ENDPOINT` - Base API URL
- `OUTPUT_DIR` - Directory for Parquet files
- `LOG_LEVEL` - Logging verbosity (default: INFO)

**Environment Variables** (Optional):
- `BATCH_SIZE` - Records per batch (default: 1000)
- `RATE_LIMIT` - Max requests per minute (default: 60)
- `RETRY_ATTEMPTS` - Max retry attempts (default: 3)
- `PARQUET_COMPRESSION` - Compression algorithm (default: snappy)

### Rollback Plan

**Simple Rollback** (< 5 minutes):
1. Stop service process: `kill <PID>` or `systemctl stop log-ingestion`
2. Remove Parquet files if needed: `rm -rf /path/to/output/*`
3. Revert configuration changes
4. No data migrations or schema changes required
5. No impact on other systems

**Risk**: Very Low - Standalone service with no dependencies

### Monitoring & Alerting

**Key Metrics to Monitor**:
- `api_calls_total{status}` - Counter of API calls by status
- `api_call_duration_seconds` - Histogram of API latency
- `logs_fetched_total` - Counter of logs successfully fetched
- `parse_errors_total` - Counter of parse failures
- `parquet_files_written_total` - Counter of files written
- `disk_usage_bytes` - Gauge of output directory size

**Recommended Alerts**:
1. **Critical**: API authentication failures > 3 in 5 minutes
2. **Warning**: Parse error rate > 5% over 15 minutes
3. **Warning**: Disk space < 10% free
4. **Critical**: Service process down
5. **Warning**: No logs fetched in 1 hour (if continuous mode)

**Logging Strategy**:
- Structured JSON logs via structlog
- Log level: INFO (production), DEBUG (development)
- Include trace_id for request correlation
- Log to stdout (container-friendly)

### Support Requirements

**Common Support Issues**:
1. API authentication failures → Check API key validity
2. Network connectivity → Verify API endpoint accessibility
3. Disk space exhaustion → Implement retention policy
4. Parse errors → Review log format changes
5. Performance degradation → Adjust batch sizes

**Troubleshooting Resources**:
- Runbook with step-by-step guides
- Structured logs for debugging
- Health check for service status

---

## 7. Risk Assessment

### Overall Risk Level
**MEDIUM** - Acceptable with mitigations in place

### Risk Matrix

| Risk ID | Risk | Probability | Impact | Score | Mitigation |
|---------|------|-------------|--------|-------|------------|
| R1 | API rate limiting blocks ingestion | Medium | High | 6/9 | Exponential backoff, configurable delays, monitoring |
| R2 | Log schema changes break parser | Medium | Medium | 4/9 | Dynamic schema detection, graceful errors, alerting |
| R3 | Disk space exhaustion | Low | High | 3/9 | Monitoring, retention policy, file rotation |
| R4 | API credentials exposure | Low | Critical | 3/9 | Environment variables, .gitignore, access controls |
| R5 | Memory leaks under sustained load | Low | Medium | 2/9 | Memory profiling, batch processing, testing |
| R6 | API endpoint changes | Low | Medium | 2/9 | Version API endpoints, change monitoring |

### Risk Mitigation Details

**R1: API Rate Limiting**
- **Mitigation**: 
  - Exponential backoff: 1s → 2s → 4s → 8s
  - Configurable rate limit (default: 60 req/min)
  - Respect Retry-After headers
  - Monitor 429 responses
- **Contingency**: Reduce batch size, increase delay between calls

**R2: Log Schema Changes**
- **Mitigation**:
  - Dynamic schema detection from CSV headers
  - Schema version tracking in logs
  - Graceful handling of unknown fields
  - Alert on schema changes
- **Contingency**: Update parser logic, manual schema mapping

**R3: Disk Space Exhaustion**
- **Mitigation**:
  - Disk space monitoring with alerts
  - Configurable retention policy
  - File rotation by date
  - Compression enabled by default
- **Contingency**: Archive old files to cold storage, expand disk

**R4: API Credentials Exposure**
- **Mitigation**:
  - Environment variables only (no code)
  - .gitignore excludes .env file
  - File permissions on .env (600)
  - Regular credential rotation
  - No credentials in logs
- **Contingency**: Rotate credentials immediately, audit access

### Acceptable Risk Threshold
**Maximum Acceptable Risk Score**: 6/9

**Current Status**: Within acceptable limits
- Highest risk: R1 (score 6/9) - Mitigated
- All risks have documented mitigations
- Contingency plans in place

---

## 8. Blast Radius Summary

### Impact Scope

**Affected Systems**: None (new standalone service)

**Affected Users**: 
- Analytics team (new capability to query logs)
- Operations team (new service to manage)

**Affected Teams**:
- Development: Implementation and testing
- Operations: Deployment and monitoring
- Security: Credential management and auditing

**Impact Duration**: 0 (no downtime of existing systems)

**Reversibility**: **Easy**
- Stop service process
- Remove output files
- Revert configuration
- No data migrations needed
- No schema changes to existing systems

### Blast Radius Classification

**Size**: SMALL

**Justification**:
- ✅ New standalone service (no integration points)
- ✅ No dependencies on existing systems
- ✅ No modifications to existing code
- ✅ Easily reversible (stop and delete)
- ✅ Low risk to production environment
- ✅ Independent deployment

**Dependencies**:
- External: Rapid7 InsightOps API (vendor service)
- Internal: None

**Failure Impact**:
- Service failure: Analytics delayed, no impact on production systems
- Data loss: Re-fetch from API (logs retained at source)
- Worst case: Stop service, no cascading failures

---

## Summary

### Overall Assessment

| Category | Assessment | Status |
|----------|-----------|--------|
| Code Impact | Medium complexity, 23 files | ✅ Manageable |
| Security | Medium risk, mitigations in place | ✅ Approved |
| Performance | Positive, new capability | ✅ Good |
| Testing | Comprehensive TDD strategy | ✅ Planned |
| Documentation | Complete documentation plan | ✅ In Progress |
| Operations | Low operational burden | ✅ Good |
| Risk | Medium, within acceptable limits | ✅ Acceptable |
| Blast Radius | Small, easily reversible | ✅ Low Impact |

### Recommendation

**PROCEED WITH IMPLEMENTATION**

The impact assessment shows this change is:
- Low risk to existing systems
- Well-planned with comprehensive testing
- Properly documented
- Security-reviewed and approved
- Performance-positive
- Easily reversible if needed

All stakeholders have approved. Development team has ATP (Approved to Proceed).

---

**Impact Assessment Completed**: 2026-02-10  
**Assessed By**: Development Team  
**Reviewed By**: Tech Lead, Security Team  
**Status**: APPROVED
