# LLM Wiki Ingestion & Compounding Rules (wiki_ingestion_rule.md)

이 문서는 옵시디언 볼트를 Karpathy 스타일 LLM Wiki로 운영하기 위한 에이전트의 상세 인제스트(Ingest), 지식 누적 병합(Compounding), 디렉터리 미러링(Mirroring) 및 문서 템플릿 수칙을 정의합니다.

---

## 1. 디렉터리 구조 (Directory Structure)

* **Raw Sources (원본 자료 - Immutable)**:
  * `0-Inbox/`, `1-Projects/`, `2-Areas/`, `3-Resources/`, `4-Archives/`, `Concepts/`
* **The Wiki (생성형 위키)**:
  * `README.md` - 메인 대시보드
  * `wiki/index.md` - 위키 문서 전체 색인
  * `wiki/log.md` - 시간순 작업 일지 (append-only)
  * `wiki/sources/` - 원본 요약본 (`src-<파일명>.md`)
  * `wiki/concepts/` - 개념 페이지 (`<개념명>.md`)
  * `wiki/entities/` - 실체 페이지 (`<실체명>.md`)
  * `wiki/comparisons/` - 기술 비교 보고서
  * `wiki/synthesis/` - 종합 리포트
  * `wiki/queries/` - 저장된 질의 및 문제 해결 가이드

---

## 2. 인제스트 2단계 사고 사슬 (CoT Operations)

### 작업 요청 유형별 트리거 (Trigger Types)
* **스크럼/스타 저장 요청**: `raw/sources/0-Inbox/` 원본 파일들을 분석해 `wiki/sources/.../src-<파일명>.md` 요약본 1:1 디렉터리 미러링 생성.
* **인사이트 추출 요청**: 요약본들을 토대로 `wiki/concepts/` 및 `wiki/entities/` 지식 문서를 신규 생성하거나 누적 병합(Compounding).
* **대화록 및 계획서 분석**: `chats/`와 `plans/`를 집중 분석하여 비교, 종합, 저장된 질의 지식을 도출 및 상호 양방향 링크 매핑(`[[...]]`).

### 1단계: 분석 (Analysis)
1. **목적 부합성**: `purpose.md`의 범위에 따라 핵심 지식 판단.
2. **요약 추출**: 핵심 요약 2-3문단 및 1문장 주석(`<!-- ONE_LINE_SUMMARY: <요약> -->`) 작성.
3. **개념/실체 추출**: 이론/패러다임 및 핵심 도구/조직 추출.
4. **모순 및 보완 검사**: 기존 위키 내용과 대조 및 모순 해소.

### 2단계: 생성 및 병합 (Generation & Merge)
* **원본 요약문**: 상단에 상대 경로 링크(`소스: [[0-Inbox/document.md]]`) 명시, 하단에 `ONE_LINE_SUMMARY` 주석 주입.
* **누적 병합 (Compounding)**: 기존 파일 존재 시 절대 덮어써서 유실시키지 않고 신규 지식을 유기적으로 하단에 누적 결합.
* **스크립트 자동 집필 전면 금지**: 파이썬/쉘 스크립트로 마크다운 텍스트를 대량 자동 생성하는 행위 엄금. 오직 AI 에이전트가 `view_file`로 수동 정독 후 직접 집필. 스크립트는 최종 `python "wiki/build.py"` 컴파일에서만 사용.
* **상투어 및 미완성 템플릿 변수 금지**: 껍데기 텍스트(`{title}` 등) 주입 금지.
* **사용자 실무 사례 할루시네이션 금지**: 사내 실무 사례(`Internal Practice`)에는 오직 `Work-Logs/`, `chats/`, `plans/`에 입증된 성과만 기재. 근거 없는 외부 기술은 '사내 시스템 직접 적용 이력 없음 (외부 참고 기술)'으로 서술.
* **실무 사례 이원화 분리**: `1. 사용자 자체 실무 적용 사례 (Internal Practice)`와 `2. 오픈소스/GitHub 실무 유즈케이스 (External OSS Use-Cases)` 소목차로 분리 서술.
* **주간 지식 복리 기록(Ledger) 동기화**: 주간/정기 지식 복리 완필 시 `[[wiki/Weekly-Knowledge-Compounding-Ledger.md|주간 지식 복리 기록]]`의 2절 타임라인 색인 표(`Weekly Index`) 및 3절 상세 기록(`Chronological Ledger`) 최상단에 해당 주차의 5대 지식 번들, ADR 번호 및 핵심 마일스톤을 누적 기록.

---

## 3. wiki/sources 디렉터리 미러링 & 동기화 규칙

* **0-Inbox 우선 적재**: 신규 소스는 먼저 `raw/sources/0-Inbox/`에 적재.
* **1:1 경로 미러링**: `raw/sources/` 하위 경로와 `wiki/sources/` 하위 경로를 1:1로 동일하게 유지.
  * 예: `raw/sources/2-Areas/Work-Logs/log.md` ➔ `wiki/sources/2-Areas/Work-Logs/src-log.md`
* **이동 동기화**: 원본 파일이 `0-Inbox/`에서 `1-4/`로 이동 시 요약본도 매칭 디렉터리로 즉각 이동 동기화 (구 경로 파일 삭제).

---

## 4. 개념/실체 표준 문서 작성 템플릿

```markdown
# <개념 또는 실체명>

## 정의 및 설명
(백엔드 동작 및 인프라 사양 중심의 명확한 상세 설명. 다른 개념 언급 시 [[위키링크]]로 연결)

## 핵심 특징 및 기술 사양
1. **특징 1**: 설명...
2. **특징 2**: 설명...

## 실무 적용 사례 및 유즈케이스

### 1. 사용자 자체 실무 적용 사례 (Internal Practice)
* **사내 시스템 / 업무 일지 사례**: (Work-Logs, chats, plans에서 입증된 실제 적용 성과만 작성. 미적용 시 '사내 시스템 직접 적용 이력 없음 (외부 참고 기술)'으로 명시)

### 2. 오픈소스/GitHub 실무 유즈케이스 (External OSS Use-Cases)
* **GitHub 레포지토리 / 오픈소스 사례**: (github-stars 등에서 도출된 공식 권장 아키텍처 및 유즈케이스)

## 관련 링크
* [[개념/실체 링크1]]
* [[개념/실체 링크2]]

<!-- ONE_LINE_SUMMARY: <개념 또는 실체에 대한 1문장 핵심 요약> -->
```
