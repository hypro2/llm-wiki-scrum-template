# LLM Wiki Schema & Workflows (AGENTS.md)

이 문서는 이 옵시디언 볼트를 **Karpathy 스타일 LLM Wiki** 구조로 운영하기 위해 LLM 에이전트(Antigravity 등)가 준수해야 할 핵심 지침 인덱스입니다.

> 📌 **관련 핵심 안내 문서 인덱스**:
> - [[purpose.md]]: 개인 지식 복리(Knowledge Compounding) 볼트 구축 목적 및 핵심 지향점
> - [[schema.md]]: LLM Wiki 계층 구조 (`raw/` vs `wiki/`) 및 5대 지식 카테고리 디렉터리 명세

---

## 1. 7대 핵심 준수 원칙 (Core Principles)

1. **지식 유실 절대 금지 (Compounding)**: 개념/실체/종합 지식 병합 및 업데이트 시 기존 본문(정의, 핵심 특징, 코드 예시)을 절대 덮어써서 날리지 말고 하단에 누적 결합한다.
2. **AI 에이전트 직접 수동 정독 & 집필 의무화**: 파이썬/쉘/Node.js 등의 스크립트로 요약문이나 위키 마크다운 문서를 대량 자동 생성하는 행위를 전면 금지한다. 스크립트는 오직 최종 `python "wiki/build.py"` 컴파일에서만 허용된다.
3. **사용자 실무 사례 할루시네이션 금지 (Anti-Hallucination)**: `Internal Practice` 섹션에는 오직 볼트 내 `Work-Logs/`, `chats/`, `plans/`에 입증된 사내/프로젝트 구현 이력만 기록하며, 미적용 기술은 '사내 시스템 직접 적용 이력 없음 (외부 참고 기술)'으로 서술한다.
4. **실무 사례 이원화 서술 (Dual-Track Practice)**: 실무 사례 작성 시 '1. 사용자 자체 실무 적용 사례(Internal Practice)'와 '2. 오픈소스/GitHub 실무 유즈케이스(External OSS Use-Cases)' 소목차로 분리하여 작성한다.
5. **1:1 경로 미러링 & 동기화 (Directory Mirroring)**: `raw/sources/` 하위 원본 파일 경로와 `wiki/sources/` 하위 요약본 경로를 1:1로 정확히 동격 유지하고, 원본 파일 이동 시 요약본도 동기화하여 이동시킨다.
6. **비공개 내부 저장소 원격 푸시 금지 (Local-Only Protection)**: 민감한 사내 코드 및 비공개 로컬 저장소는 외부 원격 저장소로의 `git push`를 전면 금지하며, 원격 푸시 대상은 안전하게 지정된 저장소로 엄격히 한정한다.
7. **협업 저장소 본인 커밋 기준 필터링**: 팀 협업 저장소의 작업 내역을 스크럼 및 위키에 수록할 때는 반드시 본인이 직접 작성한 커밋(`git log --author="<본인계정>" --no-merges`)만 반영하며, 병합으로 유입된 타 작업자의 작업분은 전면 배제한다.

---

## 2. 상세 작업 규칙 및 전용 룰 문서 참조 (Rules & Skills Pointer)

* **인제스트 CoT 프로세스 & 표준 템플릿**: `[[.agents/rules/wiki_ingestion_rule.md]]` (상세 인제스트, 미러링, 작성 템플릿 명세)
* **소유자 특별 관리 규정**: `[[.agents/rules/owner_rule.md]]` (`wiki/entities/소유자.md` 누적 병합 규칙)
* **핵심 시스템 특별 관리 규정**: `[[.agents/rules/core_system_rule.md]]` (주요 시스템 엔티티 누적 병합 규칙)
* **개인화 개발 메모리 규정**: `[[.agents/rules/user_dev_memory.md]]` (행동 지침 및 개발 원칙)
* **일일 스크럼 보고서 생성 및 관리 스킬**: `[[.agents/skills/scrum_report/SKILL.md]]` (스크럼 작성 및 동기화 SOP)
* **LLM Wiki 컴파일러 스킬**: `[[.agents/skills/llm_wiki_compiler/SKILL.md]]` (위키 5대 지식 추출 및 깃허브 스타 수집 SOP)
* **주간 지식 복리 기록 원장**: `[[wiki/Weekly-Knowledge-Compounding-Ledger.md]]` (주차별 5대 지식 번들 및 아키텍처 진화 추적 원장)
* **LinkedIn 피드 수집 및 웹 보강 스킬**: `[[.agents/skills/linkedin_ingestion/SKILL.md]]` (Playwright 활동 수집, 댓글 URL 파싱 및 위키 심층 집필 SOP)
* **Sources 분류 및 이동 스킬**: `[[.agents/skills/sources_classifier/SKILL.md]]` (Inbox ➔ 1-4번 디렉터리 분류 동기화 스킬)
* **위키 QA & 근거 기반 응답 스킬**: `[[.agents/skills/wiki_qa/SKILL.md]]` (위키 탐색 및 환류 응답 스킬)
