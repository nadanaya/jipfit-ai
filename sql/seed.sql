INSERT OR REPLACE INTO regions (region_code, region_name, demo_cost_index, note) VALUES
('SEOUL', '서울', 1.35, '데모용 상대지수이며 실거래 시세가 아님'),
('GYEONGGI', '경기', 1.15, '데모용 상대지수이며 실거래 시세가 아님'),
('INCHEON', '인천', 1.08, '데모용 상대지수이며 실거래 시세가 아님'),
('BUSAN', '부산', 1.02, '데모용 상대지수이며 실거래 시세가 아님'),
('DAEGU', '대구', 0.93, '데모용 상대지수이며 실거래 시세가 아님'),
('DAEJEON', '대전', 0.98, '데모용 상대지수이며 실거래 시세가 아님'),
('GWANGJU', '광주', 0.91, '데모용 상대지수이며 실거래 시세가 아님'),
('ULSAN', '울산', 0.94, '데모용 상대지수이며 실거래 시세가 아님'),
('SEJONG', '세종', 1.00, '데모용 상대지수이며 실거래 시세가 아님'),
('GANGWON', '강원', 0.84, '데모용 상대지수이며 실거래 시세가 아님'),
('CHUNGBUK', '충북', 0.86, '데모용 상대지수이며 실거래 시세가 아님'),
('CHUNGNAM', '충남', 0.87, '데모용 상대지수이며 실거래 시세가 아님'),
('JEONBUK', '전북', 0.80, '데모용 상대지수이며 실거래 시세가 아님'),
('JEONNAM', '전남', 0.78, '데모용 상대지수이며 실거래 시세가 아님'),
('GYEONGBUK', '경북', 0.82, '데모용 상대지수이며 실거래 시세가 아님'),
('GYEONGNAM', '경남', 0.86, '데모용 상대지수이며 실거래 시세가 아님'),
('JEJU', '제주', 1.04, '데모용 상대지수이며 실거래 시세가 아님');

INSERT OR REPLACE INTO policies (
    policy_id, name, category, description, rule_mode,
    official_url, verified_at, source_note, is_active
) VALUES
('YOUTH_MONTHLY_RENT_2026', '청년월세 지원사업', '주거비지원', '부모와 별도 거주하는 청년의 월세 부담을 낮추는 지원사업', 'screening', 'https://www.myhome.go.kr/hws/portal/dgn/selectSelfDiagnosisYouthHousView.do', '2026-07-29', '2026년 마이홈 자가진단 기준을 단순화한 사전진단', 1),
('HAPPY_HOUSING_YOUTH_2026', '행복주택 청년계층', '주택공급', '청년·대학생·사회초년생 등을 위한 공공임대주택', 'screening', 'https://m.myhome.go.kr/hws/portal/cont/selectHappyHouseView.do', '2026-07-29', '2026년 소득·자산 기준을 단순화한 사전진단', 1),
('YOUTH_JEONSE_LOAN', '청년버팀목전세자금', '금융지원', '청년의 전세보증금 마련을 돕는 주택도시기금 대출', 'discovery', 'https://www.myhome.go.kr/hws/portal/cont/selectYouthPolicyContRentalView.do', '2026-07-29', '실제 한도·금리는 공식 심사 필요', 1),
('YOUTH_DEPOSIT_RENT_LOAN', '청년전용 보증부월세대출', '금융지원', '보증금과 월세를 함께 부담하는 청년을 위한 주택도시기금 대출', 'discovery', 'https://www.myhome.go.kr/hws/portal/cont/selectYouthPolicyWarrantyMonthlyLoanView.do', '2026-07-29', '상세 소득·주택요건은 공식 페이지에서 재확인', 1),
('YOUTH_GUARANTEE_FEE', '청년 보증료 지원', '금융연계', '전세보증금 반환보증의 보증료 부담을 낮추는 지원', 'discovery', 'https://m.myhome.go.kr/hws/mbl/cont/selectYouthPolicyGuaranteeFeeSupView.do', '2026-07-29', '지역·연령·소득 조건이 달라 공식 공고 확인 필요', 1);
