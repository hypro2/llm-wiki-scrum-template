---
name: llm_wiki_compiler
description: 과거 업무 일지, 기술 노트, GitHub Star 스크랩 저장소를 분석하여 고품질의 지식 복리형 LLM Wiki(concepts, entities, comparisons, synthesis, queries) 문서를 집필하고 업데이트하는 스킬
---

# LLM Wiki Compiler Skill

본 스킬은 볼트 내의 구형 R&D 지식, 주간 업무일지, 기술 블로그 요약본 및 **GitHub Star 스크랩 저장소(`raw/sources/0-Inbox/github-stars/`)**를 탐색하여 의미가 누적 및 충돌 해결되는 [Karpathy 스타일](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)의 고도화된 위키(Wiki) 문서를 집필하고 복리 연결망을 매핑하기 위한 에이전트 전용 스킬 지침입니다.

---

## 1. 지식 탐색 및 식별 규칙

1. **과거 히스토리 추적**:
   - `raw/sources/2-Areas/Work-Logs/`, `Work-Summaries/`, `0-Inbox/chats/`, `0-Inbox/plans/`, `0-Inbox/github-stars/`, `3-Resources/github-stars/`, `3-Resources/Technical-Notes/linkedin_posts/`에 기재된 날짜별 트러블슈팅, 기술 스크랩 이력을 정독합니다.
   - 단편적인 '완료사항' 단어를 넘어 그 이면에 탑재된 기술적 핵심 원리를 포착합니다.
2. **트레이드오프 및 벤치마크 추출**:
   - 프레임워크 대조(FastAPI vs Flask, vLLM vs llama.cpp, 외부 오픈소스 파서 vs 자체 파서, LLM 직접 연산 vs 격리형 SQL 엔진), 선호도 정렬 기법(DPO vs GRPO) 등 고민 및 성능 벤치마크 지표(F1, Recall, Latency)를 색인합니다.

---

## 2. 깃허브 스타(GitHub Stars) 저장소 위키 수집 SOP & 베스트 프랙티스

### 2.1. 실수 사례 및 반면교사 (Bad Practices to Avoid) ⚠️

1. **[CRITICAL] 파이썬/쉘 스크립트 기반 마크다운 텍스트/템플릿 대량 자동 생성 (Mass Text Generation Anti-Pattern)**:
   - **잘못된 행위**: 파이썬 정규식이나 단순 문자열 포맷팅 스크립트로 README 원본을 일괄 치환하여 `src-*.md` 파일 수십~수백 개를 대량 파이썬 스크립트로 자동 집필하는 행위.
   - **참혹한 결과**: 백엔드 알고리즘, 수식, 세부 아키텍처 맥락이 전부 거세되고 `{title}`, `{definition}` 등 미완성 정규식 껍데기/상투 텍스트만 가득 찬 저품질 요약본이 양산되어 전량 파기 후 재작성하는 심각한 리소스 낭비 발생.
2. **[CRITICAL] 수동 정독 작성을 회피하려는 편법/태만**:
   - 처리해야 할 raw 저장소 파일 수가 많다는 이유(예: 수십 개 이상)로 2~3개만 작성하고 중단하려 하거나 스크립트로 우회하려는 시도. AI 에이전트는 `/goal` 모드를 적극 활용하여 전체 대상에 대해 직접 `view_file`로 100% 수동 정독·추론 및 집필을 완수해야 함.
3. **[CRITICAL] raw 경로 불일치 및 미러링 미준수**:
   - 원본 파일이 `raw/sources/0-Inbox/github-stars/`에 위치함에도 요약본을 `wiki/sources/` 루트에 난잡하게 적재하거나 상대경로 위키링크(`[[raw/sources/...]]`)를 누락하는 행위.
4. **[CRITICAL] 사용자 실무 적용 사례 지어내기/할루시네이션 전면 엄금 (Anti-Hallucination Rule)**:
   - **잘못된 행위**: 외부 기술/오픈소스 저장소(예: 오픈소스 OCR, 문서 파서, 동적 설정 도구 등)를 분석하면서, `Work-Logs/`, `chats/`, `plans/`에 직접적인 구현 근거가 없는 기술을 "사용자가 사내 시스템에 직접 적용했다"라고 지어내거나 추측하여 `1. 사용자 자체 실무 적용 사례 (Internal Practice)`에 작성하는 행위.
   - **엄격한 행동 지침**: `Internal Practice` 항목에는 오직 볼트 내 `Work-Logs/`, `chats/`, `plans/`에서 직접적으로 입증된 실제 구현 이력(예: 자체 프로덕션 AI 서비스, 문서 파싱 파이프라인, 클러스터링/분류 모델 등)만 작성할 수 있으며, 이외의 사내 미적용 기술은 **`사내 시스템 직접 적용 이력 없음 (외부 오픈소스/연구 기술 자료)`**으로 명확히 구분하여 사실만을 기록해야 함.

### 2.2. 성공 사례 및 베스트 프랙티스 (Best Practices) ✅

1. **[SOP 1] AI 에이전트 1:1 수동 정독 및 심층 마크다운 수동 집필**:
   - AI 에이전트가 직접 `view_file` 도구로 각 raw README 마크다운을 정독하고 추론(Reasoning)하여, 시니어 엔지니어 관점의 백엔드 아키텍처, 3대 핵심 기능, 실무 유즈케이스, 1문장 주석(`<!-- ONE_LINE_SUMMARY -->`) 및 원본 상대링크(`[[raw/sources/...]]`)를 포함해 `write_to_file`로 직접 마크다운 집필.
2. **[SOP 2] 1:1 디렉터리 미러링 (Directory Mirroring)**:
   - 원본 마크다운 파일 경로(`raw/sources/0-Inbox/github-stars/<파일명>.md`)와 1:1로 정확히 응하는 동격 디렉터리 구조(`wiki/sources/0-Inbox/github-stars/src-<파일명>.md`)에 생성 및 관리.
3. **[SOP 3] 5대 카테고리 지식 복리 병합 (Compounding)**:
   - 요약본 수집 완필 후, 핵심 기술 원리와 도구를 도출해 기존 `wiki/concepts/`, `wiki/entities/`, `wiki/comparisons/`, `wiki/synthesis/`, `wiki/queries/` 지식 문서 상에 덮어쓰기 유실 없이 **점진적 누적 결합(Compounding)** 및 신규 생성.
4. **[SOP 4] 최종 스크립트 컴파일 분리**:
   - 마크다운 텍스트 집필 단계에서는 스크립트를 절대 가동하지 않고, 모든 문서의 수동 집필이 100% 끝난 최종 단계에서만 `python "wiki/build.py"`를 터미널에서 실행하여 인덱스(`index.md`), 대시보드(`README.md`), 일지(`log.md`)를 일괄 컴파일.

---

## 3. 위키 문서 유형별 집필 가이드라인

### 3.1. 개념(Concepts) 및 실체(Entities) 지식 빌드

* **정의 및 설명**: 단순 단어 풀이가 아닌 시니어 엔지니어링 관점의 백엔드 동작 및 인프라 사양을 서술합니다.
* **핵심 특징**: 3~4개의 명확한 구조화된 요소를 수식($W_0 + B \times A$ 등) 혹은 아키텍처 원리를 포함해 설명합니다.
* **실무 적용 사례의 이원화 분리 (CRITICAL RULE)**:
  - 개념 및 실체 문서 집필 시, **사용자 본인이 수행한 사내/개인 실무 사례**와 **외부 깃허브 오픈소스 저장소의 실무 유즈케이스**를 섞지 말고 다음과 같이 소목차로 **명확히 분리하여 기술**합니다:
    1. **사용자 자체 실무 적용 사례 (Internal Practice)**: `Work-Logs/`, `chats/`, `plans/` 등 업무 일지/계획서에 기록된 실제 시스템 적용 성과만 작성 (예: 자체 프로덕션 RAG 시스템, 문서 전처리 파이프라인, 클러스터링/분류 모델 등). **실제 수행 기록이 없는 외부 기술은 절대 사용자가 직접 구현했다고 지어내지 말고 '사내 시스템 직접 적용 이력 없음 (외부 참고 기술)'으로 명시할 것.**
    2. **오픈소스/GitHub 실무 유즈케이스 (External OSS Use-Cases)**: `github-stars/` 등에 수집된 깃허브 레포지토리의 공식 적용 권장 아키텍처 및 오픈소스 프로젝트 유즈케이스 (예: 공개 문서 파서 벤치마크, KV-Cache 양자화 서빙 아키텍처 등).

### 3.2. 비교(Comparisons) 및 종합(Synthesis) 리포트 빌드
* **이중 매핑 비교**: 단순 장단점 나열을 배제하고 VRAM 메모리, 동시성 처리 성능, 인프라 비용 등의 기술적 평면 대조 테이블을 포함시킵니다 (예: 오픈소스 PDF 파서 5종 벤치마크 비교).
* **종합 보고서**: 흩어진 기술 노트를 연결하여 최신 AI Agent 및 RAG 스택 트렌드 같은 완성형 리포트로 정제합니다.

### 3.3. 저장된 질의(Queries) 빌드
* 개발 과정이나 레포지토리에서 다루는 크리티컬한 이슈(예: "RAG 시스템에서 토큰 비용과 컨텍스트 노이즈를 어떻게 최적화하는가?")의 상황, 원인, 해결책 가이드를 질의 문서로 신설합니다.

---

## 4. 중복 생성 방지 및 지식 추출 규칙

* **이미 존재하는 지식의 신규 생성 금지**:
  - 문서를 작성하기 전에 반드시 `wiki/concepts/`, `wiki/entities/`, `wiki/comparisons/`, `wiki/synthesis/`, `wiki/queries/` 디렉토리에 동일하거나 유사한 파일명/내용을 지닌 문서가 이미 존재하고 있는지 우선 확인합니다.
* **5대 카테고리의 균형 있는 지식 추출**:
  - 개념(Concepts), 실체(Entities), 비교(Comparisons), 종합(Synthesis), 저장된 질의(Queries)의 5대 카테고리에 맞게 균형을 이루도록 설계 및 분석하여 누락 없이 골고루 도출해 냅니다.
* **[CRITICAL] 기존 정보 덮어쓰기 유실 절대 금지**:
  - 개념/실체 지식을 병합하거나 종합(Synthesis) 인사이트를 생성/업데이트할 때, 기존 본문에 기록된 상세 정의, 핵심 특징, 관련 코드나 세부 사례 목록을 단순히 덮어쓰기하여 날리지 않고 누적 결합합니다.
* **한 줄 요약 주석 주입 (ONE_LINE_SUMMARY)**:
  - 새로 생성하거나 보강하는 모든 위키 문서 하단에는 반드시 `<!-- ONE_LINE_SUMMARY: <설명> -->` 주석을 필히 기입합니다.

---

## 5. 에이전트 위키 작업 프로토콜 (스크럼/스타 저장 및 인사이트 추출)

* **"스크럼 위키 저장" 또는 "깃허브 스타 위키 저장" 요청 시 동작 규칙**:
  - `raw/sources/0-Inbox/` 하위의 원본 파일들(`chats`, `plans`, `github-stars` 등)을 AI 에이전트가 직접 정독하여 1:1 매칭되는 디렉터리 경로(`wiki/sources/0-Inbox/.../src-<파일명>.md`)에 고품질 요약본을 수동 생성 및 갱신합니다.
* **"인사이트 추출" 및 "지식 복리" 요청 시 동작 규칙**:
  - 생성된 `wiki/sources/` 요약본들을 토대로 핵심 기술 원리 및 용어를 도출하여 `wiki/concepts/`, `wiki/entities/`, `wiki/comparisons/`, `wiki/synthesis/`, `wiki/queries/` 지식 문서를 신규 생성하거나 점진적 누적 병합(Compounding)합니다.
  - 이 때 실무 적용 사례 섹션은 **사용자 자체 실무 사례**와 **깃허브 오픈소스 유즈케이스**로 이원화 분리하여 집필합니다.
  - **[SOP 필수] 주간 지식 복리 기록 갱신**: 해당 주차의 핵심 마일스톤, 생성·병합된 5대 지식 번들(`Concepts`, `Comparisons`, `Synthesis`, `Queries`, `Entities`) 목록, ADR 번호 및 실무 성과를 `[[wiki/Weekly-Knowledge-Compounding-Ledger.md|주간 지식 복리 기록]]` 문서의 **2절 타임라인 색인 표(`Weekly Index`) 및 3절 주차별 상세 기록(`Chronological Ledger`) 최상단에 누적 기록(Prepend)**합니다.
* **최종 컴파일 실행**:
  - 모든 지식 집필 및 주간 지식 복리 기록 갱신 완필 후 `python "wiki/build.py"`를 가동해 인덱스(`wiki/index.md`), 메인 대시보드(`README.md`), 타임라인 로그(`wiki/log.md`) 및 원장 누적 통계를 최종 갱신합니다.
