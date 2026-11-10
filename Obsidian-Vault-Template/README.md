# Obsidian Vault LLM Wiki (README)

본 프로젝트 저장소는 **Karpathy 스타일 LLM Wiki** 구조로 운영되는 개인 지식 복리(Knowledge Compounding) 인프라입니다. AI 에이전트(Antigravity 등)가 원본 R&D 노트, 업무 일지, 스크럼 기록 및 깃허브 스타 수집 저장소를 정독하고 5대 카테고리 마크다운 지식 문서로 점진적 누적 결합(Compounding)을 수행합니다.

## 📊 디렉터리별 대시보드 통계 (Dashboard Statistics)

| 상위 디렉터리 | 파일 수 | 설명 |
| --- | --- | --- |
| [wiki/sources](wiki/sources) | 1 | 원본 요약본 및 출처 기록 (0-Inbox, 1-Projects, 2-Areas, 3-Resources 등) |
| [wiki/concepts](wiki/concepts) | 1 | 이론, 방법론 등 개념 문서 |
| [wiki/entities](wiki/entities) | 1 | 인물, 기업, 프로젝트, 도구 등 실체 문서 |
| [wiki/synthesis](wiki/synthesis) | 1 | 종합 분석 및 트렌드 리포트 |
| [wiki/comparisons](wiki/comparisons) | 1 | 기술, 개념 간 평면 비교 분석 |
| [wiki/queries](wiki/queries) | 1 | 트러블슈팅 및 쿼리 기록 |

### Sources 세부 디렉터리 통계

| 디렉터리 경로 | 파일 수 | 비고 |
| --- | --- | --- |
| sources/0-Inbox/ | 1 | 미분류, 신규 수집 스크랩 및 계획서 등 |
| sources/1-Projects/ | 0 | 프로젝트 관련 출처 문서 |
| sources/2-Areas/ | 0 | 주요 업무 영역 |
| └─ sources/2-Areas/Work-Logs/ | 0 | 일일/월간/전체 작업 로그 및 세션 기록 |
| └─ sources/2-Areas/Work-Summaries/ | 0 | 주간/분기 작업 요약본 |
| sources/3-Resources/ | 0 | 기술 참고 자료, 연구 리소스 |
| └─ sources/3-Resources/github-stars/ | 0 | GitHub Star 오픈소스 심층 분석 요약본 |
| └─ sources/3-Resources/Technical-Notes/Blog-Posts/ | 0 | 기술 블로그/아티클 출처 자료 |
| └─ sources/3-Resources/Technical-Notes/linkedin_posts/ | 0 | LinkedIn 기술 피드 및 웹 보강 요약본 |
| └─ sources/3-Resources/Learning-Materials/Graduate-Courses/ | 0 | 대학원 석사 과정 강의 및 연구 노트 |
| sources/4-Archives/ | 0 | 보관된 자료 |

## 🧠 주요 테마 분석 (Major Themes)

본 위키는 대형 언어 모델(LLM), RAG 파이프라인(Agentic RAG 등), AI 에이전트 구축 및 엔지니어링 지식을 중심으로 구성되어 있습니다. 특히 실무적인 트러블슈팅, 도구 비교 분석(Comparisons), 아키텍처 진화 기록이 지속적으로 축적(Compounding)됩니다.

## 🔗 위키 주요 진입점

- [소유자 (Project Owner)](wiki/entities/소유자.md): 볼트 소유자의 프로필, 커리어 이력 및 핵심 엔지니어링 역량을 관리하는 대표 실체 문서
- [주간 지식 복리 기록 (Weekly Compounding Ledger)](wiki/Weekly-Knowledge-Compounding-Ledger.md): 주차별 지식 복리 마일스톤, 생성·병합된 5대 카테고리 지식 번들 및 아키텍처 진화 원장
- [wiki/index.md](wiki/index.md): 전체 지식 문서 색인 및 한 줄 요약 목록
- [wiki/log.md](wiki/log.md): 타임라인 순 위키 변경 이력 로그
- [AGENTS.md](AGENTS.md): 에이전트 위키 컴파일 운영 규칙 및 스키마 명세
