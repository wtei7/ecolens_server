# 6. 개발 순서 및 완료 조건 (서버 파트)

## 개발 원칙 (Codex 작업 지침 반영)

- 모든 코드는 Python 타입을 명시한다.
- 하나의 파일에 여러 책임을 넣지 않는다.
- UI/비즈니스 로직 분리 원칙은 모바일 측에 해당하나, 서버도 라우터/서비스/모델을 분리한다.
- API 요청은 별도 서비스 계층에서 관리.
- 데이터베이스 변경은 Alembic Migration으로 관리.
- API 응답 형식을 일관되게 유지.
- AI 모델 없이도 개발할 수 있도록 Mock 모드를 먼저 구현.
- 기존 기능 수정 시 회귀 오류가 발생하지 않도록 테스트.
- 각 단계가 끝날 때 실행 방법과 테스트 방법을 README에 기록.
- 한 번에 전체 기능을 구현하지 말고 단계별로 구현.

## 단계별 개발 순서 (서버 측)

### 1단계: 프로젝트 기반 구성
- FastAPI 프로젝트 생성
- Docker Compose 설정 (FastAPI + PostgreSQL+PostGIS)
- PostgreSQL 연결 및 세션 설정
- 공통 환경 변수 설정(`.env`, `AI_MODE` 등)
- API 클라이언트/응답 래퍼 구성
- Alembic 초기 설정 + PostGIS 확장 마이그레이션

### 2단계: 사용자 인증
- 회원가입 (이메일/비밀번호/닉네임 검증)
- 로그인 (JWT 발급)
- 인증 상태 유지용 `get_current_user` 의존성
- 보호 엔드포인트 적용

### 3단계: 플로깅 세션
- 세션 생성
- 세션 종료 (통계 집계)
- 활동 시간 측정
- 활성 세션 복구용 조회(`?status=active`)

### 4단계: 위치 추적 및 지도 (서버 측)
- 단건/배치 좌표 저장 API
- 노이즈 필터(정확도/속도/점프)
- `sequence` 발급
- 이동 거리 계산(PostGIS)
- 세션 경로 조회 API

### 5단계: 카메라 및 Mock 탐지 (서버 측)
- `POST /api/ai/detect` Mock 구현
- `POST /api/ai/verify-cleaning` Mock 구현
- `AI_MODE=mock` 분기 처리
- 탐지 응답 스키마 정의(Bounding Box 0~1 비율)

### 6단계: 실제 AI 탐지 (서버 측)
- YOLO 모델 연결
- 이미지 업로드/저장
- 탐지 결과 변환(정규화 Bounding Box)
- 쓰레기 위치 자동 등록 흐름 연결
- 중복 탐지 검사(15초/8m)

### 7단계: 정화 검증 (서버 측)
- Before 이미지 저장
- After 이미지 수신
- 정화 검증 로직(Mock → 실제 AI)
- 상태 변경 + 점수 지급
- 사용자 누적 점수/정화 수 갱신

### 8단계: 환경지도 (서버 측)
- 영역(bounding box) 기반 쓰레기 조회 API
- 상태/종류/기간 필터
- 마커 클러스터링 API(PostGIS)

### 9단계: 리포트 (서버 측)
- 활동 결과 집계
- 경로/쓰레기 데이터 취합
- 종류별 통계/정화율
- 규칙 기반 자동 요약 문장 생성

### 10단계: 안정화 (서버 측)
- Batch 멱등 처리
- 예외/에러 응답 정리
- Rate-limit(탐지 요청)
- 테스트 코드 작성
- API 문서(OpenAPI) 점검
- 활성 세션 자동 만료 배치

## 완료 조건 (서버 시나리오)

다음 시나리오가 서버 API 수준에서 정상 작동하면 MVP 서버 구현 완료.

1. `POST /api/auth/signup` · `POST /api/auth/login` · `GET /api/auth/me` 정상 동작.
2. `POST /api/plogging/sessions` 로 세션 생성.
3. `POST .../route-points/batch` 로 좌표가 저장되고 `GET .../route-points` 로 조회됨.
4. `POST /api/ai/detect` 가 Mock/실제 모드에서 정상 응답.
5. `POST /api/plogging/sessions/{id}/trash` 로 쓰레기 위치 저장.
6. 동일 쓰레기 반복 등록 시 중복 검사로 1건만 생성(`duplicate: true` 응답).
7. `POST /api/trash/{id}/verify` 로 정화 검증 후 `cleaned` 상태와 점수 지급.
8. `POST /api/plogging/sessions/{id}/finish` 로 세션 종료 후 통계 집계.
9. `GET /api/plogging/sessions/{id}/report` 로 리포트 데이터 반환.
10. `GET /api/map/trash` 로 영역 내 쓰레기 조회.
11. `GET /api/users/me/statistics` 로 누적 통계 반환.
12. Batch 재전송/네트워크 끊김 상황에서 데이터가 유실되지 않음(멱등 처리).

## 테스트 전략 (제안)

- **단위 테스트**: 서비스 계층(`*_service`), 유틸(`geo`, `dedup`).
- **통합 테스트**: API 엔드포인트 + 테스트 DB(PostGIS) 사용.
- **명세 테스트**: Pydantic 스키마 기반 요청/응답 검증.
- **Mock AI 테스트**: `AI_MODE=mock` 환경에서 전 시나리오 실행 가능.
- 테스트는 `pytest` + `httpx`(ASGI) 권장.