# Requirement Traceability Matrix (RTM)

> **Version:** 1.1.0  
> **Last Updated:** 2026-02-10  
> **Status:** ACTIVE

This document is the **single source of truth** for all system requirements. Every feature, function, and capability must trace back to a requirement defined in this matrix.

---

## Requirement Format

**REQ-ID**: `REQ-NNN` (sequential numbering, zero-padded to 3 digits)

**Category Prefixes**:
- `[FUNC]` - Functional requirement
- `[NFR-PERF]` - Non-functional: Performance
- `[NFR-SEC]` - Non-functional: Security
- `[NFR-REL]` - Non-functional: Reliability
- `[NFR-SCALE]` - Non-functional: Scalability
- `[NFR-MAINT]` - Non-functional: Maintainability
- `[NFR-OBS]` - Non-functional: Observability

**Status Values**:
- `PROPOSED` - Requirement identified but not yet approved
- `APPROVED` - Requirement approved for implementation
- `IN_PROGRESS` - Currently being implemented
- `IMPLEMENTED` - Code written and committed
- `TESTED` - Tests written and passing
- `DEPLOYED` - Available in production
- `DEPRECATED` - No longer applicable

---

## Requirements Matrix

| REQ-ID | Category | Description | Status | Priority | Implemented In | Test Coverage | ADR Link | Date Added |
|--------|----------|-------------|--------|----------|----------------|---------------|----------|------------|
| REQ-001 | [FUNC] | Example: System shall parse log files | PROPOSED | P2 | - | - | - | 2026-02-09 |
| REQ-002 | [NFR-PERF] | Example: Parsing shall complete < 100ms for files < 1MB | PROPOSED | P2 | - | - | - | 2026-02-09 |
| REQ-003 | [NFR-SEC] | Example: Input paths validated for directory traversal | PROPOSED | P1 | - | - | - | 2026-02-09 |
| REQ-004 | [FUNC] | Service shall authenticate with Rapid7 InsightOps API | APPROVED | P1 | - | - | ADR-0001 | 2026-02-10 |
| REQ-005 | [FUNC] | Service shall fetch logs via API with configurable endpoints | APPROVED | P1 | - | - | ADR-0001 | 2026-02-10 |
| REQ-006 | [FUNC] | Service shall parse CSV-formatted log structure dynamically | APPROVED | P1 | - | - | ADR-0001 | 2026-02-10 |
| REQ-007 | [FUNC] | Service shall write logs to Apache Parquet format | APPROVED | P1 | - | - | ADR-0001 | 2026-02-10 |
| REQ-008 | [FUNC] | Service shall support configuration via environment variables | APPROVED | P2 | - | - | ADR-0001 | 2026-02-10 |
| REQ-009 | [NFR-SEC] | API credentials shall be stored in environment variables only | APPROVED | P0 | - | - | ADR-0001 | 2026-02-10 |
| REQ-010 | [NFR-OBS] | Service shall emit structured JSON logs with trace context | APPROVED | P2 | - | - | ADR-0001 | 2026-02-10 |
| REQ-011 | [NFR-PERF] | Service shall process logs efficiently using batching | APPROVED | P2 | - | - | ADR-0001 | 2026-02-10 |
| REQ-012 | [FUNC] | Service shall authenticate to Rapid7 Log Search API using `x-api-key` header | TESTED | P1 | `/src/log_ingestion/api_client.py` | `/tests/test_api_client.py` | ADR-0001 | 2026-02-10 |
| REQ-013 | [FUNC] | Service shall poll Log Search queries to completion via `links[rel=Self]` with bounded exponential backoff | TESTED | P1 | `/src/log_ingestion/api_client.py` | `/tests/test_api_client.py` | ADR-0001 | 2026-02-10 |
| REQ-014 | [FUNC] | Service shall retrieve all pages of Log Search results via `links[rel=Next]` | TESTED | P1 | `/src/log_ingestion/api_client.py` | `/tests/test_api_client.py` | ADR-0001 | 2026-02-10 |
| REQ-015 | [NFR-REL] | Service shall handle HTTP 429 using `X-RateLimit-Reset` and retry without silent failure | TESTED | P1 | `/src/log_ingestion/api_client.py` | `/tests/test_api_client.py` | ADR-0001 | 2026-02-10 |
| REQ-016 | [FUNC] | Utility shall list available Log Search log sets for the configured region | TESTED | P2 | `/src/log_ingestion/api_client.py:Rapid7ApiClient.list_log_sets()` | `/tests/test_api_client_list_log_sets_embedded_logs_info.py` | ADR-0001 | 2026-02-10 |
| REQ-017 | [FUNC] | Utility shall allow user to select a log set (by index or id) and then list logs within the selected log set using embedded `logs_info` from the logsets list response | TESTED | P2 | `/src/log_ingestion/main.py:_run_log_selection()`, `/src/log_ingestion/log_selection.py`, `/src/log_ingestion/api_client.py:Rapid7ApiClient.list_log_sets()` | `/tests/test_log_selection.py`, `/tests/test_main_select_log.py`, `/tests/test_api_client_list_log_sets_embedded_logs_info.py` | ADR-0001 | 2026-02-10 |
| REQ-018 | [FUNC] | Utility shall persist selected log id to `.env` as `RAPID7_LOG_KEY` without logging secrets | TESTED | P2 | `/src/log_ingestion/main.py`, `/src/log_ingestion/env_utils.py` | `/tests/test_env_utils.py`, `/tests/test_main_select_log.py` | ADR-0001 | 2026-02-10 |
| REQ-019 | [NFR-REL] | Utility shall not call per-logset membership endpoints in environments where log membership is provided inline via `logs_info`, and shall fail loudly with actionable guidance when embedded membership is missing | TESTED | P1 | `/src/log_ingestion/main.py:_run_log_selection()`, `/src/log_ingestion/api_client.py:Rapid7ApiClient.list_logs_in_log_set()` | `/tests/test_main_select_log.py`, `/tests/test_api_client_list_logs_in_log_set_fallback_404.py` | ADR-0001 | 2026-02-10 |
| REQ-020 | [FUNC] | CLI shall support module execution via `python -m src.log_ingestion.main ...` without import errors; direct script execution shall fail loudly with actionable guidance | APPROVED | P1 | `/src/log_ingestion/main.py` | `/tests/test_main_module_execution_guard.py` | ADR-0001 | 2026-02-11 |
| REQ-021 | [FUNC] | Service shall default `OUTPUT_DIR` to a writable path when not provided, and allow override via `OUTPUT_DIR` | APPROVED | P1 | `/src/log_ingestion/config.py`, `/src/log_ingestion/parquet_writer.py` | `/tests/test_config.py`, `/tests/test_parquet_writer.py` | ADR-0001 | 2026-02-11 |
| REQ-022 | [NFR-REL] | Service shall fail loudly with an actionable error when output directory is not writable/creatable | APPROVED | P1 | `/src/log_ingestion/parquet_writer.py` | `/tests/test_parquet_writer.py` | ADR-0001 | 2026-02-11 |

---

## Requirements by Category

### Functional Requirements (FUNC)

| REQ-ID | Description | Status | Implementation |
|--------|-------------|--------|----------------|
| REQ-001 | Example functional requirement | PROPOSED | - |

### Non-Functional Requirements (NFR)

#### Performance (NFR-PERF)

| REQ-ID | Description | Target Metric | Status |
|--------|-------------|---------------|--------|
| REQ-002 | Example performance requirement | < 100ms | PROPOSED |

#### Security (NFR-SEC)

| REQ-ID | Description | Status | Implementation |
|--------|-------------|--------|----------------|
| REQ-003 | Example security requirement | PROPOSED | - |

#### Reliability (NFR-REL)

| REQ-ID | Description | Target Metric | Status |
|--------|-------------|---------------|--------|
| - | No requirements defined yet | - | - |

#### Scalability (NFR-SCALE)

| REQ-ID | Description | Target Metric | Status |
|--------|-------------|---------------|--------|
| - | No requirements defined yet | - | - |

#### Maintainability (NFR-MAINT)

| REQ-ID | Description | Status | Implementation |
|--------|-------------|--------|----------------|
| - | No requirements defined yet | - | - |

#### Observability (NFR-OBS)

| REQ-ID | Description | Status | Implementation |
|--------|-------------|--------|----------------|
| - | No requirements defined yet | - | - |

---

## Requirement Details

### REQ-001: Example Functional Requirement
**Category**: [FUNC]  
**Priority**: P2  
**Status**: PROPOSED  
**Date Added**: 2026-02-09

**Description**:  
System shall parse log files in various standard formats (Apache Common Log Format, NGINX, etc.)

**Acceptance Criteria**:
- [ ] Parser correctly identifies log format
- [ ] Parser extracts all relevant fields
- [ ] Parser handles malformed entries gracefully
- [ ] Parser performance meets NFR-PERF requirements

**Related Requirements**:
- REQ-002 (Performance constraint)
- REQ-003 (Security constraint)

**Implemented In**:
- File: TBD
- Function/Class: TBD

**Test Coverage**:
- Test File: TBD
- Test Cases: TBD
- Coverage: TBD%

**ADR Link**: TBD

---

### REQ-002: Example Performance Requirement
**Category**: [NFR-PERF]  
**Priority**: P2  
**Status**: PROPOSED  
**Date Added**: 2026-02-09

**Description**:  
Log file parsing shall complete within 100 milliseconds for files under 1MB in size.

**Measurement**:
- Metric: P95 latency
- Tool: Performance benchmarks in test suite
- Baseline: TBD
- Target: < 100ms

**Related Requirements**:
- REQ-001 (Functional requirement this constrains)

**SLO Reference**: `/docs/requirements/slos.md#parsing-performance`

---

### REQ-003: Example Security Requirement
**Category**: [NFR-SEC]  
**Priority**: P1  
**Status**: PROPOSED  
**Date Added**: 2026-02-09

**Description**:  
All file path inputs must be validated to prevent directory traversal attacks.

**Security Controls**:
- [ ] Path canonicalization
- [ ] Allowlist validation
- [ ] Deny list for dangerous patterns (../, etc.)
- [ ] Logging of validation failures

**Related Requirements**:
- REQ-001 (Functional requirement this secures)

**Threat Model**: TBD  
**Mitigation**: TBD

---

### REQ-004: Rapid7 API Authentication
**Category**: [FUNC]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall authenticate with the Rapid7 InsightOps API using API key authentication. The service must construct proper authentication headers and handle authentication failures gracefully.

**Acceptance Criteria**:
- [ ] API client constructs correct Authorization header format
- [ ] API client includes API key from environment variable
- [ ] Service handles 401 Unauthorized responses appropriately
- [ ] Service handles 403 Forbidden responses appropriately
- [ ] Authentication failures are logged with appropriate error details
- [ ] No API keys hardcoded in source code

**Related Requirements**:
- REQ-009 (Security requirement for credential storage)
- REQ-005 (Functional requirement for API access)

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`
- Class: `Rapid7ApiClient.__init__()`, `Rapid7ApiClient.fetch_logs()`

**Test Coverage**:
- Test File: `/tests/test_api_client.py`
- Test Cases: 
  - `test_api_client_constructs_auth_header()`
  - `test_api_client_handles_401_unauthorized()`
  - `test_api_client_handles_403_forbidden()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-005: Fetch Logs via API
**Category**: [FUNC]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall fetch logs from the Rapid7 InsightOps API with configurable endpoints. The service must support pagination, handle API errors, and implement retry logic with exponential backoff for transient failures.

**Acceptance Criteria**:
- [ ] Service successfully fetches logs from API
- [ ] API endpoint is configurable via environment variable
- [ ] Service handles pagination if API returns paged results
- [ ] Service implements retry logic for transient failures (5xx errors, timeouts)
- [ ] Service implements exponential backoff between retries
- [ ] Service respects API rate limits (429 responses)
- [ ] Service handles network connectivity errors gracefully
- [ ] All API requests are logged with request/response details

**Parameters**:
- `start_time`: Start of time range for logs (ISO 8601 format)
- `end_time`: End of time range for logs (ISO 8601 format)
- `batch_size`: Number of log entries to fetch per request (configurable)

**Related Requirements**:
- REQ-004 (Authentication dependency)
- REQ-011 (Performance requirement for efficiency)

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`
- Class: `Rapid7ApiClient`
- Method: `fetch_logs(start_time, end_time)`

**Test Coverage**:
- Test File: `/tests/test_api_client.py`
- Test Cases:
  - `test_api_client_fetches_logs_successfully()`
  - `test_api_client_handles_429_rate_limit()`
  - `test_api_client_handles_500_server_error()`
  - `test_api_client_timeout_handling()`
  - `test_api_client_respects_rate_limiting()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-006: Dynamic CSV Schema Detection
**Category**: [FUNC]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall parse CSV-formatted log data with dynamic schema detection. The schema can be provided in two ways: as CSV headers in the first row, or as a separate schema definition provided at runtime. The parser must infer data types automatically and handle malformed data gracefully.

**Acceptance Criteria**:
- [ ] Parser detects schema from CSV headers (first row)
- [ ] Parser accepts schema definition provided at runtime
- [ ] Parser infers data types (string, integer, float, timestamp, boolean)
- [ ] Parser handles missing values appropriately
- [ ] Parser handles malformed CSV data gracefully (logs errors, continues processing)
- [ ] Parser handles special characters and quoted fields correctly
- [ ] Parser validates data against detected schema
- [ ] Schema is cached for reuse across batches

**Supported Data Types**:
- String (default)
- Integer (int64)
- Float (float64)
- Timestamp (datetime64[ns])
- Boolean (bool)

**Related Requirements**:
- REQ-007 (Parquet writer depends on parsed schema)
- REQ-010 (Observability requirement for parse errors)

**Implemented In**:
- File: `/src/log_ingestion/parser.py`
- Class: `LogParser`
- Methods: `detect_schema()`, `parse()`

**Test Coverage**:
- Test File: `/tests/test_parser.py`
- Test Cases:
  - `test_parser_detects_schema_from_headers()`
  - `test_parser_detects_schema_from_first_row()`
  - `test_parser_parses_data_correctly()`
  - `test_parser_handles_malformed_csv()`
  - `test_parser_handles_empty_data()`
  - `test_parser_infers_data_types()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-007: Parquet File Writing
**Category**: [FUNC]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall write parsed log data to Apache Parquet files with compression. Files shall be partitioned by date/time for efficient querying. The Parquet writer must validate files after writing to ensure data integrity.

**Acceptance Criteria**:
- [ ] Writer creates valid Apache Parquet files
- [ ] Writer applies compression (Snappy by default, configurable)
- [ ] Writer partitions files by date (e.g., `/data/logs/2026/02/10/logs_hour.parquet`)
- [ ] Writer supports batch writing for efficiency
- [ ] Writer validates written files are readable
- [ ] Writer reports compression ratio
- [ ] Files can be read by standard Parquet tools (Pandas, Spark, DuckDB)
- [ ] Schema is preserved in Parquet metadata

**Output Format**:
- File naming: `logs_{date}_{hour}.parquet`
- Partitioning: `YYYY/MM/DD/`
- Compression: Snappy (default), GZIP, Brotli (configurable)
- Schema: Preserved from parsed data

**Performance Targets**:
- Write speed: > 5,000 entries/second
- Compression ratio: > 70% vs raw JSON
- File validation: < 100ms per file

**Related Requirements**:
- REQ-006 (Parser provides data to write)
- REQ-011 (Performance requirement for efficiency)

**Implemented In**:
- File: `/src/log_ingestion/parquet_writer.py`
- Class: `ParquetWriter`
- Methods: `write(dataframe, partition_date)`

**Test Coverage**:
- Test File: `/tests/test_parquet_writer.py`
- Test Cases:
  - `test_writer_creates_parquet_schema()`
  - `test_writer_writes_single_batch()`
  - `test_writer_writes_multiple_batches()`
  - `test_writer_partitions_by_date()`
  - `test_writer_applies_compression()`
  - `test_writer_validates_output_file()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-008: Configuration Management
**Category**: [FUNC]  
**Priority**: P2  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall support configuration via environment variables following the 12-factor app methodology. Configuration must include validation with clear error messages for misconfiguration. Both required and optional parameters with sensible defaults shall be supported.

**Acceptance Criteria**:
- [ ] All required configuration parameters are loaded from environment variables
- [ ] Optional parameters have documented default values
- [ ] Configuration validation occurs at startup
- [ ] Validation errors include clear, actionable error messages
- [ ] Configuration can be loaded from `.env` file (development)
- [ ] Configuration can be loaded from system environment (production)
- [ ] Configuration object is type-safe (Pydantic models)
- [ ] IDE autocomplete works for configuration fields

**Required Configuration**:
- `RAPID7_API_KEY`: API authentication key
- `RAPID7_API_ENDPOINT`: Base API URL
- `OUTPUT_DIR`: Directory for Parquet files

**Optional Configuration** (with defaults):
- `LOG_LEVEL`: `INFO` (DEBUG, INFO, WARNING, ERROR)
- `BATCH_SIZE`: `1000` (100-10000)
- `RATE_LIMIT`: `60` (requests per minute)
- `RETRY_ATTEMPTS`: `3` (1-10)
- `PARQUET_COMPRESSION`: `snappy` (snappy, gzip, brotli, none)

**Related Requirements**:
- REQ-009 (Security requirement for credential handling)

**Implemented In**:
- File: `/src/log_ingestion/config.py`
- Class: `LogIngestionConfig`

**Test Coverage**:
- Test File: `/tests/test_config.py`
- Test Cases:
  - `test_config_loads_from_environment()`
  - `test_config_validates_required_fields()`
  - `test_config_uses_default_values()`
  - `test_config_validates_api_endpoint_format()`
  - `test_config_validates_output_dir_exists()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-009: Secure Credential Storage
**Category**: [NFR-SEC]  
**Priority**: P0 (CRITICAL)  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
API credentials and other secrets shall NEVER be hardcoded in source code. All credentials must be stored in environment variables or a secure secret management system. The `.env` file containing credentials must be excluded from version control.

**Acceptance Criteria**:
- [ ] No API keys or credentials in source code
- [ ] No API keys or credentials in configuration files committed to git
- [ ] `.env` file is excluded via `.gitignore`
- [ ] `.env.example` template provided (with no real secrets)
- [ ] Credentials loaded from environment variables at runtime
- [ ] Credentials not logged or exposed in error messages
- [ ] File permissions on `.env` are restrictive (600 or 400)
- [ ] Security scan passes with zero hardcoded secrets

**Security Controls**:
- [x] Environment variable storage for all secrets
- [x] `.gitignore` includes `.env`
- [x] Code review checklist includes secret scanning
- [ ] Automated secret detection in CI/CD (git-secrets, bandit)
- [ ] Credential rotation procedure documented

**Threat Model**:
- **Threat**: Credentials committed to git repository
  - **Mitigation**: `.gitignore`, pre-commit hooks, code review
- **Threat**: Credentials exposed in logs
  - **Mitigation**: Sanitize all log output, never log credential values
- **Threat**: Credentials in error messages
  - **Mitigation**: Generic error messages, credential redaction

**Related Requirements**:
- REQ-004 (Functional requirement for API authentication)
- REQ-008 (Functional requirement for configuration)

**Implemented In**:
- File: All source files
- Enforcement: Code review, security scanning, CI/CD checks

**Test Coverage**:
- Test File: Security audit, bandit scan
- Test Cases: Automated secret detection
- Coverage: 100% (all files scanned)

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

**Compliance**: GDPR, SOC2, PCI-DSS

---

### REQ-010: Structured Logging with Trace Context
**Category**: [NFR-OBS]  
**Priority**: P2  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall emit structured JSON logs with trace context for observability. All log events must include standard fields (timestamp, level, service, version) and context fields (trace_id, request_id) for correlation. Logs should be parseable by standard log aggregation systems.

**Acceptance Criteria**:
- [ ] All logs emitted in JSON format
- [ ] Standard fields present in all logs (timestamp, level, event, service, version)
- [ ] Trace context included (trace_id for request correlation)
- [ ] Log levels used appropriately (DEBUG, INFO, WARNING, ERROR)
- [ ] Structured fields for important data (not just message strings)
- [ ] No sensitive data (credentials, PII) in logs
- [ ] Logs written to stdout (container-friendly)
- [ ] Log format compatible with ELK, Splunk, CloudWatch

**Standard Log Fields**:
```json
{
  "timestamp": "2026-02-10T10:00:00Z",
  "level": "INFO",
  "service": "log-ingestion",
  "version": "0.1.0",
  "environment": "production",
  "trace_id": "abc123",
  "event": "event_name",
  "context": {"key": "value"}
}
```

**Key Log Events**:
- `service_started`, `config_loaded`, `api_request`, `api_response`
- `logs_fetched`, `parse_start`, `parse_complete`
- `file_write_start`, `file_write_complete`
- `batch_complete`, `error`

**Related Requirements**:
- REQ-009 (Security requirement - no credentials in logs)

**Implemented In**:
- File: All source files
- Library: `structlog`
- Configuration: `/src/log_ingestion/main.py`

**Test Coverage**:
- Test File: `/tests/test_main.py`, integration tests
- Test Cases: Verify log output format and content
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

**Monitoring**: Logs ingested into ELK/Splunk for alerting

---

### REQ-011: Service Shall Process Logs Efficiently Using Batching
**Category**: [NFR-PERF]  
**Priority**: P2  
**Status**: APPROVED  
**Date Added**: 2026-02-10

**Description**:  
Service shall process logs efficiently using batching to achieve target throughput of 1,000-10,000 log entries per minute. Memory usage must remain under 500 MB under normal load. Batch size must be configurable to balance memory usage and throughput.

**Acceptance Criteria**:
- [ ] Throughput: Process 1,000-10,000 entries per minute
- [ ] Memory: Peak memory usage < 500 MB under normal load
- [ ] Batch size configurable via environment variable
- [ ] Efficient CSV parsing (leverage pandas chunking)
- [ ] Efficient Parquet writing (use PyArrow batch writing)
- [ ] No memory leaks under sustained operation
- [ ] Resource usage scales linearly with batch size

**Performance Targets**:
- Parse rate: > 10,000 entries/second
- Write rate: > 5,000 entries/second
- API call latency: < 5 seconds (P95)
- End-to-end latency: < 100ms per 1000 entries
- Memory per batch: < 50 MB

**Measurement**:
- Tool: Performance benchmarks in test suite
- Metrics: Throughput, latency, memory usage
- Profiling: Memory profiling for leak detection

**Related Requirements**:
- REQ-005 (Functional requirement for API fetching)
- REQ-006 (Functional requirement for parsing)
- REQ-007 (Functional requirement for writing)

**Implemented In**:
- File: `/src/log_ingestion/main.py` (orchestration)
- File: `/src/log_ingestion/parser.py` (batch parsing)
- File: `/src/log_ingestion/parquet_writer.py` (batch writing)

**Test Coverage**:
- Test File: `/tests/benchmark.py`
- Test Cases: Performance benchmarks
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

**SLO Reference**: `/docs/requirements/slos.md#log-ingestion-performance`

---

### REQ-012: Rapid7 Log Search API Authentication
**Category**: [FUNC]  
**Priority**: P1  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Service shall authenticate to the Rapid7 Log Search API using the `x-api-key` request header.

**Acceptance Criteria**:
- [ ] `x-api-key` header is set on all Log Search requests
- [ ] No API keys are hardcoded
- [ ] Authentication failures are logged and raised

**Related Requirements**:
- REQ-009

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`

**Test Coverage**:
- File: `/tests/test_api_client.py`

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-013: Poll Log Search Query to Completion
**Category**: [FUNC]  
**Priority**: P1  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Service shall poll Log Search query continuations until completion when the response contains `links` with `rel=Self`.

**Acceptance Criteria**:
- [ ] Client detects “in progress” responses via `links[rel=Self]`
- [ ] Client polls the `Self` URL until completion
- [ ] Poll delay uses bounded exponential backoff (starts small, caps at a maximum)
- [ ] Invalid link shapes fail loudly with a descriptive error

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`

**Test Coverage**:
- File: `/tests/test_api_client.py`

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-014: Link-based Pagination for Log Search Results
**Category**: [FUNC]  
**Priority**: P1  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Service shall retrieve all pages of Log Search results by following `links[rel=Next]` until no next page exists.

**Acceptance Criteria**:
- [ ] Client detects next pages via `links[rel=Next]`
- [ ] Client requests the next page URL and polls to completion when needed
- [ ] Client returns a complete aggregated result set

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`

**Test Coverage**:
- File: `/tests/test_api_client.py`

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-015: Rate Limit Reset Handling for Log Search
**Category**: [NFR-REL]  
**Priority**: P1  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Service shall handle HTTP 429 rate limiting by honoring the `X-RateLimit-Reset` header (seconds until reset) and retrying.

**Acceptance Criteria**:
- [ ] On 429, client reads `X-RateLimit-Reset` as an integer seconds value
- [ ] Client logs rate limiting and sleeps for the specified duration
- [ ] Client retries and either succeeds or fails loudly after bounded attempts

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`

**Test Coverage**:
- File: `/tests/test_api_client.py`

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-016: List Available Log Sets
**Category**: [FUNC]  
**Priority**: P2  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Utility shall list available Log Search log sets for the configured region. This feature is read-only and does not modify any state.

**Acceptance Criteria**:
- [ ] Client can list log sets for the configured region
- [ ] Output includes log set ID, name, and description
- [ ] No sensitive data is exposed in log set details
- [ ] Results are paginated if there are many log sets

**Related Requirements**:
- REQ-004 (Authentication dependency)

**Implemented In**:
- File: `/src/log_ingestion/api_client.py`
- Function: `list_log_sets()`

**Test Coverage**:
- Test File: `/tests/test_api_client.py`
- Test Cases:
  - `test_list_log_sets_success()`
  - `test_list_log_sets_pagination()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-017: Select Log Set and List Logs
**Category**: [FUNC]  
**Priority**: P2  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Utility shall allow user to select a log set (by index or id) and then list logs within the selected log set using embedded `logs_info` from the logsets list response. This feature enables targeting specific logs for ingestion.

**Acceptance Criteria**:
- [ ] User can select a log set by index or ID
- [ ] System remembers the selected log set for the session
- [ ] User can list logs within the selected log set
- [ ] Log listing shows log ID, name, and metadata
- [ ] No sensitive data is exposed in log details

**Related Requirements**:
- REQ-004 (Authentication dependency)
- REQ-016 (Log set listing)

**Implemented In**:
- File: `/src/log_ingestion/main.py`, `/src/log_ingestion/log_selection.py`, `/src/log_ingestion/api_client.py`
- Function: `select_log_set()`, `list_logs_in_selected_set()`

**Test Coverage**:
- Test File: `/tests/test_log_selection.py`, `/tests/test_api_client.py`
- Test Cases:
  - `test_select_log_set_by_index()`
  - `test_select_log_set_by_id()`
  - `test_list_logs_in_selected_set()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-018: Persist Selected Log ID
**Category**: [FUNC]  
**Priority**: P2  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Utility shall persist selected log id to `.env` as `RAPID7_LOG_KEY` without logging secrets. This ensures the selected log set is used for subsequent ingestion runs.

**Acceptance Criteria**:
- [ ] Selected log ID is saved to `.env` as `RAPID7_LOG_KEY`
- [ ] No sensitive data is logged during this process
- [ ] Existing comments and formatting in `.env` are preserved
- [ ] Changes to `.env` are detected and applied without restart

**Related Requirements**:
- REQ-009 (Security requirement - no credentials in logs)
- REQ-017 (Log set selection)

**Implemented In**:
- File: `/src/log_ingestion/main.py`, `/src/log_ingestion/env_utils.py`
- Function: `persist_selected_log_id()`

**Test Coverage**:
- Test File: `/tests/test_env_utils.py`
- Test Cases:
  - `test_persist_selected_log_id()`
  - `test_log_id_persistence_across_sessions()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-019: Inline Log Membership Requirement
**Category**: [NFR-REL]  
**Priority**: P1  
**Status**: TESTED  
**Date Added**: 2026-02-10

**Description**:  
Utility shall not call per-logset membership endpoints in environments where log membership is provided inline via `logs_info`, and shall fail loudly with actionable guidance when embedded membership is missing.

**Acceptance Criteria**:
- [ ] In unsupported environments, log set selection does not call membership endpoints
- [ ] System fails with clear error message if `logs_info` is missing
- [ ] Documentation is updated to reflect environment compatibility requirements

**Related Requirements**:
- REQ-017 (Log set selection)

**Implemented In**:
- File: `/src/log_ingestion/main.py`, `/src/log_ingestion/api_client.py`
- Function: `_run_log_selection()`, `list_logs_in_log_set()`

**Test Coverage**:
- Test File: `/tests/test_main_select_log.py`, `/tests/test_api_client_list_logs_in_log_set_fallback_404.py`
- Test Cases:
  - `test_log_set_selection_unsupported_env()`
  - `test_log_set_selection_supported_env()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-020: Module Execution Guard
**Category**: [FUNC]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-11

**Description**:  
CLI shall support module execution via `python -m src.log_ingestion.main ...` without import errors; direct script execution shall fail loudly with actionable guidance.

**Acceptance Criteria**:
- [ ] Module can be executed as `python -m src.log_ingestion.main`
- [ ] Direct execution of the script file fails with an error message
- [ ] No import errors when executing as a module
- [ ] Documentation updated with module execution instructions

**Related Requirements**:
- REQ-004 (Authentication dependency)

**Implemented In**:
- File: `/src/log_ingestion/main.py`

**Test Coverage**:
- Test File: `/tests/test_main_module_execution_guard.py`
- Test Cases:
  - `test_module_execution_via_python_m()`
  - `test_direct_script_execution_fails()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-021: Default Writable Output Directory
**Category**: [FUNC]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-11

**Description**:  
Service shall default `OUTPUT_DIR` to a writable path when not provided, and allow override via `OUTPUT_DIR`.

**Acceptance Criteria**:
- [ ] Default `OUTPUT_DIR` is set to a writable path
- [ ] Service starts successfully with default configuration
- [ ] `OUTPUT_DIR` can be overridden by setting the environment variable
- [ ] Documentation updated with configuration details

**Related Requirements**:
- REQ-008 (Configuration management)

**Implemented In**:
- File: `/src/log_ingestion/config.py`, `/src/log_ingestion/parquet_writer.py`

**Test Coverage**:
- Test File: `/tests/test_config.py`, `/tests/test_parquet_writer.py`
- Test Cases:
  - `test_default_output_dir_is_writable()`
  - `test_output_dir_can_be_overridden()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

### REQ-022: Output Directory Writeability Check
**Category**: [NFR-REL]  
**Priority**: P1  
**Status**: APPROVED  
**Date Added**: 2026-02-11

**Description**:  
Service shall fail loudly with an actionable error when output directory is not writable/creatable.

**Acceptance Criteria**:
- [ ] On startup, service checks if `OUTPUT_DIR` is writable
- [ ] If not writable, service fails with an error message
- [ ] Error message includes guidance on correcting the issue
- [ ] No partial or corrupted data writes occur

**Related Requirements**:
- REQ-021 (Default writable output directory)

**Implemented In**:
- File: `/src/log_ingestion/parquet_writer.py`

**Test Coverage**:
- Test File: `/tests/test_parquet_writer.py`
- Test Cases:
  - `test_output_directory_writeability_check()`
  - `test_service_fails_with_actionable_error()`
- Coverage: TBD%

**ADR Link**: [ADR-0001](/docs/arch/adr/0001-log-ingestion-tech-stack.md)

---

## Traceability Views

### By Status

#### PROPOSED
- REQ-001, REQ-002, REQ-003

#### APPROVED
- REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-020, REQ-021, REQ-022

#### IN_PROGRESS
- (None yet)

#### IMPLEMENTED
- (None yet)

#### TESTED
- REQ-012, REQ-013, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019

#### DEPLOYED
- (None yet)

#### DEPRECATED
- (None yet)

---

### By Priority

#### P0 - CRITICAL
- REQ-009

#### P1 - HIGH
- REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-020, REQ-021, REQ-022

#### P2 - MEDIUM
- REQ-001, REQ-002, REQ-008, REQ-010, REQ-011, REQ-016, REQ-017, REQ-018

#### P3 - LOW
- (None yet)

---

## Change History

| Date | REQ-IDs | Change Description | Changed By | CR Reference |
|------|---------|-------------------|------------|--------------|
| 2026-02-09 | REQ-001, REQ-002, REQ-003 | Initial example requirements | System | - |
| 2026-02-10 | REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011 | Log ingestion service requirements | Development Team | CR-2026-02-10-001 |
| 2026-02-10 | REQ-012, REQ-013, REQ-014, REQ-015 | Log Search API requirements | Development Team | CR-2026-02-10-002 |
| 2026-02-10 | REQ-016, REQ-017, REQ-018, REQ-019 | Log set selection and persistence requirements | Development Team | CR-2026-02-10-003 |
| 2026-02-10 | REQ-016, REQ-017, REQ-018, REQ-019 | Mark log set selection requirements as TESTED and update trace links for embedded `logs_info` selection flow | Development Team | CR-2026-02-10-006 |
| 2026-02-11 | REQ-020, REQ-021, REQ-022 | Module execution and output directory requirements | Development Team | CR-2026-02-11-001 |

---

## Guidelines for Updating RTM

### When to Add Requirements

1. **New Feature Request**: Break down into atomic requirements
2. **Bug Discovery**: If bug reveals missing requirement, add it
3. **NFR Identification**: When performance/security/reliability needs are defined
4. **Architectural Change**: When structure changes necessitate new requirements

### How to Add Requirements

1. Assign next available REQ-ID (sequential)
2. Choose appropriate category
3. Write clear, testable description
4. Set priority (P0-P3)
5. Set initial status (usually PROPOSED)
6. Add to main matrix table
7. Create detailed section below
8. Update change history

### How to Update Requirements

1. Change status as work progresses
2. Add implementation details when code is written
3. Add test coverage information when tests are written
4. Link to ADRs when architectural decisions are made
5. Update change history with each modification

### Requirement Lifecycle

```mermaid
graph LR
    A[PROPOSED] --> B[APPROVED]
    B --> C[IN_PROGRESS]
    C --> D[IMPLEMENTED]
    D --> E[TESTED]
    E --> F[DEPLOYED]
    F --> G[DEPRECATED]
    
    A -.->|Rejected| H[ARCHIVED]
    B -.->|Changed| A
    C -.->|Blocked| B
```

---

## Validation Checklist

Before considering a requirement "complete", verify:

- [ ] REQ-ID is unique and sequential
- [ ] Category is correct
- [ ] Description is clear and testable
- [ ] Priority is assigned
- [ ] Status is current
- [ ] Implementation location is documented (when applicable)
- [ ] Test coverage is documented (when applicable)
- [ ] Related requirements are linked
- [ ] ADR is linked (if architectural decision made)
- [ ] Change history is updated

---

## Metrics and Reports

### Coverage Statistics

- **Total Requirements**: 22
- **Implemented**: 0 (0%)
- **Tested**: 8 (36%)
- **Deployed**: 0 (0%)
- **Approved**: 14 (64%)

### By Category

- **Functional**: 13 (59%)
- **Performance**: 2 (9%)
- **Security**: 3 (14%)
- **Observability**: 1 (5%)
- **Reliability**: 3 (14%)
- **Scalability**: 0 (0%)
- **Maintainability**: 0 (0%)

### By Priority

- **P0 (Critical)**: 1 (5%)
- **P1 (High)**: 8 (36%)
- **P2 (Medium)**: 13 (59%)
- **P3 - LOW**: 0 (0%)

---

**End of Requirement Traceability Matrix v1.1.0**
