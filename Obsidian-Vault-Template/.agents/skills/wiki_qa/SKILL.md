---
name: wiki_qa
description: 위키 지식 베이스(concepts, entities, sources, comparisons, synthesis, queries)를 코딩 어시스턴트처럼 고속 grep 및 병렬 view_file로 탐색하여 근거 기반 답변을 즉시 제공하고, 사용자 요청 시에만 wiki/queries/ 지식으로 환류하는 Q&A 스킬
---

# Wiki QA & Knowledge Query Skill (wiki_qa)

본 스킬은 옵시디언 볼트 내 **Karpathy 스타일 LLM Wiki**(`wiki/` 디렉터리)에 누적된 지식(개념, 실체, 요약본, 비교 리포트, 종합 보고서, 저장된 질의)을 코딩 어시스턴트처럼 **고속 `git grep` + 핀포인트 병렬 `view_file`** 조합으로 정밀 탐색하여, 사용자 질문에 대해 명확한 백엔드 맥락과 수식/코드 원리를 바탕으로 근거 기반 답변을 즉시 제시하기 위한 전용 스킬 지침입니다.

---

## 1. 핵심 원칙 (Core Principles)

1. **코딩 어시스턴트 스타일 고속 탐색 (2-Turn Fast QA)**:
   - `wiki/index.md` 전체를 무식하게 여러 번 나눠 읽거나 파일을 하나씩 순차 열람하지 않습니다.
   - **Turn 1**: `git grep`으로 색인(`index.md`의 제목+한줄요약)과 핵심 카테고리 본문의 **정확한 줄 번호(Line Number)**를 0.1초 만에 타겟팅합니다.
   - **Turn 2**: 검출된 핵심 문서 3~5개(또는 대형 문서의 특정 줄 번호 구간)를 **한 턴에 병렬(`view_file` 동시 호출)**로 정독한 뒤 **즉시 답변을 출력**합니다.
2. **위키 근거 중심 답변 & 양방향 위키링크 출처 명시 (Evidence & Citation)**:
   - 추측이나 일반론에 의존하지 않고, 볼트 내 문서에서 확인된 사실과 기술 사양에 기반하여 답변합니다.
   - 답변 내 언급되는 주요 개념, 실체, 요약본은 반드시 위키링크(`[[wiki/concepts/<개념명>]]`, `[[wiki/entities/<실체명>]]`, `[[wiki/sources/...]]` 등) 형식으로 출처를 명시합니다.
3. **실무 사례 이원화 분리 & 할루시네이션 금지 (Anti-Hallucination)**:
   - **사용자 사내/자체 적용 사례(Internal Practice)**: `Work-Logs`, `chats`, `plans` 등 실제 볼트에 기록된 이력만 언급하며, 적용 기록이 없는 외부 기술을 "사용자가 사내에 직접 적용했다"라고 지어내는 행위를 전면 금지합니다.
   - **외부 참고/오픈소스 사례(External OSS Use-Cases)**: `github-stars`, `linkedin_posts` 등에 수집된 참고용 기술 사례로 명확히 구분하여 서술합니다.
4. **온디맨드 지식 환류 (On-Demand Compounding)**:
   - 일반 질의응답 시에는 빠른 응답을 위해 `wiki/queries/` 파일 생성 및 `python "wiki/build.py"` 실행을 **생략**하고 답변 출력 후 즉시 종료합니다.
   - 오직 사용자가 **"위키에 저장해줘", "queries에 추가/환류해줘"** 등 명시적으로 문서화를 요청할 때만 Step 4(문서 생성 및 `build.py` 컴파일)를 수행합니다.

---

## 2. 고속 질의응답 실행 SOP (Fast-Track Operating Procedure)

### Step 1: 색인 + 본문 동시 Grep 타겟팅 (Turn 1 — `run_command`)
1. **일반 기술/개념 질의**:
   - 사용자의 질문에서 핵심 키워드(동의어, 영문/한글 약어 포함 2~4개)를 추출하고, 아래 **`git grep` 원라이너**로 (1) `wiki/index.md`의 제목·한줄요약 매칭과 (2) 핵심 5대 카테고리의 본문 매칭 줄 번호(파일당 최대 3줄, `-m 3`)를 0.1초 만에 동시 확보합니다:
     ```powershell
     git -c core.quotePath=false grep -ni --untracked -m 3 -E "키워드1|키워드2" -- wiki/index.md wiki/queries wiki/synthesis wiki/comparisons wiki/concepts wiki/entities
     ```
2. **주차별 R&D 마일스톤 / 지식 복리 번들 / 아키텍처 결정(ADR) 질의 ("1월 1주차 복리 지식", "월간 R&D 성과", "ADR-01이 뭐야?" 등)**:
   - **`wiki/Weekly-Knowledge-Compounding-Ledger.md` (주간 지식 복리 기록)**에는 주차별 핵심 R&D 테마, 5대 지식 번들(`Concepts`, `Comparisons`, `Synthesis`, `Queries`, `Entities`) 및 주요 `ADR` 내역이 표와 타임라인으로 집약되어 있습니다.
   - 주차별 지식 복리 내역이나 ADR 조회 시 `wiki/Weekly-Knowledge-Compounding-Ledger.md` 및 `wiki/entities/Core-System.md`를 1순위로 타겟팅합니다:
     ```powershell
     git -c core.quotePath=false grep -ni -E "1주차|ADR-01" -- wiki/Weekly-Knowledge-Compounding-Ledger.md wiki/entities/Core-System.md
     ```
3. **날짜 / 기간 / 타임라인 질의 ("1월에 뭐 했어?", "1월 1일 작업", "최근 작업 내역" 등)**:
   - `wiki/log.md`에는 모든 문서의 실제 날짜(`[YYYY-MM-DD]` 또는 `[YYYY-MM]`), 위키링크, 핵심 1줄 요약이 **최신순(내림차순)** 및 중요도순(`monthly` ➔ `daily` ➔ `synthesis` 우선)으로 색인되어 있습니다.
   - **특정 연/월/일 조회**: `wiki/log.md`를 대상으로 표준 날짜(`YYYY-MM-DD` 또는 `YYYY-MM`)를 `git grep`하여 0.02초 만에 해당 기간의 전체 작업 요약을 추출합니다:
     ```powershell
     git -c core.quotePath=false grep -ni "^- \[2026-01" -- wiki/log.md
     ```
     *(특정 일자 조회 시 `^- \[2026-01-01`, 월간/일일 스크럼만 필터링 시 `Work-Logs/(monthly|daily)|Work-Summaries|synthesis` 조합)*
   - **가장 최근 작업 조회**: `wiki/log.md`가 최신순 정렬이므로 `view_file("wiki/log.md", StartLine=1, EndLine=80)` 1회 호출로 즉시 확인합니다.
4. **확장 검색 (필요 시에만)**: 위 검색 결과가 부족하거나 특정 원본 코드가 필요한 경우에만 `wiki/sources` 또는 `raw/sources` 경로로 대상을 넓혀 `git grep`을 추가 실행합니다.

### Step 2: 핀포인트 병렬 정독 (Turn 2 — Parallel `view_file`)
1. Step 1의 `grep` 출력에서 가장 관련성이 높은 **핵심 문서 3~5개**를 선별합니다.
2. 개별 문서를 한 번에 하나씩 순차 호출하지 않고, **단 한 턴에 여러 개의 `view_file` 도구를 병렬 호출(Parallel Tool Calls)**하여 동시에 읽어 들입니다.
3. **줄 번호 슬라이싱 (Line-Range Targeting)**:
   - `Core-System.md`, `소유자.md` 등 수백 줄 규모의 대형 엔티티/종합 문서는 전체를 다 읽지 말고, Step 1의 `grep`에서 확인된 **줄 번호(`파일명:줄번호:`) 전후 구간(`StartLine`, `EndLine`)만 핀포인트로 지정**하여 읽습니다.
4. **열람 범위 절제 (Scope Discipline)**:
   - `wiki/` 내 정제 문서(`queries`, `synthesis`, `comparisons`, `concepts`, `entities`)와 `wiki/sources/` 요약본만으로 알고리즘·수식·코드 맥락이 충분하다면 `raw/sources/` 원본 파일은 열지 않고 바로 답변 작성으로 넘어갑니다.

### Step 3: 근거 기반 답변 즉시 출력 (Fast Response)
1. 파일 생성이나 빌드 대기 없이 즉시 사용자에게 답변을 출력합니다:
   - **요약 답변 (Executive Summary)**: 질문에 대한 직접적이고 명확한 핵심 결론
   - **기술적 세부 원리 및 분석 (Technical Details)**: 수식, 알고리즘, 아키텍처 동작 방식, 설정값/코드 설명
   - **사내 적용 이력 vs 외부 참고 이원화 (Use Cases)**: 사내 실제 적용 성과와 외부 참고 유즈케이스를 명확히 분리
   - **참조 위키 출처 (References)**: 관련 `[[wiki/...]]` 위키링크 목록 정리
2. 볼트 내에 정보가 부족한 경우:
   - 볼트에 기재된 내용까지만 명시하고, "볼트 내에 추가 기록 없음" 또는 "외부 참고 지식"임을 명백히 밝힙니다.

### Step 4: [선택적] 질의 지식 환류 및 컴파일 (On-Demand Only)
> ⚠️ **주의**: 이 단계는 일반 질문에서는 실행하지 않으며, **사용자가 명시적으로 위키 저장/환류를 요청한 경우에만** 수행합니다.

1. `wiki/queries/<질의명>.md` 파일로 신규 작성하거나 기존 관련 질의 문서 하단에 **덮어쓰기 유실 없이 점진적 누적 결합(Compounding)**합니다.
2. 문서 하단에 `<!-- ONE_LINE_SUMMARY: <한 줄 요약> -->` 주석을 필히 포함합니다.
3. 저장 완료 후 터미널에서 컴파일러를 가동하여 `README.md`, `wiki/index.md`, `wiki/log.md`를 자동 갱신합니다:
   ```powershell
   python "wiki/build.py"
   ```

---

## 3. 답변 및 질의 문서 작성 템플릿

```markdown
# [질의/주제명]

## 1. 개요 및 핵심 결론
(질문에 대한 간결하고 명확한 핵심 답변 요약 기재. 관련 [[wiki/concepts/<개념명>]] 및 [[wiki/entities/<실체명>]] 위키링크 포함)

## 2. 기술적 세부 원리 및 상세 분석
- **알고리즘 및 동작 구조**: 세부 매커니즘 설명...
- **핵심 기술 사양/수식**: $W_0 + B \times A$ 등 사양 설명...

## 3. 실무 적용 및 유즈케이스 분석

### 3.1. 사내 시스템/업무 적용 사례 (Internal Practice)
- (Work-Logs, chats, plans에서 실제 확인된 사내 적용 이력만 명시. 미적용 시 '사내 시스템 직접 적용 이력 없음 (외부 참고 기술)'으로 표시)

### 3.2. 외부 참고 및 오픈소스 유즈케이스 (External OSS Use-Cases)
- (github-stars 등 참고 자료에서 도출된 기술 및 유즈케이스)

## 4. 참조 위키 출처 (References)
* [[wiki/concepts/개념1]]
* [[wiki/entities/실체1]]
* [[wiki/sources/.../src-원본]]

<!-- ONE_LINE_SUMMARY: <질의 문서 저장 시에만 하단에 1문장 핵심 요약 주석 포함> -->
```

---

## 4. 주의사항 및 금지사항 (Bad Practices to Avoid) ⚠️

1. **[CRITICAL] `index.md` 전체 반복 열람 및 순차적 파일 읽기 금지**:
   - `wiki/index.md`를 처음부터 끝까지 `view_file`로 여러 번 쪼개 읽거나, 문서 5개를 5턴에 걸쳐 하나씩 읽지 마십시오. 반드시 `git grep` 1턴 ➔ 병렬 `view_file` 1턴으로 끝내십시오.
2. **[CRITICAL] 요청하지 않은 파일 생성 및 `build.py` 실행 금지**:
   - 단순 질문에 답변할 때 임의로 `wiki/queries/` 파일을 만들거나 `python "wiki/build.py"`를 돌려 응답을 지연시키지 마십시오.
3. **[CRITICAL] 근거 없는 지어내기(할루시네이션) 및 기존 지식 덮어쓰기 금지**:
   - 볼트에 없는 내용을 사내 시스템에 적용했다고 지어내지 마십시오.
   - 사용자 요청으로 `wiki/queries/`에 환류할 때는 기존 문서 내용을 유실시키지 않고 누적 결합하십시오.
