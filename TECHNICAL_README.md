# Medical Telegram Data Warehouse - Technical Documentation

## Project Overview

End-to-end ELT (Extract, Load, Transform) data pipeline for Ethiopian medical business Telegram data.

**Tech Stack:**
- Extraction: Telethon (Telegram API)
- Loading: PostgreSQL + psycopg2
- Transformation: dbt + SQL
- Enrichment: YOLOv8 (object detection)
- API: FastAPI + Pydantic
- Orchestration: Dagster
- Infrastructure: Docker Compose

## Architecture

```
Telegram Channels
      ↓
   Scraper (async/await, Telethon)
      ↓
Data Lake (JSON, partitioned by date)
      ↓
PostgreSQL raw.telegram_messages
      ↓
dbt Staging (stg_telegram_messages)
      ↓
Star Schema (Marts)
 ├── dim_channels
 ├── dim_dates
 ├── fct_messages
 └── fct_image_detections (YOLO)
      ↓
FastAPI Analytics Endpoints
      ↓
Dagster Orchestration
```

## Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with actual credentials
```

### 2. Generate Test Data

```bash
python scripts/generate_mock_data.py
```

Output:
- `data/raw/telegram_messages/YYYY-MM-DD/*.json` (1,000 messages)
- `data/raw/images/{channel}/*.jpg` (50 placeholder images)

### 3. PostgreSQL Setup

**Option A: Docker**
```bash
docker-compose up -d postgres
```

**Option B: Manual**
```bash
# Create database
createdb telegram_warehouse
```

### 4. Load Data to PostgreSQL

```bash
python src/load_to_postgres.py
```

Creates `raw.telegram_messages` table with 1,000 records.

### 5. Run dbt Transformations

```bash
cd medical_warehouse
dbt parse
dbt run
dbt test
cd ..
```

Outputs:
- `staging.stg_telegram_messages` (view)
- `marts.dim_channels` (5 rows)
- `marts.dim_dates` (1,096 rows)
- `marts.fct_messages` (1,000 rows)

### 6. Run YOLO Detection

```bash
python src/yolo_detect.py
```

Outputs:
- `data/yolo_results.csv` (detection results)
- Creates `raw.image_detections` table

### 7. Start FastAPI

```bash
uvicorn api.main:app --reload
```

Access API at: `http://localhost:8000`
OpenAPI docs: `http://localhost:8000/docs`

### 8. Run Dagster (Optional)

```bash
dagster dev -f src/pipeline.py
```

Access UI at: `http://localhost:3000`

## File Structure

```
medical-telegram-warehouse-week8/
├── src/                           # ETL modules
│   ├── scraper.py                # Telegram extraction (380 lines)
│   ├── load_to_postgres.py       # Data loading (300+ lines)
│   ├── yolo_detect.py            # Object detection (250+ lines)
│   ├── pipeline.py               # Dagster orchestration (200+ lines)
│   └── definitions.py            # Dagster definitions
├── api/                           # FastAPI application
│   ├── main.py                   # Endpoints (350+ lines)
│   ├── database.py               # Database connection
│   └── schemas.py                # Pydantic models
├── medical_warehouse/            # dbt project
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_telegram_messages.sql
│   │   └── marts/
│   │       ├── dim_channels.sql
│   │       ├── dim_dates.sql
│   │       ├── fct_messages.sql
│   │       └── fct_image_detections.sql
│   ├── tests/
│   │   ├── assert_no_future_messages.sql
│   │   └── assert_positive_engagement.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── tests/                         # Unit & integration tests
│   ├── test_scraper.py
│   ├── test_load_postgres.py
│   ├── test_yolo_detect.py
│   ├── test_api.py
│   └── test_pipeline.py
├── scripts/                       # Utility scripts
│   ├── generate_mock_data.py
│   ├── load_yolo_to_postgres.py
│   └── validate_pipeline.py
├── data/                          # Data lake
│   ├── raw/
│   │   ├── telegram_messages/
│   │   └── images/
│   └── yolo_results.csv
├── notebooks/                     # Analysis notebooks
├── logs/                          # Log files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .github/workflows/unittests.yml
```

## Key Components

### Task 1: Telegram Scraper (`src/scraper.py`)

- Async/await pattern for non-blocking I/O
- Telethon client for API integration
- Rate limiting (2s between channels)
- Image download & storage
- Comprehensive error logging
- Duplicate detection via unique constraint

**Usage:**
```python
from scraper import TelegramScraper
import asyncio

async def main():
    scraper = TelegramScraper(api_id, api_hash, phone)
    await scraper.authenticate()
    results = await scraper.scrape_multiple_channels(['channel1', 'channel2'])
    await scraper.close()

asyncio.run(main())
```

### Task 2: dbt Transformation

**Staging Model** - Cleans raw data:
- Type casting (dates, integers)
- Text trimming & deduplication
- Null handling
- Calculated fields (message_length, has_image_flag)

**Star Schema:**

`dim_channels` - 5 rows
```
channel_key (PK) | channel_name | channel_username | channel_type | created_at
```

`dim_dates` - 1,096 rows (2024-2026)
```
date_key (PK) | full_date | day_of_week | month | quarter | is_weekend
```

`fct_messages` - 1,000 rows
```
message_id | channel_key (FK) | date_key (FK) | message_text | views | forwards | has_media
```

### Task 3: YOLO Detection (`src/yolo_detect.py`)

Image Classification:
- `promotional` - person + product
- `product_display` - product only
- `lifestyle` - person only
- `other` - neither

**Output CSV:**
```
message_id | channel_name | detected_class | confidence_score | image_category | num_objects
```

### Task 4: FastAPI Endpoints (`api/main.py`)

1. **GET /api/reports/top-products?limit=10**
   - Returns most mentioned products
   - Response: ProductMetric array with frequency, avg_views, avg_forwards

2. **GET /api/channels/{channel_name}/activity**
   - Channel engagement metrics
   - Response: ChannelActivity with total_messages, total_views, avg_forwards, image_percentage

3. **GET /api/search/messages?query=paracetamol&limit=20**
   - Full-text message search
   - Response: MessageSearchResponse with matching messages

4. **GET /api/reports/visual-content**
   - Image usage statistics
   - Response: VisualContentStats by category and channel

**Documentation:** Auto-generated at `/docs` (Swagger UI)

### Task 5: Dagster Orchestration (`src/pipeline.py`)

Pipeline Operations:
1. `scrape_telegram_data` - Extract
2. `load_raw_to_postgres` - Load
3. `run_dbt_transformations` - Transform
4. `run_yolo_enrichment` - Enrich

**Dependency Graph:**
```
scrape → load → transform → yolo
```

**Run:**
```bash
dagster dev -f src/pipeline.py
```

## Database Schema

### Raw Layer
```sql
CREATE TABLE raw.telegram_messages (
    message_id, channel_name, channel_username,
    message_date, message_text, has_media,
    image_path, views, forwards, media_type,
    loaded_at
);

CREATE TABLE raw.image_detections (
    message_id, channel_name, detected_class,
    confidence_score, image_category, num_objects,
    loaded_at
);
```

### Analytics Layer (dbt marts)
- Staging views for data cleaning
- Dimensional tables (dim_channels, dim_dates)
- Fact table (fct_messages)
- Image detection joins (fct_image_detections)

## Testing

### Unit Tests
```bash
pytest tests/ -v --cov=src
```

Test Coverage:
- `test_scraper.py` - Scraper initialization, data structure
- `test_load_postgres.py` - Connection, data insertion
- `test_yolo_detect.py` - Image classification logic
- `test_api.py` - Endpoint validation
- `test_pipeline.py` - Dagster ops definitions

### Pipeline Validation
```bash
python scripts/validate_pipeline.py
```

Checks:
- ✓ Project structure (27 files, 12 directories)
- ✓ Python syntax (19 files)
- ✓ Dependencies in requirements.txt
- ✓ dbt models (1 staging, 4 marts)
- ✓ Docker configuration
- ✓ Environment template
- ✓ Git commits with team attribution

## CI/CD Pipeline

**.github/workflows/unittests.yml**

On push/PR to main/develop:
1. Python 3.11 setup
2. Dependency installation
3. Flake8 linting (E9, F63, F7, F82)
4. Black format check
5. pytest execution
6. Coverage reporting

## Configuration

### Environment Variables (.env)

```bash
# Telegram API (optional for mock data)
TELEGRAM_API_ID=your_id
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE=+251900000000

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telegram_warehouse
DB_USER=postgres
DB_PASSWORD=your_password

# dbt
DBT_PROFILES_DIR=./medical_warehouse
```

### Docker Compose

Services:
- `postgres`: PostgreSQL 15 with health checks
- `app`: Python environment with all dependencies

```bash
docker-compose up -d
```

## Development

### Adding New dbt Models

1. Create `.sql` file in `models/staging/` or `models/marts/`
2. Add descriptions in `schema.yml`
3. Define tests (not_null, unique, relationships)
4. Run `dbt run && dbt test`

### Adding New API Endpoints

1. Define Pydantic schema in `api/schemas.py`
2. Create endpoint in `api/main.py` with proper type hints
3. Add docstrings and example responses
4. Test via `/docs` Swagger UI

### Extending YOLO Detection

1. Modify class definitions in `YOLODetector.PERSON_CLASSES`, etc.
2. Update classification logic in `classify_image()`
3. Re-run detection: `python src/yolo_detect.py`

## Troubleshooting

### Database Connection Error
```
Error: could not connect to server: Connection refused
Solution: Start PostgreSQL (docker-compose up -d postgres)
```

### dbt Profile Error
```
Error: target 'dev' not found
Solution: Ensure .env has DB credentials, check profiles.yml
```

### YOLO Model Download
```
Error: Cannot download yolov8n.pt
Solution: First run creates ~35MB download, ensure internet connection
```

### API Port Already in Use
```
Error: Address already in use :8000
Solution: uvicorn api.main:app --port 8001
```

## Performance Notes

- Staging view (stg_telegram_messages) uses ROW_NUMBER() for deduplication
- Star schema enables efficient aggregations (no complex joins)
- Date dimension enables fast time-based filtering
- Surrogate keys improve join performance
- YOLO nano model trades accuracy for speed (efficient for laptops)

## Code Quality

- **Linting:** flake8 (PEP 8 compliance)
- **Formatting:** black (auto-formatter)
- **Type Hints:** Pydantic + Python type annotations
- **Docstrings:** Comprehensive module and function documentation
- **Error Handling:** Try-catch with logging
- **Testing:** pytest with fixtures and mocking

## Deployment

### Local
```bash
# Install
pip install -r requirements.txt

# Run all components
docker-compose up -d
python src/load_to_postgres.py
python src/yolo_detect.py
uvicorn api.main:app
dagster dev -f src/pipeline.py
```

### Production
1. Set up PostgreSQL with replication
2. Configure dbt with production profiles
3. Deploy FastAPI via Gunicorn/uWSGI
4. Schedule Dagster jobs via cron or cloud scheduler
5. Set up monitoring and alerting
6. Implement data retention policies

## References

- [Telethon Documentation](https://docs.telethon.dev/)
- [dbt Documentation](https://docs.getdbt.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Dagster Documentation](https://docs.dagster.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## License

Technical documentation for Kara Solutions Week 8 Challenge.

---

**Last Updated:** 30 June 2026  
**Version:** 1.0  
**Status:** Production Ready
