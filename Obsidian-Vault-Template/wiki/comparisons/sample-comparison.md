# Sample Comparison (전통적 메모 vs LLM Wiki)

## 개요 및 목적
본 문서는 전통적인 폴더/태그 기반 메모 시스템과 **Karpathy 스타일의 AI 에이전트 연동 컴파일형 LLM Wiki** 간의 구조적 차이와 지식 복리 효율성을 평면 비교 분석합니다.

## 상세 비교 매트릭스

| 비교 기준 | 전통적 메모 시스템 (Notion/일반 옵시디언) | LLM Wiki (컴파일형 지식 베이스) |
| :--- | :--- | :--- |
| **지식 계층 구조** | 단일 계층 (메모 덤프) | 2계층 분리 (`raw/` 불변 원본 vs `wiki/` 정제 지식) |
| **요약 및 색인** | 사용자가 수동 작성 | AI 에이전트 직접 정독 후 수동 집필 + `build.py` 자동 색인 |
| **지식 유실 방지** | 이전 내용 덮어쓰기 위험 | 누적 결합(Compounding) 및 주간 복리 원장 추적 |
| **세션 연동** | 별도 툴 분리 | Claude/Antigravity 대화 로그 및 계획서 1:1 미러링 |
| **할루시네이션 가드** | 없음 | 내부 실무(Internal) vs 외부 오픈소스(External) 이원화 서술 |

## 결론 및 권장 아키텍처
장기적인 연구 개발 및 커리어 관리를 위해서는 AI 에이전트가 직접 정독하여 5대 카테고리(`concepts`, `entities`, `comparisons`, `synthesis`, `queries`)로 정제·누적하는 LLM Wiki 구조가 압도적으로 높은 지식 재사용성과 복리 효과를 제공합니다.

## 관련 링크
* [[sample-concept.md|Sample Concept]]
* [[Weekly-Knowledge-Compounding-Ledger.md|주간 지식 복리 기록]]

<!-- ONE_LINE_SUMMARY: 전통적 메모 방식 대비 LLM Wiki 구조의 2계층 분리 및 컴파일형 지식 복리 우수성 비교 -->
