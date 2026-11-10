# Obsidian LLM Wiki 템플릿 사용 안내서 (walkthrough.md)

본 문서는 **Karpathy 스타일 LLM Wiki 템플릿**을 복제하여 새 프로젝트나 개인 지식 베이스를 시작할 때 준수해야 할 핵심 가이드입니다.

---

## 1. 초기 설정 (Quick Start)

1. **소유자 정보 수정**:
   - `wiki/entities/소유자.md` 파일명을 본인 이름(예: `홍길동.md`)으로 변경하고 프로필과 기술 스택을 작성합니다.
   - `.agents/rules/owner_rule.md` 내의 조직명, 직책을 본인 환경에 맞게 수정합니다.
2. **목적 정의 (`purpose.md`)**:
   - 볼트의 연구 범위, 수집 대상, 지식 복리 목적을 본인 도메인에 맞게 설정합니다.
3. **위키 컴파일 실행**:
   - 터미널에서 `python "wiki/build.py"`를 실행하여 메인 대시보드(`README.md`), 색인(`wiki/index.md`), 변경 로그(`wiki/log.md`)를 자동 생성합니다.

---

## 2. 일상 작업 워크플로우

1. **신규 원본 자료 적재**:
   - 새로 수집한 마크다운 문서나 기술 문서는 `raw/sources/0-Inbox/`에 적재합니다.
2. **에이전트 인제스트 지시**:
   - AI 에이전트에게 "Inbox 자료를 인제스트하여 요약본과 5대 지식을 도출해줘"라고 지시합니다.
   - 에이전트는 `wiki/sources/`에 요약본(`src-*.md`)을 생성하고, 관련 `concepts/`, `entities/`, `comparisons/` 문서를 작성/병합합니다.
3. **대시보드 빌드**:
   - `python "wiki/build.py"` 가동으로 지식 인덱스를 자동 최신화합니다.

<!-- ONE_LINE_SUMMARY: Karpathy 스타일 LLM Wiki 템플릿 초기 설정 및 일상 작업 워크플로우 가이드 -->
