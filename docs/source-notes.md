# 데이터·정책 출처 메모

기준 확인일: **2026-07-29**

## 대회 주제

- 사용자 제공 PDF `★[제8회 AI Challenge] 현직자 Pick 주제 리스트.pdf`
- 선택 항목: 1번 `청년 주거 금융 도우미`
- 핵심 요구: 소득·자산·희망 지역 분석, 청년 금융지원·주거 금융정보 추천, 월세·관리비·생활비를 고려한 적정 주거비 제안

## 정책 정보

### 청년월세 지원사업

- 공식 자가진단: `https://www.myhome.go.kr/hws/portal/dgn/selectSelfDiagnosisYouthHousView.do`
- MVP에 반영한 2026년 공개 조건: 19~34세, 부모와 별도 거주, 청년가구 기준중위소득 60% 이하, 청년가구 총재산 1억 2,200만원 이하
- 원가구 소득·재산, 중복수혜, 임대차 조건은 수동 확인으로 남김

### 행복주택 청년계층

- 공식 설명: `https://m.myhome.go.kr/hws/portal/cont/selectHappyHouseView.do`
- MVP에 반영한 공개 조건: 만 19~39세, 혼인 중이 아닌 무주택자, 2026년 청년 총자산 2억 5,100만원, 자동차 4,542만원 기준
- 실제 세대 범위, 계층 증빙, 지역별 모집공고는 수동 확인

### 금융·보증 상품 탐색

- 청년 주거지원 분류: `https://www.myhome.go.kr/hws/portal/cont/selectYouthPolicyContRentalView.do`
- 청년전용 보증부월세대출: `https://www.myhome.go.kr/hws/portal/cont/selectYouthPolicyWarrantyMonthlyLoanView.do`
- 청년 보증료 지원: `https://m.myhome.go.kr/hws/mbl/cont/selectYouthPolicyGuaranteeFeeSupView.do`

## 데이터 한계

- 지역 주거비 지수는 UI·모델 파이프라인 검증을 위한 **데모 상대지수**다.
- 학습 데이터는 코드로 재생성되는 **합성 데이터**다.
- 정책 기준은 변경될 수 있으므로 실제 신청 전 공식 공고와 기관 심사가 우선한다.
