# 3. 데이터베이스 설계

## 개요

- **DBMS**: PostgreSQL
- **공간 확장**: PostGIS
- **ORM**: SQLAlchemy
- **마이그레이션**: Alembic — 모든 스키마 변경은 반드시 마이그레이션으로 관리

좌표 데이터는 PostGIS의 `POINT` 타입으로 저장하여 공간 쿼리(거리 계산, 영역 조회, 클러스터링)를 효율적으로 수행한다.

## 테이블 목록

1. `users` — 사용자
2. `plogging_sessions` — 플로깅 세션
3. `route_points` — 이동 경로 좌표
4. `trash_records` — 쓰레기 기록
5. `detection_logs` — 탐지 이력

---

## users

```text
id                  PK
email               UNIQUE, NOT NULL
password_hash       NOT NULL
nickname            UNIQUE, NOT NULL
total_distance       누적 이동 거리 (m)
total_duration       누적 활동 시간 (s)
total_cleaned_count  누적 정화 쓰레기 수
total_score          누적 점수
created_at
updated_at
```

### 비고

- `email`, `nickname`은 UNIQUE 제약 필요.
- `password_hash`는 평문 저장 금지. bcrypt 등으로 해시.
- 누적 통계 컬럼들은 쓰레기/세션 종료 시 서비스 계층에서 갱신.

---

## plogging_sessions

```text
id                  PK
user_id             FK → users.id
status              NOT NULL  (active | paused | completed | cancelled)
started_at
ended_at
duration_seconds
distance_meters
detected_count
cleaned_count
uncollected_count
total_score
start_latitude
start_longitude
end_latitude
end_longitude
created_at
updated_at
```

### status

| 상태 | 설명 |
| --- | --- |
| `active` | 진행 중 |
| `paused` | 일시정지 |
| `completed` | 정상 종료 |
| `cancelled` | 취소 |

### 비고

- `started_at`, `ended_at`, `duration_seconds`는 종료 처리 시 계산.
- `distance_meters`는 `route_points` 기반으로 이동 거리 합산.
- `detected_count` / `cleaned_count` / `uncollected_count`는 쓰레기 레코드 기반 집계.
- `total_score`는 정화 완료된 쓰레기 점수 합계.
- `start_*` / `end_*` 좌표는 `POINT`로도 저장하면 공간 쿼리 유리.

---

## route_points

```text
id           PK
session_id   FK → plogging_sessions.id
latitude
longitude
accuracy      GPS 정확도 (m)
sequence      좌표 순서
recorded_at
```

### PostGIS

좌표는 `POINT` 타입 컬럼(예: `geom GEOMETRY(POINT, 4326)`)으로도 저장한다.

```sql
ALTER TABLE route_points
  ADD COLUMN geom geometry(POINT, 4326)
  GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) STORED;
```

### 비고

- `sequence`는 세션 내 순서 보장용.
- 노이즈 필터링은 저장 전 서비스 계층에서 수행 (정확도/속도/점프 검사). 자세한 기준은 [05-policies.md](./05-policies.md) 참고.
- Batch 삽입을 지원해야 함 (모바일에서 모아 전송).

---

## trash_records

```text
id                PK
session_id         FK → plogging_sessions.id
user_id            FK → users.id
type               쓰레기 종류
status             상태 (detected | verification_pending | cleaned | not_cleaned | uncertain)
confidence         AI 신뢰도 (0~1)
latitude
longitude
location           PostGIS POINT
before_image_url
after_image_url
detected_at
cleaned_at
last_detected_at
detection_count
score
created_at
updated_at
```

### status

| 상태 | 설명 |
| --- | --- |
| `detected` | 탐지됨 |
| `verification_pending` | 검증 대기 (After 이미지 접수 후) |
| `cleaned` | 정화 완료 |
| `not_cleaned` | 미수거 |
| `uncertain` | 판단 불가 |

### 비고

- `type` 값: `can`, `plastic_bottle`, `paper_cup`, `vinyl`, `general`, `glass_bottle`, `bulky`.
- `confidence` 신뢰도 기준 `0.7` 이상만 등록.
- `location`은 PostGIS `POINT`로 저장하여 중복 검사(거리 8m 이하)와 환경지도 영역 조회에 사용.
- `detection_count`, `last_detected_at`은 중복 탐지 시 갱신 (새 레코드 생성 X).
- `score`는 정화 완료(`cleaned`) 시 점수 테이블 기반으로 계산하여 저장.

---

## detection_logs

```text
id              PK
trash_record_id  FK → trash_records.id
confidence
bounding_box     JSONB (x, y, width, height — 0~1 비율)
image_url
detected_at
```

### 비고

- bounding_box는 정규화된 비율(0~1)로 저장.
- 한 쓰레기 레코드에 여러 탐지 로그가 발생할 수 있음.
- 이미지는 파일 저장소(S3/로컬)에 저장하고 URL만 보관.

---

## 인덱스 (제안)

- `users(email)` UNIQUE
- `users(nickname)` UNIQUE
- `plogging_sessions(user_id, status)`
- `plogging_sessions(created_at)`
- `route_points(session_id, sequence)`
- `route_points` — `geom` GiST 인덱스
- `trash_records(session_id)`
- `trash_records(user_id)`
- `trash_records(status)`
- `trash_records` — `location` GiST 인덱스 (환경지도 영역 조회용)
- `trash_records(created_at)`
- `detection_logs(trash_record_id)`

```sql
CREATE INDEX idx_route_points_geom ON route_points USING GIST (geom);
CREATE INDEX idx_trash_records_location ON trash_records USING GIST (location);
```

## ERD (텍스트)

```text
users 1 ──── N plogging_sessions
                    │
                    └── N route_points
                    └── N trash_records ──── N detection_logs
users 1 ──────────── N trash_records (user_id)
```

## 마이그레이션 규칙

- 모든 스키마 변경은 Alembic 마이그레이션 스크립트로 생성.
- Auto-generate 후 반드시 검토(제약, 인덱스, PostGIS 컬럼).
- PostGIS 확장은 초기 마이그레이션에서 `CREATE EXTENSION IF NOT EXISTS postgis;` 로 활성화.