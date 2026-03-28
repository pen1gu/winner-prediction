# Web Demo 실행 방법

`/client` 폴더에 서버 DB 기반 웹 데모를 추가했습니다.

## 1) 사전 조건

- PostgreSQL 실행 중
- `server/config/settings.py`의 `database_url`이 현재 DB 환경과 일치
- 경기 데이터가 DB에 적재되어 있음

## 2) 실행

프로젝트 루트에서:

```bash
python client/demo_server.py
```

브라우저에서 아래 주소 접속:

- `http://127.0.0.1:8080`

## 3) 제공 API

- `GET /api/health`
- `GET /api/matches/latest?limit=10` (1~30)

## 4) 화면 기능

- 최근 경기 수 선택 후 조회
- 팀명, 스코어, 리그/라운드/일시/경기장
- xG, 점유율, 슈팅, 유효슈팅 요약 카드 표시
