# 7. 개발 환경 구성 및 실행 가이드 (서버 파트)

## 전제

- Docker 및 Docker Compose 설치됨
- Python 3.11+ (로컬 개발 시)
- PostgreSQL 15+ with PostGIS

## 디렉터리 구조 (최종 목표)

```text
ecolens_server/
├── app/
├── alembic/
├── ai/
├── tests/
├── docs/                 # 본 문서들
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 환경 변수 (`.env`)

`.env.example` 기준:

```env
# App
APP_NAME=EcoLens
ENV=local
DEBUG=true
API_PREFIX=/api

# Database
POSTGRES_USER=ecolens
POSTGRES_PASSWORD=ecolens
POSTGRES_DB=ecolens
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://ecolens:ecolens@db:5432/ecolens

# JWT
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI
AI_MODE=mock          # mock | yolo
AI_SERVICE_URL=http://ai:8001

# Storage
STORAGE_TYPE=local    # local | s3
STORAGE_LOCAL_PATH=./storage
S3_ENDPOINT=
S3_BUCKET=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

## docker-compose.yml (제안)

```yaml
version: "3.9"

services:
  db:
    image: postgis/postgis:15-3.4
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./alembic:/app/alembic
      - ./storage:/app/storage

  ai:
    build: ./ai
    env_file: .env
    depends_on:
      - api
    ports:
      - "8001:8001"

volumes:
  db_data:
```

> `ai` 서비스는 MVP 초기(Mock) 단계에서는 생략하거나 FastAPI에 인라인으로 둘 수 있다.

## Dockerfile (제안)

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## requirements.txt (제안)

```text
fastapi
uvicorn[standard]
sqlalchemy
alembic
psycopg2-binary
pydantic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
python-multipart
geoalchemy2
httpx
pytest
pytest-asyncio
```

## 최초 실행 순서

```bash
# 1. 환경 변수 복사
cp .env.example .env

# 2. 컨테이너 빌드 및 실행
docker compose up -d --build

# 3. 마이그레이션(PostGIS 확장 포함)
docker compose exec api alembic upgrade head

# 4. API 문서 확인
# http://localhost:8000/docs  (OpenAPI Swagger UI)
```

## 로컬 개발 (Docker 없이)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

DB는 로컬 PostgreSQL + PostGIS를 실행하거나 docker compose db 만 실행:

```bash
docker compose up -d db
```

## Alembic 초기 설정

```bash
alembic init alembic
```

`alembic/env.py`에서 `DATABASE_URL`을 읽도록 설정하고, `target_metadata`를 SQLAlchemy `Base.metadata`와 연결.

PostGIS 확장 마이그레이션(첫 번째 revision):

```python
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

def downgrade():
    op.execute("DROP EXTENSION IF EXISTS postgis;")
```

## 테스트 실행

```bash
# 전체
pytest

# 통합 테스트만
pytest tests/integration

# 커버리지
pytest --cov=app --cov-report=term-missing
```

테스트용 DB는 별도 데이터베이스(예: `ecolens_test`) 사용 권장. PostGIS 확장 필요.

## API 문서

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- 모든 응답은 공통 래퍼(`data`/`error`) 사용. 상세는 [04-api.md](./04-api.md).

## 단계별 README 기록 규칙

각 단계 종료 시 프로젝트 루트 `README.md`에 아래 항목을 갱신:

- 실행 방법 (명령어)
- 테스트 방법 (명령어 + 기대 결과)
- 변경된 환경 변수
- 마이그레이션 적용 사항
- 알려진 제한 사항

## CI (GitHub Actions) 제안

- PR 시: lint(`ruff`/`flake8`) + `pytest`
- main 머지 시: Docker 이미지 빌드 + push (선택)
- 마이그레이션은 배포 단계에서 `alembic upgrade head` 수행