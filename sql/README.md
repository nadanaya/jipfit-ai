# SQLite 산출물

## 파일

- `schema.sql`: 지역, 정책, 익명 분석 로그 테이블과 인덱스
- `seed.sql`: 17개 지역과 5개 정책 시드
- `queries.sql`: 대표 조회
- `tests.sql`: 외래키와 핵심 무결성 검증
- `validation-report.json`: 검증 실행 결과

## 검증

```bash
python scripts/validate_sqlite.py \
  --schema sql/schema.sql \
  --seed sql/seed.sql \
  --queries sql/queries.sql \
  --tests sql/tests.sql \
  --report sql/validation-report.json
```

검증은 메모리 DB와 트랜잭션 안에서 수행하고 마지막에 롤백한다.

## 안전성

앱 로그 저장은 `src/database.py`에서 `?` 파라미터 바인딩을 사용한다. 이름, 전화번호, 계좌번호, 상세주소를 저장하지 않는다.
