import os
import glob
import re
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
wiki_dir = script_dir
root_dir = os.path.dirname(wiki_dir)

META_BOLD_SKIP = {'핵심', '내용', '참고', '완료사항', '공유사항', '진행사항', '이슈', '목표'}

def _clean_markdown_inline(text):
    # [[path|label]] -> label
    text = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', text)
    # [[path/to/name.md]] or [[name]] -> name
    def _repl_link(m):
        inner = m.group(1).split('/')[-1]
        if inner.endswith('.md'):
            inner = inner[:-3]
        return inner
    text = re.sub(r'\[\[([^\]]+)\]\]', _repl_link, text)
    # [label](url) -> label
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold/italic markers
    text = re.sub(r'(\*\*|\*|__)', '', text)
    return " ".join(text.split()).strip()

def read_one_line_summary(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<!--\s*ONE_LINE_SUMMARY:\s*(.*?)\s*-->', content, re.DOTALL)
            if match:
                return " ".join(match.group(1).split())
            
            # Fallback 1: 들여쓰기 없는 최상위 번호/불릿 볼드 핵심 항목 우선 추출 (최대 3개)
            bold_items = []
            for pattern in (r'^(?:\d+\.|\*|-)[ \t]+\*\*([^*\n]+?)\*\*', r'^[ \t]+(?:\d+\.|\*|-)[ \t]+\*\*([^*\n]+?)\*\*'):
                for m in re.finditer(pattern, content, re.MULTILINE):
                    item = m.group(1).strip().rstrip(':')
                    if item and item not in META_BOLD_SKIP and len(item) > 3:
                        if item not in bold_items:
                            bold_items.append(item)
                        if len(bold_items) >= 3:
                            break
                if bold_items:
                    break
            if bold_items:
                return " / ".join(bold_items)

            # Fallback 2: 본문 첫 유의미 문장/불릿 추출
            body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
            body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
            in_code = False
            for raw_line in body.splitlines():
                line = raw_line.strip()
                if line.startswith('```'):
                    in_code = not in_code
                    continue
                if in_code or not line:
                    continue
                if line.startswith(('#', '>', '|', '---', '***', '소스:', '- 소스:', '* 소스:', '- 수집 출처:', '- 찐 원본 출처:')):
                    continue
                cleaned = _clean_markdown_inline(re.sub(r'^(?:\d+\.|\*|-)[ \t]+', '', line))
                if len(cleaned) >= 10:
                    sent_match = re.match(r'^(.{10,130}?(?:다\.|음\.|함\.|\.(?=\s|$)))', cleaned)
                    if sent_match:
                        return sent_match.group(1).strip()
                    return cleaned[:135] + ('...' if len(cleaned) > 135 else '')
    except:
        pass
    return ""

def extract_doc_date(filepath, basename):
    # 1. 파일명에 YYYY-MM-DD 패턴
    m_ymd = re.search(r'(20\d{2}-\d{2}-\d{2})', basename)
    if m_ymd:
        return m_ymd.group(1)
    
    # 2. Frontmatter 내 modified / created 날짜
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            head = f.read(600)
        m_mod = re.search(r"modified:\s*['\"]?(20\d{2}-\d{2}-\d{2})", head)
        if m_mod:
            return m_mod.group(1)
    except:
        pass

    # 3. 파일명에 YYYY-MM 패턴
    m_ym = re.search(r'(20\d{2}-\d{2})(?!-\d)', basename)
    if m_ym:
        return m_ym.group(1)

    # 4. 파일명에 'YY년 M월' 패턴
    m_kr = re.search(r'(\d{2})년\s*(\d{1,2})월', basename)
    if m_kr:
        yy, mm = int(m_kr.group(1)), int(m_kr.group(2))
        return f"20{yy:02d}-{mm:02d}"

    # 5. 파일명에 연도(20XX)만 있는 경우
    m_y = re.search(r'\b(202[0-9])\b', basename)
    if m_y:
        return m_y.group(1)

    # 6. 기본 폴백: 파일 수정 시각 (mtime)
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except:
        return "0000-00-00"

def get_files(subdir):
    path = os.path.join(wiki_dir, subdir, '**', '*.md')
    files = glob.glob(path, recursive=True)
    files = [f.replace('\\', '/') for f in files]
    return sorted(files)

def build_index():
    subdirs = ['queries', 'synthesis', 'comparisons', 'concepts', 'entities', 'sources']
    lines = ["# LLM Wiki Index\n"]
    
    # Core Ledgers
    ledger_file = os.path.join(wiki_dir, 'Weekly-Knowledge-Compounding-Ledger.md')
    if os.path.exists(ledger_file):
        lines.append("## Core Ledgers\n")
        ledger_summary = read_one_line_summary(ledger_file)
        if ledger_summary:
            lines.append(f"- [[Weekly-Knowledge-Compounding-Ledger.md|Weekly-Knowledge-Compounding-Ledger]] - {ledger_summary}")
        else:
            lines.append("- [[Weekly-Knowledge-Compounding-Ledger.md|Weekly-Knowledge-Compounding-Ledger]]")
        lines.append("- [[log.md|Timeline Log]] - 시간순 작업 일지 및 변경 이력\n")
    
    for subdir in subdirs:
        lines.append(f"## {subdir.capitalize()}\n")
        files = get_files(subdir)
        for filepath in files:
            filename = os.path.basename(filepath)
            basename = filename[:-3]
            rel_path = filepath[len(wiki_dir)+1:]
            
            summary = read_one_line_summary(filepath)
            if summary:
                lines.append(f"- [[{rel_path}|{basename}]] - {summary}")
            else:
                lines.append(f"- [[{rel_path}|{basename}]]")
        lines.append("\n")
        
    with open(os.path.join(wiki_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

def get_stats():
    stats = {}
    stats['concepts'] = len(get_files('concepts'))
    stats['entities'] = len(get_files('entities'))
    stats['synthesis'] = len(get_files('synthesis'))
    stats['comparisons'] = len(get_files('comparisons'))
    stats['queries'] = len(get_files('queries'))
    
    sources_files = get_files('sources')
    stats['sources_total'] = len(sources_files)
    
    sources_detail = {
        '0-Inbox': 0,
        '1-Projects': 0,
        '2-Areas': 0,
        '3-Resources': 0,
        '4-Archives': 0,
        'Work-Logs': 0,
        'Work-Summaries': 0,
        'github-stars': 0,
        'Blog-Posts': 0,
        'linkedin_posts': 0,
        'Graduate-Courses': 0
    }
    
    for f in sources_files:
        if '/0-Inbox/' in f: sources_detail['0-Inbox'] += 1
        if '/1-Projects/' in f: sources_detail['1-Projects'] += 1
        if '/2-Areas/' in f: 
            sources_detail['2-Areas'] += 1
            if '/Work-Logs/' in f: sources_detail['Work-Logs'] += 1
            if '/Work-Summaries/' in f: sources_detail['Work-Summaries'] += 1
        if '/3-Resources/' in f:
            sources_detail['3-Resources'] += 1
            if '/github-stars/' in f: sources_detail['github-stars'] += 1
            if '/Blog-Posts/' in f: sources_detail['Blog-Posts'] += 1
            if '/linkedin_posts/' in f: sources_detail['linkedin_posts'] += 1
            if '/Graduate-Courses/' in f: sources_detail['Graduate-Courses'] += 1
        if '/4-Archives/' in f: sources_detail['4-Archives'] += 1
            
    return stats, sources_detail

def sync_ledger_metrics(stats):
    ledger_path = os.path.join(wiki_dir, 'Weekly-Knowledge-Compounding-Ledger.md')
    if not os.path.exists(ledger_path):
        return
    try:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = (
            r'(\* \*\*5대 카테고리 누적 현황\*\*:\n)'
            r'(?:  \* [^\n]+\n)+'
        )
        replacement = (
            f"\\1"
            f"  * Concepts: {stats['concepts']}개 문서\n"
            f"  * Comparisons: {stats['comparisons']}개 문서\n"
            f"  * Synthesis: {stats['synthesis']}개 문서\n"
            f"  * Queries: {stats['queries']}개 문서\n"
            f"  * Entities: {stats['entities']}개 문서\n"
            f"  * Sources 요약본: {stats['sources_total']}개 문서\n"
        )
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            with open(ledger_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
    except:
        pass

def build_readme():
    stats, sd = get_stats()
    sync_ledger_metrics(stats)
    
    # Project Owner 엔티티 요약 동적 감지
    owner_entity = None
    for cand in ['소유자.md', 'Owner.md']:
        cand_path = os.path.join(wiki_dir, 'entities', cand)
        if os.path.exists(cand_path):
            owner_entity = cand
            break
    if not owner_entity:
        entity_files = get_files('entities')
        if entity_files:
            owner_entity = os.path.basename(entity_files[0])

    if owner_entity:
        owner_name = owner_entity[:-3]
        owner_summary = read_one_line_summary(os.path.join(wiki_dir, 'entities', owner_entity))
        if not owner_summary:
            owner_summary = f"본 볼트 소유자(Project Owner) {owner_name}의 프로필 및 커리어 지식 엔티티"
        owner_entry_line = f"- [{owner_name} (Project Owner)](wiki/entities/{owner_entity}): {owner_summary}"
    else:
        owner_entry_line = "- [Project Owner](wiki/entities/소유자.md): 본 볼트 소유자의 프로필 및 커리어 지식 엔티티"

    lines = [
        "# Obsidian Vault LLM Wiki (README)\n",
        "본 프로젝트 저장소는 **Karpathy 스타일 LLM Wiki** 구조로 운영되는 개인 지식 복리(Knowledge Compounding) 인프라입니다. AI 에이전트(Antigravity 등)가 원본 R&D 노트, 업무 일지, 스크럼 기록 및 깃허브 스타 수집 저장소를 정독하고 5대 카테고리 마크다운 지식 문서로 점진적 누적 결합(Compounding)을 수행합니다.\n",
        "## 📊 디렉터리별 대시보드 통계 (Dashboard Statistics)\n",
        "| 상위 디렉터리 | 파일 수 | 설명 |",
        "| --- | --- | --- |",
        f"| [wiki/sources](wiki/sources) | {stats['sources_total']} | 원본 요약본 및 출처 기록 (0-Inbox, 1-Projects, 2-Areas, 3-Resources 등) |",
        f"| [wiki/concepts](wiki/concepts) | {stats['concepts']} | 이론, 방법론 등 개념 문서 |",
        f"| [wiki/entities](wiki/entities) | {stats['entities']} | 인물, 기업, 프로젝트, 도구 등 실체 문서 |",
        f"| [wiki/synthesis](wiki/synthesis) | {stats['synthesis']} | 종합 분석 및 트렌드 리포트 |",
        f"| [wiki/comparisons](wiki/comparisons) | {stats['comparisons']} | 기술, 개념 간 평면 비교 분석 |",
        f"| [wiki/queries](wiki/queries) | {stats['queries']} | 트러블슈팅 및 쿼리 기록 |\n",
        "### Sources 세부 디렉터리 통계\n",
        "| 디렉터리 경로 | 파일 수 | 비고 |",
        "| --- | --- | --- |",
        f"| sources/0-Inbox/ | {sd['0-Inbox']} | 미분류, 신규 수집 스크랩 및 계획서 등 |",
        f"| sources/1-Projects/ | {sd['1-Projects']} | 프로젝트 관련 출처 문서 |",
        f"| sources/2-Areas/ | {sd['2-Areas']} | 주요 업무 영역 |",
        f"| └─ sources/2-Areas/Work-Logs/ | {sd['Work-Logs']} | 일일/월간/전체 작업 로그 및 세션 기록 |",
        f"| └─ sources/2-Areas/Work-Summaries/ | {sd['Work-Summaries']} | 주간/분기 작업 요약본 |",
        f"| sources/3-Resources/ | {sd['3-Resources']} | 기술 참고 자료, 연구 리소스 |",
        f"| └─ sources/3-Resources/github-stars/ | {sd['github-stars']} | GitHub Star 오픈소스 심층 분석 요약본 |",
        f"| └─ sources/3-Resources/Technical-Notes/Blog-Posts/ | {sd['Blog-Posts']} | 기술 블로그/아티클 출처 자료 |",
        f"| └─ sources/3-Resources/Technical-Notes/linkedin_posts/ | {sd['linkedin_posts']} | LinkedIn 기술 피드 및 웹 보강 요약본 |",
        f"| └─ sources/3-Resources/Learning-Materials/Graduate-Courses/ | {sd['Graduate-Courses']} | 대학원 석사 과정 강의 및 연구 노트 |",
        f"| sources/4-Archives/ | {sd['4-Archives']} | 보관된 자료 |\n",
        "## 🧠 주요 테마 분석 (Major Themes)\n",
        "본 위키는 대형 언어 모델(LLM), RAG 파이프라인(Agentic RAG 등), AI 에이전트 구축 및 엔지니어링 지식을 중심으로 구성되어 있습니다. 특히 실무적인 트러블슈팅, 도구 비교 분석(Comparisons), 아키텍처 진화 기록이 지속적으로 축적(Compounding)됩니다.\n",
        "## 🔗 위키 주요 진입점\n",
        owner_entry_line,
        "- [주간 지식 복리 기록 (Weekly Compounding Ledger)](wiki/Weekly-Knowledge-Compounding-Ledger.md): 주차별 지식 복리 마일스톤, 생성·병합된 5대 카테고리 지식 번들 및 아키텍처 진화 원장",
        "- [wiki/index.md](wiki/index.md): 전체 지식 문서 색인 및 한 줄 요약 목록",
        "- [wiki/log.md](wiki/log.md): 타임라인 순 위키 변경 이력 로그",
        "- [AGENTS.md](AGENTS.md): 에이전트 위키 컴파일 운영 규칙 및 스키마 명세\n"
    ]
    
    content = "\n".join(lines)
    
    with open(os.path.join(root_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(content)
    
    for deprecated in [os.path.join(wiki_dir, 'README.md'), os.path.join(wiki_dir, 'overview.md')]:
        if os.path.exists(deprecated):
            try:
                os.remove(deprecated)
            except:
                pass

def _log_priority(rel_path):
    if rel_path == 'Weekly-Knowledge-Compounding-Ledger.md':
        return 0
    if '/Work-Logs/monthly/' in rel_path or '/Work-Summaries/' in rel_path or '/Work-Logs/total/' in rel_path:
        return 0
    if '/Work-Logs/daily/' in rel_path:
        return 1
    if rel_path.startswith(('synthesis/', 'comparisons/', 'queries/', 'concepts/', 'entities/')):
        return 2
    if '/Work-Logs/plans/' in rel_path or '/Work-Logs/chats/' in rel_path:
        return 4
    return 3

def build_log():
    log_entries = []
    path = os.path.join(wiki_dir, '**', '*.md')
    files = glob.glob(path, recursive=True)
    
    for filepath in files:
        filepath_norm = filepath.replace('\\', '/')
        if os.path.basename(filepath_norm) in ['index.md', 'overview.md', 'README.md', 'log.md', 'log-archive-init.md', 'walkthrough.md', 'build.py']:
            continue
        try:
            filename = os.path.basename(filepath_norm)
            basename = filename[:-3]
            rel_path = filepath_norm[len(wiki_dir)+1:]
            date_str = extract_doc_date(filepath_norm, basename)
            summary = read_one_line_summary(filepath_norm)
            log_entries.append((date_str, _log_priority(rel_path), rel_path, basename, summary))
        except:
            pass
            
    log_entries.sort(key=lambda x: (-int(re.sub(r'\D', '', x[0]).ljust(8, '0')[:8]), x[1], x[2]))
    
    lines = ["# 변경 이력 및 타임라인 색인 (Timeline Log)\n"]
    for date_str, _, rel_path, basename, summary in log_entries:
        if summary:
            lines.append(f"- [{date_str}] [[{rel_path}|{basename}]] - {summary}")
        else:
            lines.append(f"- [{date_str}] [[{rel_path}|{basename}]]")
        
    with open(os.path.join(wiki_dir, 'log.md'), 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

if __name__ == '__main__':
    build_index()
    build_readme()
    build_log()
    print("Project root README.md & Wiki Dashboard rebuilt successfully.")
