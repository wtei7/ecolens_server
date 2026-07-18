# 2. 시스템 구조 및 기술 스택 (서버 파트)

## 시스템 구조

서버는 크게 세 영역으로 구성된다.

```text
React Native App
        ↓ REST API
FastAPI Server
├─ 인증 (JWT)
├─ 플로깅 세션 관리
├─ 위치 데이터 저장
├─ 쓰레기 데이터 관리
├─ 중복 탐지 검사
├─ 점수 계산
└─ 리포트 생성

        ↓
PostgreSQL + PostGIS
├─ 사용자
├─ 플로깅 세션
├─ 이동 경로
├─ 쓰레기 기록
└─ 점수 기록

        ↓ (AI 서버는 FastAPI와 분리 가능)
AI Service
├─ 쓰레기 탐지 (YOLO)
├─ 쓰레기 종류 분류
└─ Before·After 검증
```

### 모듈 분리 원칙

- **AI 탐지 기능과 플로깅 세션 기능을 분리**: 한 기능의 장애가 전체 활동을 중단시키지 않도록 한다.
- **AI 서버가 응답하지 않더라도** GPS 경로 기록은 계속 저장되어야 한다.
- **인증, 세션, 위치, 쓰레기, 리포트**는 각각 별도 라우터/서비스 계층으로 분리한다.

## 기술 스택

### 백엔드

- **Python**
- **FastAPI** — REST API 프레임워크
- **SQLAlchemy** — ORM
- **Alembic** — DB 마이그레이션
- **Pydantic** — 요청/응답 스키마 검증
- **JWT** — 인증 (access token, 필요시 refresh token)

### 데이터베이스

- **PostgreSQL**
- **PostGIS** — 위치/공간 쿼리, `POINT` 타입, 거리 계산, 영역 기반 조회

### AI

- **YOLO 기반 객체 탐지**
- **OpenCV 기반 이미지 전처리**
- **Before·After 이미지 비교**
- AI 기능이 준비되지 않은 초기 단계에서는 **Mock AI API** 제공

### 파일 저장소

- MVP에서는 **로컬 파일 저장** 또는 **S3 호환 스토리지** 사용
- 탐지 이미지, Before/After 이미지 저장

### 개발 환경

- **Docker Compose** — FastAPI, PostgreSQL, (선택) AI 서버 컨테이너
- **GitHub Actions** — CI/CD
- **`.env` 기반 환경 변수 관리**

## 폴더 구조 (제안)

```text
ecolens_server/
├── app/
│   ├── main.py                 # FastAPI 앱 진입점
│   ├── core/
│   │   ├── config.py           # 설정 (.env 로드)
│   │   ├── security.py         # JWT 해싱/인코딩
│   │   └── database.py         # DB 세션/엔진
│   ├── api/
│   │   ├── deps.py             # 의존성 (현재 사용자 등)
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── plogging.py
│   │       ├── trash.py
│   │       ├── map.py
│   │       ├── report.py
│   │       └── ai.py
│   ├── models/                 # SQLAlchemy 모델
│   ├── schemas/                # Pydantic 스키마
│   ├── services/               # 비즈니스 로직 계층
│   │   ├── auth_service.py
│   │   ├── session_service.py
│   │   ├── route_service.py
│   │   ├── trash_service.py
│   │   ├── detect_service.py
│   │   ├── verify_service.py
│   │   ├── score_service.py
│   │   └── report_service.py
│   └── utils/
│       ├── geo.py             # PostGIS/거리 계산 유틸
│       └── dedup.py           # 중복 탐지 검사
├── alembic/                   # 마이그레이션
├── ai/                        # AI 서비스 (별도 컨테이너 가능)
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── docs/
```

## 계층 분리 원칙 (Codex 작업 지침 반영)

- **라우터(api)**: HTTP 요청/응답 처리만 담당. 비즈니스 로직 최소화.
- **서비스(services)**: 비즈니스 로직 (세션 생성, 중복 검사, 점수 계산, 리포트 집계 등).
- **모델(models)**: SQLAlchemy ORM 엔티티.
- **스키마(schemas)**: Pydantic 요청/응답 모델.
- 하나의 파일에 여러 책임을 넣지 않는다.
- API 응답 형식을 일관되게 유지한다.

## 일관된 API 응답 형식 (제안)

성공 응답:

```json
{
  "data": { },
  "meta": { }
}
```

에러 응답:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": { }
  }
}
```

상세한 엔드포인트 정의는 [04-api.md](./04-api.md) 참고.

## 인증 흐름

```text
POST /api/auth/signup → 사용자 생성 + password hash 저장
POST /api/auth/login  → 이메일/비밀번호 검증 + JWT 발급
GET  /api/auth/me     → JWT 검증 후 사용자 정보 반환
```

- 비밀번호는 반드시 해시하여 저장 (예: `passlib` with bcrypt).
- 보호된 엔드포인트는 JWT 의존성(`get_current_user`)을 통해 인증한다.