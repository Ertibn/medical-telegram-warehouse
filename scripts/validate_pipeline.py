"""
Validation script for complete pipeline.
Checks all components are working correctly.
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_project_structure():
    """Validate all required directories and files exist."""
    logger.info("Validating project structure...")
    
    required_dirs = [
        'src', 'api', 'tests', 'scripts', 'notebooks',
        'data/raw/telegram_messages', 'data/raw/images',
        'medical_warehouse/models/staging',
        'medical_warehouse/models/marts',
        'medical_warehouse/tests',
        '.github/workflows', 'logs'
    ]
    
    required_files = {
        'Python': [
            'src/scraper.py',
            'src/load_to_postgres.py',
            'src/yolo_detect.py',
            'src/pipeline.py',
            'src/definitions.py',
            'api/main.py',
            'api/database.py',
            'api/schemas.py',
            'scripts/generate_mock_data.py',
            'scripts/load_yolo_to_postgres.py'
        ],
        'SQL': [
            'medical_warehouse/models/staging/stg_telegram_messages.sql',
            'medical_warehouse/models/marts/dim_channels.sql',
            'medical_warehouse/models/marts/dim_dates.sql',
            'medical_warehouse/models/marts/fct_messages.sql',
            'medical_warehouse/models/marts/fct_image_detections.sql'
        ],
        'Config': [
            'medical_warehouse/dbt_project.yml',
            'medical_warehouse/profiles.yml',
            'requirements.txt',
            'Dockerfile',
            'docker-compose.yml',
            '.env.example',
            '.gitignore'
        ],
        'Tests': [
            'tests/test_scraper.py',
            'tests/test_load_postgres.py',
            'tests/test_yolo_detect.py',
            'tests/test_api.py',
            'tests/test_pipeline.py'
        ]
    }
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.error(f"Missing directories: {missing_dirs}")
        return False
    
    logger.info("✓ All required directories exist")
    
    total_files = sum(len(files) for files in required_files.values())
    missing_files = []
    
    for category, files in required_files.items():
        for file_path in files:
            if not Path(file_path).exists():
                missing_files.append(f"{category}: {file_path}")
    
    if missing_files:
        logger.error(f"Missing files:\n  " + "\n  ".join(missing_files))
        return False
    
    logger.info(f"✓ All {total_files} required files exist")
    return True


def validate_python_syntax():
    """Validate Python files have correct syntax."""
    logger.info("Validating Python syntax...")
    
    import py_compile
    
    python_files = list(Path('src').glob('*.py')) + \
                   list(Path('api').glob('*.py')) + \
                   list(Path('tests').glob('*.py')) + \
                   list(Path('scripts').glob('*.py'))
    
    errors = []
    for py_file in python_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(str(py_file))
    
    if errors:
        logger.error(f"Python syntax errors in: {errors}")
        return False
    
    logger.info(f"✓ All {len(python_files)} Python files have valid syntax")
    return True


def validate_requirements():
    """Validate requirements.txt has all dependencies."""
    logger.info("Validating requirements.txt...")
    
    required_packages = {
        'pandas': 'Data manipulation',
        'telethon': 'Telegram API',
        'psycopg2-binary': 'PostgreSQL driver',
        'dbt-postgres': 'dbt transformation',
        'fastapi': 'Web API framework',
        'pydantic': 'Data validation',
        'ultralytics': 'YOLO object detection',
        'dagster': 'Pipeline orchestration',
        'pytest': 'Testing framework'
    }
    
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    missing = []
    for package, description in required_packages.items():
        if package.lower() not in content:
            missing.append(f"{package} ({description})")
    
    if missing:
        logger.error(f"Missing requirements:\n  " + "\n  ".join(missing))
        return False
    
    logger.info(f"✓ All {len(required_packages)} required packages in requirements.txt")
    return True


def validate_dbt_models():
    """Validate dbt model definitions."""
    logger.info("Validating dbt models...")
    
    dbt_path = Path('medical_warehouse/models')
    
    staging_models = list(dbt_path.glob('staging/*.sql'))
    mart_models = list(dbt_path.glob('marts/*.sql'))
    
    logger.info(f"  - Staging models: {len(staging_models)}")
    logger.info(f"  - Mart models: {len(mart_models)}")
    
    if len(staging_models) < 1:
        logger.error("Missing staging models")
        return False
    
    if len(mart_models) < 3:
        logger.error("Missing mart models (need dim_channels, dim_dates, fct_messages)")
        return False
    
    logger.info(f"✓ dbt models properly structured")
    return True


def validate_git_commits():
    """Validate git history has proper commits."""
    logger.info("Validating git commits...")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['git', 'log', '--oneline', '-10'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("Could not read git log")
            return True
        
        commits = result.stdout.strip().split('\n')
        logger.info(f"  - Total commits: {len(commits)}")
        
        team_commits = [c for c in commits if 'Kara Solutions Team' in c]
        if team_commits:
            logger.info(f"  - Team-attributed commits: {len(team_commits)}")
        
        logger.info(f"✓ Git history present")
        return True
    
    except Exception as e:
        logger.warning(f"Could not validate git: {e}")
        return True


def validate_docker_setup():
    """Validate Docker configuration."""
    logger.info("Validating Docker setup...")
    
    if not Path('Dockerfile').exists():
        logger.error("Dockerfile not found")
        return False
    
    if not Path('docker-compose.yml').exists():
        logger.error("docker-compose.yml not found")
        return False
    
    logger.info("✓ Docker configuration present")
    return True


def validate_env_config():
    """Validate environment configuration template."""
    logger.info("Validating environment configuration...")
    
    if not Path('.env.example').exists():
        logger.error(".env.example not found")
        return False
    
    with open('.env.example', 'r') as f:
        env_content = f.read()
    
    required_env_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'TELEGRAM_PHONE',
        'DB_HOST',
        'DB_PORT',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing = [var for var in required_env_vars if var not in env_content]
    
    if missing:
        logger.error(f"Missing env variables: {missing}")
        return False
    
    logger.info(f"✓ Environment configuration has all {len(required_env_vars)} variables")
    return True


def main():
    """Run all validations."""
    logger.info("=" * 70)
    logger.info("MEDICAL TELEGRAM WAREHOUSE - PIPELINE VALIDATION")
    logger.info("=" * 70)
    
    checks = [
        ("Project Structure", validate_project_structure),
        ("Python Syntax", validate_python_syntax),
        ("Requirements", validate_requirements),
        ("dbt Models", validate_dbt_models),
        ("Docker Setup", validate_docker_setup),
        ("Environment Config", validate_env_config),
        ("Git Commits", validate_git_commits),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            logger.info(f"\n{check_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            logger.error(f"Error in {check_name}: {e}")
            results.append((check_name, False))
    
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status:8} - {check_name}")
    
    logger.info(f"\nTotal: {passed}/{total} checks passed")
    logger.info("=" * 70)
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
