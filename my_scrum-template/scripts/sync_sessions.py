#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_sessions.py - Comprehensive Session & Plan Sync Pipeline for Claude Code & Antigravity (IDE)

이 스크립트는 3대 소스 경로:
1. Claude Code 프로젝트 세션 (~/.claude/projects/)
2. Antigravity 세션 및 플랜 (~/.gemini/antigravity/brain/)
3. Antigravity IDE 세션 및 플랜 (~/.gemini/antigravity-ide/brain/)
에서 생성된 대화 로그(JSONL)와 계획서(implementation_plan.md)를 자동으로 탐색하여,
- 더미/빈 세션(OAuth 만료, 무대화, 500B 미만)을 엄격히 필터링 및 청소하고,
- my_scrum (plans, chats/raw, chats/md)으로 증분 복사 및 고품질 마크다운 파싱을 수행하며,
- Obsidian Vault (raw/sources/2-Areas/Work-Logs)로 1:1 미러링하고,
- 최종적으로 wiki/build.py를 실행하여 지식 인덱스를 자동 최신화합니다.
"""

import os
import sys
import re
import json
import shutil
import hashlib
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Windows 콘솔 유니코드 인코딩 보장
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# parse_chat 모듈 임포트 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    import parse_chat
except ImportError:
    parse_chat = None


def detect_paths():
    """
    현재 사용자 홈 환경에 맞춰 3대 원본 경로 및 저장소 경로를 자동 감지합니다.
    """
    home = os.path.expanduser("~")
    
    # 1. Claude Projects 경로
    claude_dir = os.path.join(home, ".claude", "projects")
    
    # 2. Antigravity Brain 경로
    ag_dir = os.path.join(home, ".gemini", "antigravity", "brain")
    
    # 3. Antigravity IDE Brain 경로
    ag_ide_dir = os.path.join(home, ".gemini", "antigravity-ide", "brain")
    
    # 4. my_scrum 저장소 경로 후보
    candidate_scrum = [
        os.path.abspath(os.path.join(CURRENT_DIR, "..")),
        os.path.join(home, "Documents", "GitHub", "my_scrum"),
        os.path.join(home, "Documents", "GitHub", "my_scrum-template"),
    ]
    scrum_dir = None
    for cand in candidate_scrum:
        if os.path.isdir(cand) and os.path.isdir(os.path.join(cand, "plans")):
            scrum_dir = cand
            break
    if not scrum_dir:
        scrum_dir = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
        
    # 5. Obsidian Vault 경로 후보
    candidate_obsidian = [
        os.path.join(os.path.dirname(scrum_dir), "Obsidian-Vault-Template") if scrum_dir else None,
        os.path.join(home, "Documents", "GitHub", "Obsidian-Vault-Template"),
        os.path.join(home, "Documents", "Obsidian-Vault"),
        os.path.join(home, "Documents", "GitHub", "Obsidian-Vault"),
        os.path.join(home, "Documents", "Obsidian Vault"),
        os.path.join(home, "Desktop", "Obsidian Vault"),
        os.path.join(os.path.dirname(scrum_dir), "Obsidian-Vault") if scrum_dir else None,
        os.path.join(os.path.dirname(scrum_dir), "Obsidian Vault") if scrum_dir else None
    ]
    obsidian_dir = None
    for cand in candidate_obsidian:
        if cand and os.path.isdir(cand) and os.path.isdir(os.path.join(cand, "raw")):
            obsidian_dir = cand
            break

    return {
        "home": home,
        "claude_projects": claude_dir if os.path.isdir(claude_dir) else None,
        "claude_plans": os.path.join(home, ".claude", "plans") if os.path.isdir(os.path.join(home, ".claude", "plans")) else None,
        "ag_brain": ag_dir if os.path.isdir(ag_dir) else None,
        "ag_ide_brain": ag_ide_dir if os.path.isdir(ag_ide_dir) else None,
        "scrum_dir": scrum_dir,
        "obsidian_dir": obsidian_dir
    }


def is_valid_session_jsonl(file_path):
    """
    JSONL 파일이 더미/빈 파일이 아닌 유효한 실질적 대화 세션인지 엄격히 검사합니다.
    - 파일 크기 최소 500바이트 이상
    - OAuth 만료 오류 또는 단순 시스템 에러 세션 제외
    - 실제 사용자(User) 입력이 유의미하게 존재하는지 확인
    """
    try:
        if not os.path.exists(file_path):
            return False
        file_size = os.path.getsize(file_path)
        if file_size < 500:
            return False
        
        has_valid_user_message = False
        has_auth_error = False

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line_idx, line in enumerate(f):
                if line_idx > 200:  # 앞부분 200줄 검사
                    break
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    # 인증 실패 확인
                    content_str = str(data.get("content", "")) + str(data.get("message", ""))
                    if "OAuth session expired" in content_str or "Failed to authenticate" in content_str:
                        has_auth_error = True

                    # Claude Code 형식
                    if data.get("type") in ("user", "USER_INPUT"):
                        text_val = ""
                        c = data.get("content", "")
                        if not c and isinstance(data.get("message"), dict):
                            c = data.get("message", {}).get("content", "")

                        if isinstance(c, str):
                            text_val = c.strip()
                        elif isinstance(c, list):
                            text_parts = []
                            for item in c:
                                if isinstance(item, dict):
                                    if item.get("type") == "text":
                                        text_parts.append(str(item.get("text", "")))
                                elif isinstance(item, str):
                                    text_parts.append(item)
                            text_val = " ".join(text_parts).strip()
                        
                        if len(text_val) >= 2:
                            has_valid_user_message = True
                            
                    # Antigravity transcript 형식
                    if data.get("type") == "USER_INPUT" and data.get("content"):
                        if len(str(data["content"]).strip()) >= 2:
                            has_valid_user_message = True
                except Exception:
                    continue

        if has_auth_error and not has_valid_user_message:
            return False

        return has_valid_user_message
    except Exception:
        return False


def is_valid_markdown_chat(md_path):
    """
    파싱된 마크다운 파일이 내용이 비어있지 않고 실질적인 대화 내용을 담고 있는지 검사합니다.
    """
    try:
        if not os.path.exists(md_path):
            return False
        if os.path.getsize(md_path) < 500:
            return False
        with open(md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
        if "OAuth session expired" in content or "Failed to authenticate" in content:
            if len(content) < 800:
                return False
        lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#") and not l.startswith(">")]
        return len(lines) >= 3
    except Exception:
        return False


def slugify(text, max_len=40):
    """
    제목 텍스트를 파일명에 안전한 슬러그로 변환합니다.
    """
    if not text:
        return ""
    cleaned = re.sub(r"^[#\s]+", "", text).strip()
    cleaned = re.sub(r'[\/:*?"<>|\[\]\(\)]', "", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = cleaned.strip("-")
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip("-")
    return cleaned


def extract_plan_title(plan_path):
    """
    implementation_plan.md 파일의 첫 번째 헤더(# ...)에서 제목을 추출합니다.
    """
    try:
        with open(plan_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith("# "):
                    title = line_str[2:].strip()
                    return title
        return ""
    except Exception:
        return ""


def file_content_differs(src, dst):
    """
    두 파일의 내용이 다른지 빠르게 확인합니다 (크기 및 해시 비교).
    """
    if not os.path.exists(dst):
        return True
    if os.path.getsize(src) != os.path.getsize(dst):
        return True
    
    def md5(p):
        h = hashlib.md5()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    
    return md5(src) != md5(dst)


def cleanup_dummy_files(paths, stats):
    """
    my_scrum 및 Obsidian Vault 내에 이미 들어간 빈/더미 파일들을 검사하여 정리합니다.
    """
    print("\n" + "=" * 60)
    print("🧹 [0/4] Cleaning up empty / dummy files")
    print("=" * 60)
    
    md_dir = os.path.join(paths["scrum_dir"], "chats", "md")
    raw_dir = os.path.join(paths["scrum_dir"], "chats", "raw")
    obsidian_md_dir = os.path.join(paths["obsidian_dir"], "raw", "sources", "2-Areas", "Work-Logs", "chats", "md") if paths["obsidian_dir"] else None
    obsidian_raw_dir = os.path.join(paths["obsidian_dir"], "raw", "sources", "2-Areas", "Work-Logs", "chats", "raw") if paths["obsidian_dir"] else None

    cleaned_count = 0
    if os.path.isdir(md_dir):
        for fname in os.listdir(md_dir):
            if not fname.endswith(".md"):
                continue
            md_path = os.path.join(md_dir, fname)
            if not is_valid_markdown_chat(md_path):
                # 더미 마크다운 파일 삭제
                try:
                    os.remove(md_path)
                    cleaned_count += 1
                    # Obsidian Vault 내 상응 파일도 삭제
                    if obsidian_md_dir:
                        ob_md = os.path.join(obsidian_md_dir, fname)
                        if os.path.exists(ob_md):
                            os.remove(ob_md)
                except Exception as e:
                    print(f"  ❌ Error removing dummy MD {fname}: {e}")

    # raw 디렉토리에서도 유효하지 않은 jsonl 파일 정리
    if os.path.isdir(raw_dir):
        for fname in os.listdir(raw_dir):
            if not fname.endswith(".jsonl"):
                continue
            raw_path = os.path.join(raw_dir, fname)
            if not is_valid_session_jsonl(raw_path):
                try:
                    os.remove(raw_path)
                    if obsidian_raw_dir:
                        ob_raw = os.path.join(obsidian_raw_dir, fname)
                        if os.path.exists(ob_raw):
                            os.remove(ob_raw)
                except Exception:
                    pass

    stats["dummy_cleaned"] = cleaned_count
    print(f"✨ Cleaned {cleaned_count} empty / dummy session markdown files.")


def sync_plans(paths, stats, force=False):
    """
    Antigravity 및 Antigravity IDE의 implementation_plan.md 파일을 my_scrum/plans/로 동기화합니다.
    """
    print("\n" + "=" * 60)
    print("📋 [1/4] Plans Sync (Antigravity & Antigravity IDE)")
    print("=" * 60)
    
    target_plans_dir = os.path.join(paths["scrum_dir"], "plans")
    os.makedirs(target_plans_dir, exist_ok=True)
    
    sources = []
    if paths["ag_brain"]:
        sources.append(("Antigravity Brain", paths["ag_brain"]))
    if paths["ag_ide_brain"]:
        sources.append(("Antigravity IDE Brain", paths["ag_ide_brain"]))
        
    if not sources:
        print("⚠️ Antigravity brain directories not found.")
        return

    for label, brain_dir in sources:
        print(f"🔍 Scanning plans in {label}: {brain_dir}")
        try:
            conv_dirs = [
                d for d in os.listdir(brain_dir)
                if os.path.isdir(os.path.join(brain_dir, d)) and not d.startswith(".")
            ]
        except Exception as e:
            print(f"❌ Error accessing {brain_dir}: {e}")
            continue

        for conv_id in conv_dirs:
            plan_file = os.path.join(brain_dir, conv_id, "implementation_plan.md")
            if not os.path.isfile(plan_file) or os.path.getsize(plan_file) < 200:
                continue

            stats["plans_scanned"] += 1
            raw_title = extract_plan_title(plan_file)
            slug = slugify(raw_title)
            
            if slug:
                out_name = f"{conv_id}-{slug}.md"
            else:
                out_name = f"{conv_id}-plan.md"
                
            dst_plan = os.path.join(target_plans_dir, out_name)
            
            if force or file_content_differs(plan_file, dst_plan):
                try:
                    shutil.copy2(plan_file, dst_plan)
                    if os.path.exists(dst_plan):
                        stats["plans_synced"] += 1
                        print(f"  ✨ [Plan Copied] {conv_id[:8]}... -> {out_name}")
                except Exception as e:
                    stats["plans_failed"] += 1
                    print(f"  ❌ [Error] Failed to copy plan {conv_id}: {e}")
            else:
                stats["plans_skipped"] += 1

    # Claude Plans 수집
    if paths.get("claude_plans") and os.path.isdir(paths["claude_plans"]):
        print(f"🔍 Scanning Claude plans: {paths['claude_plans']}")
        try:
            for fname in os.listdir(paths["claude_plans"]):
                if not fname.lower().endswith(".md") or fname.startswith("."):
                    continue
                if ".tmp." in fname.lower():
                    continue
                plan_file = os.path.join(paths["claude_plans"], fname)
                if not os.path.isfile(plan_file) or os.path.getsize(plan_file) < 200:
                    continue
                stats["plans_scanned"] += 1
                dst_plan = os.path.join(target_plans_dir, fname)
                if force or file_content_differs(plan_file, dst_plan):
                    try:
                        shutil.copy2(plan_file, dst_plan)
                        if os.path.exists(dst_plan):
                            stats["plans_synced"] += 1
                            print(f"  ✨ [Claude Plan Copied] {fname}")
                    except Exception as e:
                        stats["plans_failed"] += 1
                        print(f"  ❌ [Error] Failed to copy Claude plan {fname}: {e}")
                else:
                    stats["plans_skipped"] += 1
        except Exception as e:
            print(f"❌ Error accessing Claude plans {paths['claude_plans']}: {e}")


def sync_chats(paths, stats, force=False):
    """
    Claude Code 및 Antigravity(IDE) 대화 로그를 my_scrum/chats/raw/ 로 수집하고
    my_scrum/chats/md/ 로 고품질 파싱을 수행합니다. (더미 파일 엄격 필터링)
    """
    print("\n" + "=" * 60)
    print("💬 [2/4] Chats Sync & Markdown Parsing (Claude & Antigravity)")
    print("=" * 60)
    
    raw_dir = os.path.join(paths["scrum_dir"], "chats", "raw")
    md_dir = os.path.join(paths["scrum_dir"], "chats", "md")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    # 1. Claude Projects 수집
    if paths["claude_projects"]:
        print(f"🔍 Scanning Claude projects: {paths['claude_projects']}")
        try:
            for proj_dir in os.listdir(paths["claude_projects"]):
                full_proj = os.path.join(paths["claude_projects"], proj_dir)
                if not os.path.isdir(full_proj):
                    continue
                for fname in os.listdir(full_proj):
                    if not fname.lower().endswith(".jsonl") or fname.startswith("."):
                        continue
                    src_jsonl = os.path.join(full_proj, fname)
                    if not is_valid_session_jsonl(src_jsonl):
                        stats["chats_dummy_filtered"] += 1
                        continue
                    
                    stats["chats_scanned"] += 1
                    dst_jsonl = os.path.join(raw_dir, fname)
                    
                    raw_updated = False
                    if force or file_content_differs(src_jsonl, dst_jsonl):
                        shutil.copy2(src_jsonl, dst_jsonl)
                        stats["chats_raw_synced"] += 1
                        raw_updated = True
                    
                    expected_md_prefix = os.path.splitext(fname)[0]
                    existing_mds = [f for f in os.listdir(md_dir) if expected_md_prefix[:8] in f]
                    
                    if force or raw_updated or not existing_mds:
                        if parse_chat:
                            ok, out_path = parse_chat.process_file(dst_jsonl, output_path=md_dir, overwrite=True, verbose=False)
                            if ok and out_path and is_valid_markdown_chat(out_path):
                                stats["chats_md_parsed"] += 1
                                print(f"  ✅ [Claude Parsed] {fname} -> {os.path.basename(out_path)}")
                            else:
                                if out_path and os.path.exists(out_path):
                                    os.remove(out_path)
                                stats["chats_dummy_filtered"] += 1
                        else:
                            print(f"  ⚠️ parse_chat module not available, skipped MD parsing for {fname}")
                    else:
                        stats["chats_skipped"] += 1
        except Exception as e:
            print(f"❌ Error processing Claude projects: {e}")

    # 2. Antigravity & Antigravity IDE Brain 수집
    ag_sources = []
    if paths["ag_brain"]:
        ag_sources.append(("Antigravity", paths["ag_brain"]))
    if paths["ag_ide_brain"]:
        ag_sources.append(("Antigravity IDE", paths["ag_ide_brain"]))

    for label, brain_dir in ag_sources:
        print(f"🔍 Scanning {label} transcript logs: {brain_dir}")
        try:
            conv_dirs = [
                d for d in os.listdir(brain_dir)
                if os.path.isdir(os.path.join(brain_dir, d)) and not d.startswith(".")
            ]
        except Exception as e:
            print(f"❌ Error accessing {brain_dir}: {e}")
            continue

        for conv_id in conv_dirs:
            log_file = os.path.join(brain_dir, conv_id, ".system_generated", "logs", "transcript.jsonl")
            if not os.path.isfile(log_file):
                continue
            if not is_valid_session_jsonl(log_file):
                stats["chats_dummy_filtered"] += 1
                continue

            stats["chats_scanned"] += 1
            dst_jsonl_name = f"{conv_id}.jsonl"
            dst_jsonl = os.path.join(raw_dir, dst_jsonl_name)
            
            raw_updated = False
            if force or file_content_differs(log_file, dst_jsonl):
                shutil.copy2(log_file, dst_jsonl)
                stats["chats_raw_synced"] += 1
                raw_updated = True

            existing_mds = [f for f in os.listdir(md_dir) if conv_id[:8] in f]
            if force or raw_updated or not existing_mds:
                if parse_chat:
                    ok, out_path = parse_chat.process_file(dst_jsonl, output_path=md_dir, overwrite=True, verbose=False)
                    if ok and out_path and is_valid_markdown_chat(out_path):
                        stats["chats_md_parsed"] += 1
                        print(f"  ✅ [{label} Parsed] {conv_id[:8]}... -> {os.path.basename(out_path)}")
                    else:
                        if out_path and os.path.exists(out_path):
                            os.remove(out_path)
                        stats["chats_dummy_filtered"] += 1
                else:
                    print(f"  ⚠️ parse_chat module not available, skipped MD parsing for {conv_id}")
            else:
                stats["chats_skipped"] += 1


def mirror_to_obsidian(paths, stats, force=False):
    """
    my_scrum 내의 chats(raw/md), plans, daily, monthly, total 디렉터리를
    Obsidian Vault/raw/sources/2-Areas/Work-Logs/ 로 1:1 고속 미러링합니다.
    """
    print("\n" + "=" * 60)
    print("🔄 [3/4] Obsidian Vault 1:1 Mirroring")
    print("=" * 60)
    
    if not paths["obsidian_dir"]:
        print("⚠️ Obsidian Vault directory not found. Skipping 1:1 mirror.")
        return

    work_logs_raw = os.path.join(paths["obsidian_dir"], "raw", "sources", "2-Areas", "Work-Logs")
    os.makedirs(work_logs_raw, exist_ok=True)
    
    sync_targets = [
        ("plans", os.path.join(paths["scrum_dir"], "plans"), os.path.join(work_logs_raw, "plans")),
        ("chats/raw", os.path.join(paths["scrum_dir"], "chats", "raw"), os.path.join(work_logs_raw, "chats", "raw")),
        ("chats/md", os.path.join(paths["scrum_dir"], "chats", "md"), os.path.join(work_logs_raw, "chats", "md")),
        ("daily", os.path.join(paths["scrum_dir"], "daily"), os.path.join(work_logs_raw, "daily")),
        ("monthly", os.path.join(paths["scrum_dir"], "monthly"), os.path.join(work_logs_raw, "monthly")),
        ("total", os.path.join(paths["scrum_dir"], "total"), os.path.join(work_logs_raw, "total")),
    ]

    for label, src_dir, dst_dir in sync_targets:
        if not os.path.exists(src_dir):
            continue
        os.makedirs(dst_dir, exist_ok=True)
        
        src_files = set(os.listdir(src_dir))
        dst_files = set(os.listdir(dst_dir))
        
        # 1. 삭제된 파일 Obsidian Vault에서도 제거 (클린 동기화)
        for d_file in (dst_files - src_files):
            del_path = os.path.join(dst_dir, d_file)
            if os.path.isfile(del_path):
                os.remove(del_path)

        # 2. 신규 및 변경 파일 복사
        copied_count = 0
        for f in src_files:
            s_path = os.path.join(src_dir, f)
            if not os.path.isfile(s_path):
                continue
            d_path = os.path.join(dst_dir, f)
            if force or file_content_differs(s_path, d_path):
                shutil.copy2(s_path, d_path)
                copied_count += 1
                stats["obsidian_mirrored"] += 1
        
        print(f"  📂 Mirrored '{label}': {copied_count} files updated/copied (Total {len(src_files)} files in dir)")


def compile_wiki(paths):
    """
    Obsidian Vault의 wiki/build.py 컴파일러를 실행하여 위키 대시보드 및 인덱스를 최신화합니다.
    """
    print("\n" + "=" * 60)
    print("🚀 [4/4] LLM Wiki Auto-Compilation (build.py)")
    print("=" * 60)
    
    if not paths["obsidian_dir"]:
        print("⚠️ Obsidian Vault not found. Skipping build.py execution.")
        return
        
    build_py = os.path.join(paths["obsidian_dir"], "wiki", "build.py")
    if not os.path.isfile(build_py):
        print(f"⚠️ build.py not found at: {build_py}")
        return

    try:
        res = subprocess.run([sys.executable, build_py], cwd=paths["obsidian_dir"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0:
            print(f"✅ Wiki Build Success:\n{res.stdout.strip()}")
        else:
            print(f"❌ Wiki Build Failed (code {res.returncode}):\n{res.stderr.strip()}")
    except Exception as e:
        print(f"❌ Error invoking build.py: {e}")


def print_summary(stats, elapsed_time):
    """
    전체 실행 통계 요약을 출력합니다.
    """
    print("\n" + "=" * 60)
    print(f"✨ Session & Plan Sync Pipeline Completed in {elapsed_time:.2f}s")
    print("=" * 60)
    print(f"- Dummy Cleaned: {stats['dummy_cleaned']} files removed")
    print(f"- Plans: {stats['plans_scanned']} scanned | {stats['plans_synced']} synced | {stats['plans_skipped']} skipped | {stats['plans_failed']} failed")
    print(f"- Chats: {stats['chats_scanned']} scanned | {stats['chats_raw_synced']} raw synced | {stats['chats_md_parsed']} parsed MD | {stats['chats_skipped']} skipped | {stats['chats_dummy_filtered']} dummy filtered")
    print(f"- Obsidian 1:1 Mirrored: {stats['obsidian_mirrored']} files updated")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Sync & Parse Claude Code & Antigravity (IDE) Sessions & Plans to my_scrum & Obsidian Vault"
    )
    parser.add_argument("--force", "-f", action="store_true", help="Force re-sync and re-parse all files")
    parser.add_argument("--skip-mirror", action="store_true", help="Skip 1:1 mirror to Obsidian Vault")
    parser.add_argument("--skip-build", action="store_true", help="Skip wiki/build.py execution")
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    paths = detect_paths()
    
    print("=" * 60)
    print("🚀 Claude Code & Antigravity Sessions Sync Pipeline")
    print("=" * 60)
    print(f"• User Home       : {paths['home']}")
    print(f"• Claude Projects : {paths['claude_projects'] or 'NOT FOUND'}")
    print(f"• Antigravity     : {paths['ag_brain'] or 'NOT FOUND'}")
    print(f"• Antigravity IDE : {paths['ag_ide_brain'] or 'NOT FOUND'}")
    print(f"• my_scrum Target : {paths['scrum_dir']}")
    print(f"• Obsidian Target : {paths['obsidian_dir'] or 'NOT FOUND'}")
    
    stats = {
        "dummy_cleaned": 0,
        "plans_scanned": 0,
        "plans_synced": 0,
        "plans_skipped": 0,
        "plans_failed": 0,
        "chats_scanned": 0,
        "chats_raw_synced": 0,
        "chats_md_parsed": 0,
        "chats_skipped": 0,
        "chats_dummy_filtered": 0,
        "chats_failed": 0,
        "obsidian_mirrored": 0
    }
    
    # 0. Clean up existing dummy / empty files
    cleanup_dummy_files(paths, stats)

    # 1. Plans Sync
    sync_plans(paths, stats, force=args.force)
    
    # 2. Chats Sync & Parse
    sync_chats(paths, stats, force=args.force)
    
    # 3. Mirror to Obsidian
    if not args.skip_mirror:
        mirror_to_obsidian(paths, stats, force=args.force)
        
    # 4. Compile Wiki
    if not args.skip_build and not args.skip_mirror:
        compile_wiki(paths)
        
    elapsed = (datetime.now() - start_time).total_seconds()
    print_summary(stats, elapsed)


if __name__ == "__main__":
    main()
