# 런타임 스모크 테스트

## 확인 완료

- Python 소스 전체 컴파일
- 핵심 서비스 CLI 실행
- 모델 로드·확률 예측
- SQLite 초기화·시드·대표 쿼리·무결성
- Pytest 12개 통과

## 브라우저 UI 확인 상태

이 빌드 환경의 내부 Python 패키지 저장소에는 Streamlit 배포본이 없어 브라우저 서버를 직접 기동하지 못했다. `app.py` 문법 컴파일과 내부 서비스 호출은 통과했다.

사용자 환경에서는 다음 순서로 확인한다.

```bash
python -m pip install -r requirements.txt
python scripts/bootstrap.py
streamlit run app.py
```

UI 실행 여부는 제출 전 실제 Windows PC에서 한 번 더 확인해야 한다.
