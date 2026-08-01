"""B층 제2 확증분할 수집 (PLAN-031 §3 🔒사전등록 · PLAN-032 §5 설계 · 승인 2026-08-01).

**이 패키지의 유일한 존재 이유는 PLAN-031 §3의 포함·배제·표집 순서를 결정적으로 집행하는
것이다.** 규칙은 이 코드가 정하지 않는다 — 코드가 규칙과 어긋나면 코드가 틀린 것이다.

층위:
  `stream`  검색 스트림의 결정적 순서 (타이블록 보류 · k-way 합병 · dedup)
  `screen`  순수 판정 (I/O 없음 · reason 코드 동결)
  `family`  신규 출원번호 → DOCDB simple family (BigQuery)
  `biblio`  서지상세 원응답 파싱 (심사관 인용 · claim1 · 행정상태)
  `ledger`  스크리닝 원장 append·재개
  `report`  r 추정(Wilson CI)·데이터 프로파일
  `driver`  오케스트레이션·예산·정지
"""
