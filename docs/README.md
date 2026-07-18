# EcoLens Server Documentation

EcoLens 서버(백엔드) 개발 문서 모음입니다. 이 문서들은 EcoLens 서비스 개발 기획서 중 **서버/백엔드** 파트에 해당하는 내용을 정리한 것입니다.

## 문서 목록

| 문서 | 설명 |
| --- | --- |
| [01-overview.md](./01-overview.md) | 서비스 개요 및 백엔드 역할 |
| [02-architecture.md](./02-architecture.md) | 시스템 구조 및 기술 스택 |
| [03-database.md](./03-database.md) | 데이터베이스 설계 및 PostGIS 활용 |
| [04-api.md](./04-api.md) | REST API 설계 |
| [05-policies.md](./05-policies.md) | 위치 기록, AI 처리, 예외 처리 정책 |
| [06-roadmap.md](./06-roadmap.md) | 개발 순서 및 완료 조건 |
| [07-setup.md](./07-setup.md) | 개발 환경 구성 및 실행 가이드 |

## 대상 독자

- EcoLens 백엔드 개발자
- API를 연동하는 프론트엔드/모바일 개발자
- 인프라/DevOps 담당자

## 기술 스택 요약

- **언어/프레임워크**: Python, FastAPI
- **ORM/마이그레이션**: SQLAlchemy, Alembic
- **검증/직렬화**: Pydantic
- **인증**: JWT
- **데이터베이스**: PostgreSQL + PostGIS
- **AI 서비스**: YOLO 기반 객체 탐지, OpenCV 기반 전처리, Before·After 검증 (Mock 모드 지원)
- **개발 환경**: Docker Compose, GitHub Actions, `.env` 환경 변수