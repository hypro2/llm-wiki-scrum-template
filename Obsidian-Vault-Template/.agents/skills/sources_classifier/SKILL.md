---
name: sources_classifier
description: raw/sources/0-Inbox/ 하위의 미분류 원본 파일 및 wiki/sources/0-Inbox/ 요약본을 정식 카테고리(1-Projects, 2-Areas, 3-Resources, 4-Archives)로 분류 이동하고, 볼트 전체의 관련 위키 링크([[...]])를 일괄 수정 및 자동 컴파일하는 SOP 스킬
---

# Sources 0-Inbox 미분류 정리 & 위키 링크 자동 수정 SOP 스킬

본 스킬은 볼트 내 `raw/sources/0-Inbox/` 디렉터리에 수집되어 있는 미분류 원본 문서들을 검토하여 적절한 정식 카테고리로 이동시키고, `wiki/sources/0-Inbox/`에 기재된 동격의 요약 문서(`src-*.md`) 디렉터리 위치를 1:1 미러링으로 동기화 이동하며, 볼트 전체의 위키 링크(`[[...]]`)를 변경된 신 경로로 일괄 수정하고 컴파일까지 완수하기 위한 에이전트 표준 행동 가이드라인입니다.

---

## 1. 분류 카테고리 및 이동 규칙 (Directory Mirroring Rules)

### 1.1. 표준 4대 정식 카테고리
1. **`1-Projects/`**: 기한과 목표가 명확한 특정 프로젝트, 개발 계획서, 산출물 관련 원본 문서
2. **`2-Areas/`**: 주간/월간 업무 일지(`Work-Logs`), 스크럼 기록, 정기 리포트, 사내 시스템 관련 문서
3. **`3-Resources/`**: 기술 노트, 프레임워크 연구 문서, 깃허브 스타 스크랩(`github-stars`), PDF 논문/교재 등 학습 및 참고 기술 자료
4. **`4-Archives/`**: 만료되었거나 완료되어 보관 목적으로 이전하는 자료

### 1.2. 디렉터리 1:1 미러링 및 동기화 원칙 (Directory Mirroring)
- 원본 파일이 `raw/sources/0-Inbox/path/file.md`에서 `raw/sources/<Category>/path/file.md`로 이동하면, 요약본 파일 또한 `wiki/sources/0-Inbox/path/src-file.md`에서 `wiki/sources/<Category>/path/src-file.md`로 **1:1 매칭되는 동일 대상 디렉터리로 즉각 이동**시켜 동기화해야 합니다.
- 이동 후 이전 경로에 남아있는 잔재 요약본이나 빈 디렉터리는 깨끗이 제거하여 중복 생성을 차단합니다.

---

## 2. 5단계 실행 SOP (Standard Operating Procedure)

### Step 1: 미분류 대상 탐색 및 분류 판단 (Analysis & Classification)
1. `raw/sources/0-Inbox/` 하위의 대상 파일(마크다운, PDF, txt 등) 또는 서브 디렉터리를 `view_file` 또는 `list_dir` 도구로 분석합니다.
2. 문서 내용과 핵심 주제를 파악하여 `1-Projects`, `2-Areas`, `3-Resources`, `4-Archives` 중 가장 부합하는 정식 카테고리를 결정합니다.
3. 문서 내에 특정 분류 위치나 경로 태그가 명시되어 있다면 해당 지정 경로를 최우선으로 반영합니다.

### Step 2: 원본 파일 이동 (Move Raw File)
- 원본 파일을 `raw/sources/0-Inbox/...`에서 결정된 정식 카테고리 위치(`raw/sources/<Category>/...`)로 이동시킵니다.
- 쉘 커맨드 또는 파이썬 스크립트를 이용하여 안전하게 파일/폴더 이동을 수행합니다.

### Step 3: 요약 문서 동기화 이동 (Mirror Wiki Source File)
- 해당 원본에 매칭되는 요약 문서(`wiki/sources/0-Inbox/.../src-<파일명>.md`)가 존재하는지 확인합니다.
- 존재할 경우, 동일한 카테고리 계층 구조를 갖추도록 `wiki/sources/<Category>/.../src-<파일명>.md` 경로로 이동시킵니다.

### Step 4: 위키 링크 일괄 수정 (Link Refactoring)
1. **요약 문서 상단 링크 수정**:
   - 이동된 요약 문서(`src-*.md`) 상단의 `소스: [[raw/sources/0-Inbox/...]]` 구 경로 위키 링크를 신규 이동된 `소스: [[raw/sources/<Category>/...]]` 상대경로 위키 링크로 수정합니다.
2. **전체 위키 문서 링크 일괄 갱신**:
   - 볼트 내 모든 `wiki/` 문서(`concepts/`, `entities/`, `comparisons/`, `synthesis/`, `queries/`, `Weekly-Knowledge-Compounding-Ledger.md` 등)를 탐색하여, 이동 전 구 경로(`[[raw/sources/0-Inbox/...]]`, `[[wiki/sources/0-Inbox/...]]`, `[[sources/0-Inbox/...]]`)를 가리키고 있는 모든 위키 링크를 신 경로로 일괄 검색 및 치환합니다.

### Step 5: 위키 자동 컴파일 및 검증 (Auto-Compile & Verification)
1. 분류 이동 및 링크 수정 작업이 완료되면, 터미널에서 위키 컴파일러를 실행합니다:
   ```powershell
   python "wiki/build.py"
   ```
2. 컴파일러 실행을 통해 프로젝트 루트의 `README.md` (대시보드 세부 디렉터리 통계), `wiki/index.md` (전체 색인), `wiki/log.md` (타임라인 로그) 및 `Weekly-Knowledge-Compounding-Ledger.md` (누적 통계)가 자동으로 갱신되었는지 확인합니다. (`build.py`가 `wiki/log.md`를 최신 경로 기준으로 자동 재작성하므로 `log.md`에 수동으로 텍스트를 append하지 않습니다.)

---

## 3. 주의사항 및 금지사항 (Bad Practices to Avoid) ⚠️

1. **[CRITICAL] 링크 유실 방지**: 원본/요약본 이동 후 기존 지식 문서(`concepts/`, `entities/` 등)에서 그 문서를 가리키던 위키 링크를 갱신하지 않아 끊어진 링크(Broken Link)가 발생하는 일이 없도록 반드시 Step 4의 전역 링크 치환을 수행해야 합니다.
2. **[CRITICAL] 덮어쓰기 유실 금지**: 요약본이나 개념 문서를 수정할 때 기존의 고품질 분석 내용이나 주석(`<!-- ONE_LINE_SUMMARY -->`)을 덮어써서 날려버리는 행위를 엄금합니다.
3. **[CRITICAL] 빈 디렉터리 정리**: 이동 후 `0-Inbox/` 하위에 남은 사용되지 않는 빈 폴더나 구 버전 중복 요약본은 즉시 정리합니다.
