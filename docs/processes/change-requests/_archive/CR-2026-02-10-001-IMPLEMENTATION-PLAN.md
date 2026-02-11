# Implementation Plan: Rapid7 InsightOps Log Ingestion Service

**Plan Version**: 1.0  
**Created**: 2026-02-10  
**Last Updated**: 2026-02-10  
**Change Request**: CR-2026-02-10-001

---

## Executive Summary

This document provides a comprehensive, step-by-step implementation plan for building a service that pulls logs from the Rapid7 InsightOps API and saves them to Parquet files for analytics.

**Estimated Timeline**: 13 hours  
**Team Size**: 1-2 developers  
**Methodology**: Test-Driven Development (TDD)

---

## Prerequisites

### Before Starting Implementation

- [x] CR approved and ATP token received: CR-2026-02-10-001
- [ ] Branch created: `feat/REQ-004-rapid7-log-ingestion`
- [ ] Development environment setup
  - [ ] Python 3.9+ installed
  - [ ] pip/virtualenv installed
  - [ ] Git configured
- [ ] Required tools installed
  - [ ] pytest
  - [ ] ruff (linter/formatter)
  - [ ] bandit (security scanner)
- [ ] Test Rapid7 API credentials obtained (development environment)
- [ ] Access to documentation repository

### Development Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development tools
pip install pytest pytest-cov pytest-mock ruff bandit
```

---

## Phase 1: Documentation & Requirements (1 hour)

### Step 1.1: Update Requirement Traceability Matrix

**File**: `/docs/requirements/rtm.md`

**Tasks**:
- [ ] Add REQ-004: [FUNC] Service shall authenticate with Rapid7 InsightOps API
- [ ] Add REQ-005: [FUNC] Service shall fetch logs via API with configurable endpoints
- [ ] Add REQ-006: [FUNC] Service shall parse CSV-formatted log structure dynamically
- [ ] Add REQ-007: [FUNC] Service shall write logs to Apache Parquet format
- [ ] Add REQ-008: [FUNC] Service shall support configuration via environment variables
- [ ] Add REQ-009: [NFR-SEC] API credentials shall be stored in environment variables only
- [ ] Add REQ-010: [NFR-OBS] Service shall emit structured JSON logs with trace context
- [ ] Add REQ-011: [NFR-PERF] Service shall process logs efficiently using batching

**Acceptance Criteria**:
- Each requirement has clear description
- Status set to IN_PROGRESS
- Priority assigned (P1 or P2)
- Linked to CR-2026-02-10-001

**Time**: 20 minutes

---

### Step 1.2: Create Architectural Decision Record

**File**: `/docs/arch/adr/0001-log-ingestion-tech-stack.md`

**Tasks**:
- [ ] Document technology choices (Python, PyArrow, Pandas, Pydantic)
- [ ] Explain rationale for each choice
- [ ] List alternatives considered
- [ ] Document consequences and trade-offs
- [ ] Add links to related requirements

**Time**: 20 minutes

---

### Step 1.3: Create Architecture Diagrams

**File**: `/docs/arch/diagrams/log-ingestion.mmd`

**Tasks**:
- [ ] System context diagram (service, Rapid7 API, file system)
- [ ] Component diagram (internal modules)
- [ ] Data flow diagram (API → Parser → Parquet)
- [ ] Deployment diagram (runtime environment)

**Time**: 15 minutes

---

### Step 1.4: Create Operations Runbook

**File**: `/docs/runbooks/log-ingestion-service.md`

**Tasks**:
- [ ] Service overview
- [ ] Configuration reference
- [ ] Start/stop procedures
- [ ] Monitoring and alerting
- [ ] Troubleshooting guide
- [ ] Common issues and solutions

**Time**: 5 minutes (detailed content added during implementation)

---

## Phase 2: Project Structure Setup (30 minutes)

### Step 2.1: Create Directory Structure

```bash
mkdir -p src/log_ingestion
mkdir -p tests
touch src/log_ingestion/__init__.py
touch tests/__init__.py
```

**Tasks**:
- [ ] Create `/src/log_ingestion/` directory
- [ ] Create `/tests/` directory
- [ ] Create `__init__.py` files
- [ ] Verify structure

**Time**: 5 minutes

---

### Step 2.2: Create Configuration Files

**Files to Create**:
1. `requirements.txt` - Python dependencies
2. `pyproject.toml` - Project metadata and tool configuration
3. `.env.example` - Configuration template
4. Update `.gitignore` - Python-specific ignores

**requirements.txt**:
```
# Core dependencies
requests>=2.31.0
pyarrow>=14.0.0
pandas>=2.1.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
structlog>=23.2.0

# Development dependencies
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
ruff>=0.1.0
bandit>=1.7.5
```

**Tasks**:
- [ ] Create `requirements.txt`
- [ ] Create `pyproject.toml` with project metadata
- [ ] Create `.env.example` with configuration template
- [ ] Update `.gitignore` to exclude `.env`, `__pycache__`, `.pytest_cache`, etc.

**Time**: 15 minutes

---

### Step 2.3: Initialize Git Branch

```bash
git checkout -b feat/REQ-004-rapid7-log-ingestion
git add .
git commit -m "feat: initial project structure for log ingestion service"
```

**Tasks**:
- [ ] Create feature branch
- [ ] Commit initial structure
- [ ] Push to remote

**Time**: 10 minutes

---

## Phase 3: TDD - Configuration Module (1 hour)

### Step 3.1: Write Configuration Tests (RED Phase)

**File**: `/tests/test_config.py`

**Test Cases**:
```python
def test_config_loads_from_environment():
    """Test that configuration loads from environment variables"""
    
def test_config_validates_required_fields():
    """Test that missing required fields raise validation error"""
    
def test_config_uses_default_values():
    """Test that optional fields have sensible defaults"""
    
def test_config_validates_api_endpoint_format():
    """Test that API endpoint must be valid URL"""
    
def test_config_validates_output_dir_exists():
    """Test that output directory path validation"""
```

**Tasks**:
- [ ] Write test for environment variable loading
- [ ] Write test for required field validation
- [ ] Write test for default values
- [ ] Write test for URL validation
- [ ] Write test for path validation
- [ ] Run tests - **verify they fail**

**Expected**: All tests fail (no implementation yet)

**Time**: 20 minutes

---

### Step 3.2: Implement Configuration Module (GREEN Phase)

**File**: `/src/log_ingestion/config.py`

**Implementation**:
```python
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl
from pathlib import Path

class LogIngestionConfig(BaseSettings):
    # Required fields
    rapid7_api_key: str = Field(..., description="Rapid7 API authentication key")
    rapid7_api_endpoint: HttpUrl = Field(..., description="Rapid7 API base URL")
    output_dir: Path = Field(..., description="Directory for Parquet files")
    
    # Optional fields with defaults
    log_level: str = Field(default="INFO", description="Logging level")
    batch_size: int = Field(default=1000, description="Records per batch")
    rate_limit: int = Field(default=60, description="Max API requests per minute")
    retry_attempts: int = Field(default=3, description="Max retry attempts")
    parquet_compression: str = Field(default="snappy", description="Compression algorithm")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

**Tasks**:
- [ ] Implement `LogIngestionConfig` class with Pydantic
- [ ] Add required fields with validation
- [ ] Add optional fields with defaults
- [ ] Add environment variable loading
- [ ] Run tests - **verify they pass**

**Expected**: All tests pass

**Time**: 20 minutes

---

### Step 3.3: Refactor Configuration (REFACTOR Phase)

**Tasks**:
- [ ] Add comprehensive docstrings
- [ ] Add type hints
- [ ] Improve error messages for validation failures
- [ ] Add example usage in docstring
- [ ] Run tests - **verify they still pass**

**Time**: 20 minutes

---

## Phase 4: TDD - API Client (2 hours)

### Step 4.1: Write API Client Tests (RED Phase)

**File**: `/tests/test_api_client.py`

**Test Cases**:
```python
def test_api_client_constructs_auth_header():
    """Test that API client creates proper authentication header"""
    
def test_api_client_fetches_logs_successfully(mock_requests):
    """Test successful log fetch from API"""
    
def test_api_client_handles_401_unauthorized(mock_requests):
    """Test handling of authentication failure"""
    
def test_api_client_handles_429_rate_limit(mock_requests):
    """Test retry with exponential backoff on rate limit"""
    
def test_api_client_handles_500_server_error(mock_requests):
    """Test retry logic on server errors"""
    
def test_api_client_respects_rate_limiting():
    """Test that client enforces rate limit"""
    
def test_api_client_timeout_handling(mock_requests):
    """Test timeout configuration and handling"""
```

**Tasks**:
- [ ] Write test for authentication header
- [ ] Write test for successful fetch with mock response
- [ ] Write tests for HTTP error codes (401, 403, 429, 500)
- [ ] Write test for retry logic with exponential backoff
- [ ] Write test for rate limiting
- [ ] Write test for timeout handling
- [ ] Run tests - **verify they fail**

**Time**: 40 minutes

---

### Step 4.2: Implement API Client (GREEN Phase)

**File**: `/src/log_ingestion/api_client.py`

**Implementation**:
```python
import requests
import time
import structlog
from typing import Dict, Any, Optional
from .config import LogIngestionConfig

logger = structlog.get_logger()

class Rapid7ApiClient:
    """Client for Rapid7 InsightOps API"""
    
    def __init__(self, config: LogIngestionConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.rapid7_api_key}",
            "Content-Type": "application/json"
        })
    
    def fetch_logs(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Fetch logs from API with retry logic"""
        # Implementation with retry, rate limiting, error handling
```

**Tasks**:
- [ ] Implement `Rapid7ApiClient` class
- [ ] Add authentication header construction
- [ ] Implement `fetch_logs()` method
- [ ] Add retry logic with exponential backoff
- [ ] Add rate limiting
- [ ] Add error handling for various HTTP codes
- [ ] Add timeout configuration
- [ ] Add structured logging
- [ ] Run tests - **verify they pass**

**Time**: 60 minutes

---

### Step 4.3: Refactor API Client (REFACTOR Phase)

**Tasks**:
- [ ] Extract retry logic to decorator (`@retry_with_backoff`)
- [ ] Add comprehensive logging (request/response details)
- [ ] Add metrics tracking (API calls, errors, latency)
- [ ] Improve error messages
- [ ] Add docstrings and type hints
- [ ] Run tests - **verify they still pass**

**Time**: 20 minutes

---

## Phase 5: TDD - CSV Parser (1.5 hours)

### Step 5.1: Write Parser Tests (RED Phase)

**File**: `/tests/test_parser.py`

**Test Cases**:
```python
def test_parser_detects_schema_from_headers():
    """Test CSV header detection and schema inference"""
    
def test_parser_detects_schema_from_first_row():
    """Test schema detection from first data row"""
    
def test_parser_parses_data_correctly():
    """Test data parsing with proper types"""
    
def test_parser_handles_malformed_csv():
    """Test graceful handling of malformed CSV"""
    
def test_parser_handles_empty_data():
    """Test handling of empty CSV"""
    
def test_parser_infers_data_types():
    """Test type inference (string, int, float, timestamp)"""
```

**Tasks**:
- [ ] Write test for CSV header detection
- [ ] Write test for first-row schema detection
- [ ] Write test for data parsing
- [ ] Write test for malformed CSV handling
- [ ] Write test for empty data
- [ ] Write test for type inference
- [ ] Run tests - **verify they fail**

**Time**: 30 minutes

---

### Step 5.2: Implement CSV Parser (GREEN Phase)

**File**: `/src/log_ingestion/parser.py`

**Implementation**:
```python
import pandas as pd
import structlog
from typing import Dict, Any, List
from io import StringIO

logger = structlog.get_logger()

class LogParser:
    """Parse log data from CSV format"""
    
    def __init__(self):
        self.schema = None
    
    def detect_schema(self, csv_data: str) -> Dict[str, str]:
        """Detect schema from CSV headers or first row"""
        # Implementation
    
    def parse(self, csv_data: str) -> pd.DataFrame:
        """Parse CSV data into DataFrame"""
        # Implementation with error handling
```

**Tasks**:
- [ ] Implement `LogParser` class
- [ ] Implement `detect_schema()` method
- [ ] Implement `parse()` method with pandas
- [ ] Add type inference logic
- [ ] Add error handling for malformed data
- [ ] Add schema caching
- [ ] Run tests - **verify they pass**

**Time**: 45 minutes

---

### Step 5.3: Refactor Parser (REFACTOR Phase)

**Tasks**:
- [ ] Optimize memory usage for large CSVs
- [ ] Add structured logging for schema detection
- [ ] Improve error messages
- [ ] Add progress reporting for large files
- [ ] Add docstrings and type hints
- [ ] Run tests - **verify they still pass**

**Time**: 15 minutes

---

## Phase 6: TDD - Parquet Writer (1.5 hours)

### Step 6.1: Write Parquet Writer Tests (RED Phase)

**File**: `/tests/test_parquet_writer.py`

**Test Cases**:
```python
def test_writer_creates_parquet_schema():
    """Test Parquet schema creation from DataFrame"""
    
def test_writer_writes_single_batch():
    """Test writing single batch to Parquet file"""
    
def test_writer_writes_multiple_batches():
    """Test appending multiple batches"""
    
def test_writer_partitions_by_date():
    """Test file partitioning by date"""
    
def test_writer_applies_compression():
    """Test compression is applied"""
    
def test_writer_validates_output_file():
    """Test that output file is readable Parquet"""
```

**Tasks**:
- [ ] Write test for schema creation
- [ ] Write test for single batch write
- [ ] Write test for multiple batches
- [ ] Write test for date partitioning
- [ ] Write test for compression
- [ ] Write test for file validation
- [ ] Run tests - **verify they fail**

**Time**: 30 minutes

---

### Step 6.2: Implement Parquet Writer (GREEN Phase)

**File**: `/src/log_ingestion/parquet_writer.py`

**Implementation**:
```python
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import structlog
from pathlib import Path
from datetime import datetime
from .config import LogIngestionConfig

logger = structlog.get_logger()

class ParquetWriter:
    """Write log data to Parquet files"""
    
    def __init__(self, config: LogIngestionConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write(self, df: pd.DataFrame, partition_date: str = None) -> Path:
        """Write DataFrame to Parquet file"""
        # Implementation with compression, partitioning
```

**Tasks**:
- [ ] Implement `ParquetWriter` class
- [ ] Implement schema conversion (pandas → PyArrow)
- [ ] Implement `write()` method with PyArrow
- [ ] Add batch writing support
- [ ] Add date-based partitioning
- [ ] Add compression (Snappy)
- [ ] Add file validation
- [ ] Run tests - **verify they pass**

**Time**: 45 minutes

---

### Step 6.3: Refactor Parquet Writer (REFACTOR Phase)

**Tasks**:
- [ ] Optimize buffer sizes
- [ ] Add progress logging
- [ ] Add metrics (files written, bytes written, compression ratio)
- [ ] Improve error handling
- [ ] Add docstrings and type hints
- [ ] Run tests - **verify they still pass**

**Time**: 15 minutes

---

## Phase 7: TDD - Main Orchestration (1 hour)

### Step 7.1: Write Main Service Tests (RED Phase)

**File**: `/tests/test_main.py`

**Test Cases**:
```python
def test_main_orchestrates_pipeline(mock_api, tmp_path):
    """Test end-to-end pipeline: fetch → parse → write"""
    
def test_main_handles_api_errors(mock_api):
    """Test error handling and recovery"""
    
def test_main_handles_parse_errors(mock_api):
    """Test parse error handling"""
    
def test_main_handles_sigint():
    """Test graceful shutdown on SIGINT"""
    
def test_main_handles_sigterm():
    """Test graceful shutdown on SIGTERM"""
```

**Tasks**:
- [ ] Write test for complete pipeline
- [ ] Write test for API error propagation
- [ ] Write test for parse error handling
- [ ] Write test for graceful shutdown (SIGINT)
- [ ] Write test for graceful shutdown (SIGTERM)
- [ ] Run tests - **verify they fail**

**Time**: 20 minutes

---

### Step 7.2: Implement Main Service (GREEN Phase)

**File**: `/src/log_ingestion/main.py`

**Implementation**:
```python
import signal
import sys
import structlog
from .config import LogIngestionConfig
from .api_client import Rapid7ApiClient
from .parser import LogParser
from .parquet_writer import ParquetWriter

logger = structlog.get_logger()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("shutdown_signal_received", signal=signum)
    sys.exit(0)

def main():
    """Main entry point for log ingestion service"""
    # Load configuration
    # Initialize components
    # Execute pipeline
    # Handle errors
```

**Tasks**:
- [ ] Implement signal handlers (SIGINT, SIGTERM)
- [ ] Implement `main()` function
- [ ] Connect API client → Parser → Parquet writer
- [ ] Add error handling and logging
- [ ] Add progress reporting
- [ ] Run tests - **verify they pass**

**Time**: 30 minutes

---

### Step 7.3: Refactor Main Service (REFACTOR Phase)

**Tasks**:
- [ ] Extract pipeline logic to separate function
- [ ] Add comprehensive logging
- [ ] Add metrics collection
- [ ] Improve error messages
- [ ] Add docstrings
- [ ] Run tests - **verify they still pass**

**Time**: 10 minutes

---

## Phase 8: Integration Testing (1 hour)

### Step 8.1: Create Integration Tests

**File**: `/tests/test_integration.py`

**Test Scenarios**:
```python
def test_end_to_end_with_mock_api(tmp_path):
    """Test complete flow with mocked API responses"""
    # Mock API → Parse → Write → Validate output
    
def test_multi_batch_processing(tmp_path):
    """Test processing multiple batches"""
    
def test_error_recovery(tmp_path):
    """Test error handling and recovery"""
    
def test_parquet_file_readable(tmp_path):
    """Test that output Parquet files are valid"""
```

**Tasks**:
- [ ] Create comprehensive end-to-end test
- [ ] Mock Rapid7 API with realistic responses
- [ ] Validate Parquet output (schema, data integrity)
- [ ] Test multi-batch scenarios
- [ ] Test error recovery
- [ ] Run integration tests
- [ ] Measure test coverage - **verify ≥ 80%**

**Time**: 60 minutes

---

## Phase 9: Observability & Quality (1 hour)

### Step 9.1: Add Structured Logging

**Tasks**:
- [ ] Configure structlog in `main.py`
- [ ] Add log context (trace_id, request_id)
- [ ] Add logging to all major operations
- [ ] Configure JSON output for production
- [ ] Test logging output

**Time**: 20 minutes

---

### Step 9.2: Add Metrics

**Tasks**:
- [ ] Define metrics (counters, gauges, histograms)
- [ ] Add metrics collection in API client
- [ ] Add metrics collection in parser
- [ ] Add metrics collection in writer
- [ ] Document metrics in runbook

**Time**: 20 minutes

---

### Step 9.3: Run Quality Checks

**Commands**:
```bash
# Run linter
ruff check src/ tests/

# Run formatter
ruff format src/ tests/

# Run tests with coverage
pytest tests/ -v --cov=src/log_ingestion --cov-report=term-missing --cov-report=html

# Check coverage threshold
pytest tests/ --cov=src/log_ingestion --cov-fail-under=80
```

**Tasks**:
- [ ] Run ruff linter - fix all issues
- [ ] Run ruff formatter - format all code
- [ ] Run pytest with coverage
- [ ] Verify coverage ≥ 80%
- [ ] Fix any failing tests
- [ ] Review coverage report, add tests for uncovered code

**Time**: 20 minutes

---

## Phase 10: Security & Performance (1 hour)

### Step 10.1: Security Validation

**Commands**:
```bash
# Dependency vulnerability scan
pip-audit

# Security code scan
bandit -r src/

# Check for secrets
git secrets --scan
```

**Tasks**:
- [ ] Run pip-audit for dependency vulnerabilities
- [ ] Fix or document any vulnerabilities
- [ ] Run bandit security scanner
- [ ] Fix any security issues
- [ ] Verify no hardcoded secrets in code
- [ ] Verify `.env` is in `.gitignore`
- [ ] Review file permissions in code

**Time**: 30 minutes

---

### Step 10.2: Performance Validation

**Test Script**: `/tests/benchmark.py`

```python
import time
import pandas as pd
from src.log_ingestion.parser import LogParser
from src.log_ingestion.parquet_writer import ParquetWriter

def benchmark_parsing(num_records=10000):
    """Benchmark CSV parsing performance"""
    
def benchmark_parquet_writing(num_records=10000):
    """Benchmark Parquet writing performance"""
    
def benchmark_compression_ratio():
    """Measure Parquet compression vs raw data"""
```

**Tasks**:
- [ ] Create performance benchmark script
- [ ] Benchmark parsing (target: < 100ms per 1000 records)
- [ ] Benchmark Parquet writing
- [ ] Measure memory usage
- [ ] Measure compression ratio (target: > 70%)
- [ ] Document results

**Time**: 30 minutes

---

## Phase 11: Documentation Finalization (30 minutes)

### Step 11.1: Update README

**File**: `README.md`

**Sections to Add**:
- [ ] Service overview
- [ ] Features list
- [ ] Installation instructions
- [ ] Configuration guide
- [ ] Usage examples
- [ ] Troubleshooting section

**Time**: 15 minutes

---

### Step 11.2: Finalize Runbook

**File**: `/docs/runbooks/log-ingestion-service.md`

**Sections to Complete**:
- [ ] Configuration reference (all environment variables)
- [ ] Start/stop procedures
- [ ] Monitoring metrics
- [ ] Alert definitions
- [ ] Common issues and solutions
- [ ] Troubleshooting flowchart

**Time**: 10 minutes

---

### Step 11.3: Create CHANGELOG

**File**: `CHANGELOG.md`

**Content**:
```markdown
# Changelog

## [0.1.0] - 2026-02-10

### Added
- Initial release of Rapid7 InsightOps log ingestion service
- API client with authentication and retry logic
- Dynamic CSV parser with schema detection
- Parquet writer with compression and partitioning
- Configuration via environment variables
- Structured logging with trace context
- Comprehensive test suite (>80% coverage)
```

**Time**: 5 minutes

---

## Phase 12: Manual Testing & Validation (1 hour)

### Step 12.1: Manual Testing

**Prerequisites**:
- [ ] Rapid7 API credentials (dev environment)
- [ ] Sample log data available

**Test Scenarios**:

1. **Basic Functionality**:
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with real credentials
   
   # Run service
   python -m src.log_ingestion.main
   
   # Verify Parquet files created
   ls -lh /path/to/output/
   ```

2. **Verify Parquet Files**:
   ```python
   import pandas as pd
   df = pd.read_parquet('/path/to/output/logs_2026-02-10.parquet')
   print(df.head())
   print(df.dtypes)
   ```

3. **Error Scenarios**:
   - Invalid API key
   - Network failure
   - Malformed CSV
   - Disk full

**Tasks**:
- [ ] Test with real Rapid7 API
- [ ] Verify Parquet files are created correctly
- [ ] Read Parquet files with pandas - verify data
- [ ] Test error scenarios manually
- [ ] Verify logging output
- [ ] Take screenshots of successful runs

**Time**: 45 minutes

---

### Step 12.2: Final Validation Checklist

**Pre-Merge Checklist**:
- [ ] All automated tests passing
- [ ] Test coverage ≥ 80%
- [ ] Linter passing (zero warnings)
- [ ] Security scan clean
- [ ] Manual testing successful
- [ ] Documentation complete and reviewed
- [ ] No secrets in code or git history
- [ ] Performance benchmarks documented
- [ ] RTM updated with implementation details
- [ ] ADR finalized
- [ ] Runbook complete

**Time**: 15 minutes

---

## Success Criteria

### Definition of Done

- [x] Requirements documented in RTM (REQ-004 through REQ-011)
- [ ] Tests written using TDD (Red-Green-Refactor)
- [ ] All tests passing
- [ ] Test coverage ≥ 80%
- [ ] Linter passing with zero warnings
- [ ] Security scan clean (no new vulnerabilities)
- [ ] Documentation updated (README, ADR, Runbook, RTM)
- [ ] Architecture diagrams created
- [ ] Manual testing successful
- [ ] Performance benchmarks meet targets
- [ ] Code reviewed and approved

### Quality Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Test Coverage | ≥ 80% | TBD | ⏳ Pending |
| Linting Issues | 0 | TBD | ⏳ Pending |
| Security Vulns | 0 critical | TBD | ⏳ Pending |
| Parse Performance | < 100ms/1000 | TBD | ⏳ Pending |
| Compression Ratio | > 70% | TBD | ⏳ Pending |

---

## Risk Mitigation During Implementation

### Common Issues and Solutions

**Issue**: Tests failing during TDD Green phase
- **Solution**: Review test expectations, debug implementation, use breakpoints

**Issue**: Coverage below 80%
- **Solution**: Add tests for uncovered branches, test error paths

**Issue**: Security scan finds vulnerabilities
- **Solution**: Update dependencies, fix code issues, document accepted risks

**Issue**: Performance below targets
- **Solution**: Profile code, optimize hot paths, adjust batch sizes

**Issue**: Integration test failures
- **Solution**: Review mocked API responses, verify data flow, check file permissions

---

## Post-Implementation

### Next Steps After Completion

1. **Create Pull Request**
   - Use PR template
   - Include CR-ID in title
   - Complete DoD checklist
   - Link to requirements and documentation

2. **Code Review**
   - Assign reviewers
   - Address feedback
   - Update tests if needed

3. **Merge and Deploy**
   - Merge to main branch
   - Tag release: `v0.1.0`
   - Deploy to test environment
   - Monitor for issues

4. **Monitor in Production**
   - Watch logs for errors
   - Monitor metrics
   - Verify SLOs are met
   - Document any issues

---

## Timeline Summary

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| 1. Documentation & Requirements | 1 hour | Day 1, 09:00 | Day 1, 10:00 |
| 2. Project Structure | 30 min | Day 1, 10:00 | Day 1, 10:30 |
| 3. Configuration Module | 1 hour | Day 1, 10:30 | Day 1, 11:30 |
| 4. API Client | 2 hours | Day 1, 11:30 | Day 1, 13:30 |
| Lunch Break | 30 min | Day 1, 13:30 | Day 1, 14:00 |
| 5. CSV Parser | 1.5 hours | Day 1, 14:00 | Day 1, 15:30 |
| 6. Parquet Writer | 1.5 hours | Day 1, 15:30 | Day 1, 17:00 |
| 7. Main Orchestration | 1 hour | Day 1, 17:00 | Day 1, 18:00 |
| 8. Integration Testing | 1 hour | Day 2, 09:00 | Day 2, 10:00 |
| 9. Observability & Quality | 1 hour | Day 2, 10:00 | Day 2, 11:00 |
| 10. Security & Performance | 1 hour | Day 2, 11:00 | Day 2, 12:00 |
| 11. Documentation | 30 min | Day 2, 12:00 | Day 2, 12:30 |
| 12. Manual Testing | 1 hour | Day 2, 12:30 | Day 2, 13:30 |
| **Total** | **13 hours** | | |

**Note**: Timeline assumes focused work with minimal interruptions. Adjust based on team capacity and priorities.

---

## Appendix

### Useful Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/log_ingestion --cov-report=html

# Run linter
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Security scan
bandit -r src/
pip-audit

# Run service
python -m src.log_ingestion.main
```

### Related Documentation

- Change Request: `/docs/processes/change-requests/CR-2026-02-10-001.md`
- Impact Assessment: `/docs/processes/change-requests/CR-2026-02-10-001-IMPACT-ASSESSMENT.md`
- RTM: `/docs/requirements/rtm.md`
- ADR: `/docs/arch/adr/0001-log-ingestion-tech-stack.md`
- Runbook: `/docs/runbooks/log-ingestion-service.md`

---

**Implementation Plan Version**: 1.0  
**Status**: APPROVED  
**Last Updated**: 2026-02-10
