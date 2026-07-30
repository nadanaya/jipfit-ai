# Figma 핸드오프

Figma 링크와 편집 권한이 제공되지 않아 실제 프레임은 수정하지 않았다. 아래 명세는 현재 Streamlit MVP를 발표자료·고도화 UI로 옮길 때 사용한다.

## 페이지와 프레임

### 01_Input / Desktop 1440

- 상단 브랜드 카드: 서비스명, 태그라인, 팀명
- 3열 입력 카드: 사용자 조건 / 지역·가구 / 집 비용
- 정책 조건 체크박스 3개
- 전체 너비 Primary 버튼

### 02_Result / Desktop 1440

- KPI 카드 4개
- 좌측 AI 위험 카드와 확률 차트
- 우측 현금흐름 차트
- 정책 후보 테이블
- 정책 아코디언 상세
- 다음 행동 3개와 고지문

### 03_Mobile / 390

- 모든 3열·4열을 1열로 적층
- 표는 카드 목록으로 변환
- 공식 페이지 버튼은 44px 이상 높이

## 컴포넌트 상태

- Button: Default / Hover / Disabled / Loading
- Input: Default / Focus / Error / Filled
- Risk badge: Stable / Caution / Risk
- Policy card: Passed / Manual Check / Low Priority
- Notice: Info / Warning / Legal disclaimer

## 접근성

- 텍스트 대비 WCAG AA 목표
- 위험을 색상만으로 표현하지 않고 문구·아이콘 병행
- 금액은 원 또는 만원을 명시
- 링크 목적을 `공식 정보 확인`으로 구체화
