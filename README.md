# EcoLens Server

EcoLens 백엔드 서비스(FastAPI + PostgreSQL/PostGIS).

전체 기획서와 단계별 진행 상황은 [`docs/`](./docs) 폴더를 참고하세요.

## 구조

```
ecolens_server/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI 앱 진입점 (/health, /ready)
│   ├── config.py          # Pydantic Settings 기반 환경 설정
│   ├── db.py              # SQLAlchemy 엔진/세션
│   ├── core/
│   │   ├── security.py    # 비밀번호 해시, JWT 발급/검증
│   │   └── deps.py        # 의존성 (get_current_user)
│   ├── models/            # ORM 모델 (User, Session, RoutePoint, Trash 등)
│   ├── schemas/           # Pydantic 스키마
│   └── ...
├── alembic/               # 마이그레이션
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── docs/                  # 서비스 기획/설계 문서
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 1단계: 프로젝트 기반 구성

이 단계에서는 서버가 컨테이너 환경에서 부팅되고, PostgreSQL(PostGIS)과 연결되며, 기본 ORM/Alembic 스키마가 준비됩니다.

### 실행 방법

```bash
# 1. 환경 변수 파일 생성
cp .env.example .env

# 2. 컨테이너 빌드 및 실행
docker compose up --build -d

# 3. 헬스 체크
curl http://localhost:8000/health
# {"status":"ok","service":"EcoLens","ai_mode":"mock"}

# 4. 초기 마이그레이션 생성 및 적용
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head
```

### 테스트 방법

```bash
# 컨테이너 진입 후 Python 임포트 확인
docker compose exec api python -c "from app.models import Base; print(sorted(Base.metadata.tables.keys()))"

# DB 컨테이너 정상 여부
docker compose exec db pg_isready -U ecolens
```

예상 출력(테이블 목록):
```
['detection_logs', 'plogging_sessions', 'route_points', 'trash_records', 'users']
```

## 개발 순서

1. **1단계(완료)**: 프로젝트 기반 구성 - FastAPI + Docker + PostGIS + Alembic
2. 2단계: 사용자 인증 (signup / login / me)
3. 3단계: 플로깅 세션 시작/종료/복구
4. 4단계: GPS 위치 추적 및 Batch 저장
5. 5단계: 카메라 + Mock AI 탐지
6. 6단계: 실제 AI 탐지 + 중복 검사
7. 7단계: Before·After 정화 검증 + 점수
8. 8단계: 환경지도
9. 9단계: 리포트 및 통계
10. 10단계: 안정화, 오프라인 동기화, 테스트

각 단계가 끝날 때마다 실행/테스트 방법이 이 README에 추가됩니다.