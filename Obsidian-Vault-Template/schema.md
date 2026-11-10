# LLM Wiki Schema & Rules (schema.md)

이 문서는 이 옵시디언 볼트를 **Karpathy 스타일 LLM Wiki** 구조로 운영하기 위해 준수해야 할 위키 구조 규칙과 페이지 타입 명세를 기술합니다.

## 1. 디렉터리 구조 및 역할 (Directory Structure)

* `README.md` - 볼트 전체의 유일한 메인 대시보드입니다. `python "wiki/build.py"`에 의해 카테고리별 문서 통계와 주요 진입점 링크가 자동 갱신됩니다. (`wiki/README.md`, `wiki/overview.md`는 단일화를 위해 폐기됨)
* `AGENTS.md` - 에이전트가 준수해야 할 7대 핵심 원칙과 전용 규칙/스킬 포인터를 관리하는 최상위 운영 인덱스입니다.
* `purpose.md` - 위키 지식 베이스의 목적, 핵심 질문, 연구 범위를 기술한 최상위 설계 문서입니다.
* `schema.md` - [본 문서] 위키의 구조적 규칙과 페이지 타입 명세를 기술합니다.
* `.agents/` - 에이전트 전용 규칙(`rules/`) 및 표준 작업 스킬(`skills/`) 보관소입니다.
  - `.agents/rules/` - `wiki_ingestion_rule.md`, `owner_rule.md`, `core_system_rule.md`
  - `.agents/skills/` - `llm_wiki_compiler`, `wiki_qa`, `scrum_report`, `sources_classifier`, `linkedin_ingestion`
* `raw/` - 인제스트 대상이 되는 원본 데이터 보관소입니다. (불변 상태로 유지)
  - `raw/sources/` - 업로드 및 수집된 원본 마크다운 파일들의 백업 복사본입니다 (`0-Inbox`, `1-Projects`, `2-Areas`, `3-Resources`, `4-Archives`). 원래의 계층 구조를 보존하여 복사됩니다.
  - `raw/assets/` - 본문 내에 삽입되는 이미지, 도면 등 로컬 리소스 보관소입니다.
* `wiki/` - 에이전트가 직접 분석하고 가공한 컴파일형 지식망입니다.
  - `wiki/build.py` - `README.md`, `wiki/index.md`, `wiki/log.md` 및 주간 복리 원장 통계를 일괄 갱신하는 공식 컴파일러 스크립트입니다.
  - `wiki/index.md` - 콘텐츠 카탈로그로, 6대 섹션(`Queries`, `Synthesis`, `Comparisons`, `Concepts`, `Entities`, `Sources`) 문서의 전체 목록과 한 줄 요약을 관리합니다.
  - `wiki/log.md` - 전체 위키 문서를 날짜(내림차순) 및 중요도(`monthly` ➔ `daily` ➔ `5대 지식` ➔ `기타`) 순으로 자동 정렬한 타임라인 색인(`Timeline Log`)입니다.
  - `wiki/Weekly-Knowledge-Compounding-Ledger.md` - 매주 도출된 5대 카테고리 지식 번들과 주요 ADR(Architecture Decision Records) 진화 과정을 주차별로 누적 추적하는 공식 주간 지식 복리 원장입니다.
  - `wiki/sources/` - 원본 문서의 요약본 및 출처 기록 페이지(`src-<파일명>.md`)가 `raw/sources/`와 1:1 동격 경로로 미러링 저장됩니다.
  - `wiki/concepts/` - 이론, 방법론, 기술 기법 지식을 복리(compounding) 축적하는 개념 페이지입니다.
  - `wiki/entities/` - 인물(`소유자.md`), 기업(`회사명.md`), 시스템(`Core-System.md`), 도구/라이브러리 정보를 복리 축적하는 실체 페이지입니다.
  - `wiki/queries/` - 리서치 및 트러블슈팅 시 생성된 정밀 문제 해결 가이드 및 질의 결과물 보관소입니다.
  - `wiki/synthesis/` - 여러 소스 파일 간의 종합적인 지식 융합 분석 문서가 축적됩니다.
  - `wiki/comparisons/` - 대조적 아키텍처, 기법 및 라이브러리 간의 상세 평면 비교 분석 문서가 축적됩니다.

---

## 2. 페이지 타입 명세 (Page Type Specs)

### 2.1. 자료 요약 페이지 (wiki/sources/.../src-<파일명>.md)
* `raw/sources/` 하위 원본 경로와 1:1로 일치하는 디렉터리에 `src-<파일명>.md` 이름으로 생성합니다.
* 상단에는 반드시 원본 파일로 통하는 상대 경로 링크를 작성합니다. (예: `소스: [[raw/sources/0-Inbox/document.md]]`)
* 중간에는 본문의 핵심 아키텍처, 기술 원리, 핵심 변경 내역을 구조화하여 요약합니다.
* 하단에는 색인 자동화 파싱을 위한 `<!-- ONE_LINE_SUMMARY: <한 줄 요약> -->` 주석을 반드시 주입합니다.

### 2.2. 개념 및 실체 페이지 (wiki/concepts/ 및 wiki/entities/)
* 페이지 최상위 제목은 `# <개념/실체명>` 으로 지정합니다.
* `## 정의 및 설명` 및 `## 핵심 특징 및 기술 사양` 하위에 백엔드 동작 및 인프라 사양 중심의 구조화된 본문을 작성하며, 다른 위키 문서 언급 시 반드시 `[[위키링크]]` 형식을 적용합니다.
* `## 실무 적용 사례 및 유즈케이스` 섹션은 반드시 다음 두 소목차로 **이원화 분리**하여 서술합니다:
  1. `### 1. 사용자 자체 실무 적용 사례 (Internal Practice)`: `Work-Logs/`, `chats/`, `plans/`에서 입증된 사내 실제 구현 이력만 기재하며, 미적용 외부 기술은 `'사내 시스템 직접 적용 이력 없음 (외부 참고 기술)'`으로 명시합니다 (할루시네이션 절대 금지).
  2. `### 2. 오픈소스/GitHub 실무 유즈케이스 (External OSS Use-Cases)`: 외부 오픈소스 저장소 및 연구 레퍼런스의 권장 아키텍처와 벤치마크 유즈케이스를 기술합니다.
* `## 관련 링크` 하위에 연관된 타 개념/실체 목록을 불릿 형태로 관리하며, 새로운 지식 유입 시 누적하여 병합(Merge)합니다.
* 문서 최하단에는 `<!-- ONE_LINE_SUMMARY: <한 줄 요약> -->` 주석을 반드시 포함합니다.

### 2.3. 비교, 종합 분석 및 질의 페이지 (wiki/comparisons/, wiki/synthesis/, wiki/queries/)
* 비교 분석(Comparisons) 페이지는 상이한 도구/아키텍처/알고리즘(예: 외부 오픈소스 파서 vs 자체 구현 파서, LLM 직접 추론 vs 격리형 실행 엔진)을 정량 지표 표, 장단점 분석, 아키텍처 대조의 형태로 비교합니다.
* 종합 분석(Synthesis) 페이지는 월간/주간 R&D 진화 리포트 및 종합 트렌드 분석을 통해 시간 경과에 따른 5대 지식 번들과 ADR 진화 과정을 총망라합니다. (전체 주차별 누적 원장은 최상위 원장인 **[[wiki/Weekly-Knowledge-Compounding-Ledger.md|주간 지식 복리 기록]]**에서 통합 관리)
* 질의 답변(Queries) 페이지는 엔지니어링 트러블슈팅 및 핵심 아키텍처 해결 가이드를 기록합니다.
* 모든 비교/종합/질의 페이지 하단에도 `<!-- ONE_LINE_SUMMARY: <한 줄 요약> -->` 주석을 필히 기입합니다.

---

## 3. 지식 병합 규칙 (Compounding Rule)
* 기존에 동일한 파일명의 개념/실체 마크다운 파일이 존재할 경우, **기존 본문을 절대 덮어쓰기하여 날리지 않고, 새로 추가된 문맥 정보와 링크 목록을 기존 텍스트 하단에 유기적으로 결합하여 개편**합니다.
* 병합 시에는 1) 기술적 정의 비교 및 정제, 2) 세부 특징 누적, 3) 모순점(Contradiction) 유무 검출 및 경고 삽입, 4) 교차 위키링크 목록 취합 순서로 컴파일을 고도화하여 정보 유실을 완전히 방지합니다.
