# -*- coding: utf-8 -*-
"""
repo_qa.py - Local repository question answering for Jarvis.

This module keeps codebase answers offline and source-grounded. It does not try
to hallucinate architecture; it reads project files, finds matching symbols and
paths, and returns concise explanations anchored to the local repo.
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from codebase_manager import CodebaseManager


STOP_WORDS = {
    "a", "about", "an", "and", "are", "can", "does", "explain", "file", "how",
    "in", "is", "me", "module", "of", "repo", "repository", "show", "tell",
    "the", "this", "what", "where", "which", "who", "why",
}


class RepoQuestionAnswerer:
    def __init__(self, project_root: str = None):
        self.manager = CodebaseManager(project_root=project_root)
        self._file_cache = self.manager.list_project_files()
        self._path_index = {}
        for file_info in self._file_cache:
            normalized = self._normalize_path(file_info["path"])
            self._path_index[normalized] = file_info["path"]

    def matches(self, prompt: str) -> bool:
        text = (prompt or "").strip()
        lowered = text.lower()

        if re.search(r"[a-zA-Z0-9_./-]+\.(py|md|json|yaml|yml|toml|txt)\b", text):
            return True

        if re.search(r"\b(where is|which file|what file|what does|how does|explain|summarize|walk me through)\b", lowered):
            if re.search(r"\b(code|repo|repository|file|module|class|function|method|symbol|implementation)\b", lowered):
                return True
            if self._extract_identifier_candidates(text):
                return True

        if re.search(r"\b(class|function|method|module|symbol|implementation)\b", lowered):
            return True

        return False

    def get_repo_stats(self) -> dict:
        python_files = [item for item in self._file_cache if item["path"].endswith(".py")]
        return {
            "indexed_files": len(self._file_cache),
            "python_files": len(python_files),
        }

    def answer(self, question: str) -> str:
        explicit_paths = self._find_explicit_paths(question)
        candidates, hits_by_file = self._find_candidate_files(question, explicit_paths)

        if not candidates:
            return (
                "I couldn't map that question to a repo file yet. Try asking with a filename, path, or symbol, "
                "for example `explain core/main_loop.py` or `where is PluginLoader used?`"
            )

        primary = candidates[0]
        display_primary = self._display_path(primary)
        primary_content = self.manager.read_file(primary)
        summary = self._summarize_file(primary, primary_content, question, hits_by_file.get(primary, []))

        related_lines = []
        for file_path in candidates[:3]:
            for hit in hits_by_file.get(file_path, [])[:3]:
                related_lines.append(
                    f"- {self._display_path(hit['file'])}:{hit['line']} -> {hit['content'].strip()}"
                )

        related_files = "\n".join(f"- {self._display_path(path)}" for path in candidates[:3])
        lines = [
            f"Repo answer based on local code:",
            f"Best match: {display_primary}",
            summary,
        ]

        if related_files:
            lines.extend(["Related files:", related_files])

        if related_lines:
            lines.extend(["Relevant lines:", "\n".join(related_lines)])

        lines.append("Ask a deeper follow-up with a path or symbol if you want a more targeted walkthrough.")
        return "\n".join(lines)

    def _find_explicit_paths(self, question: str) -> List[str]:
        matches = re.findall(r"([a-zA-Z0-9_./-]+\.(?:py|md|json|yaml|yml|toml|txt))", question)
        resolved = []
        for match in matches:
            normalized = self._normalize_path(match)
            if normalized in self._path_index:
                resolved.append(self._path_index[normalized])
                continue

            for indexed_path, original_path in self._path_index.items():
                if indexed_path.endswith(normalized):
                    resolved.append(original_path)
                    break
        return resolved

    def _normalize_path(self, path: str) -> str:
        return (path or "").replace("\\", "/").lstrip("./").lower()

    def _display_path(self, path: str) -> str:
        return (path or "").replace("\\", "/")

    def _extract_identifier_candidates(self, question: str) -> List[str]:
        raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", question)
        keep = []
        for token in raw_tokens:
            lowered = token.lower()
            if lowered in STOP_WORDS:
                continue
            keep.append(token)
        return keep[:8]

    def _find_candidate_files(self, question: str, explicit_paths: List[str]) -> Tuple[List[str], Dict[str, List[dict]]]:
        file_scores = Counter()
        hits_by_file: Dict[str, List[dict]] = defaultdict(list)
        explicit_ranked = list(dict.fromkeys(explicit_paths))
        explicit_set = set(explicit_ranked)

        for path in explicit_ranked:
            file_scores[path] += 20

        identifiers = self._extract_identifier_candidates(question)
        for identifier in identifiers:
            results = self.manager.search_code(identifier)
            for result in results:
                file_scores[result["file"]] += 3
                hits_by_file[result["file"]].append(result)

        lowered_question = question.lower()
        for file_info in self._file_cache:
            basename = os.path.basename(file_info["path"]).lower()
            stem = os.path.splitext(basename)[0]
            if basename in lowered_question or stem in lowered_question:
                file_scores[file_info["path"]] += 6

        ranked = explicit_ranked[:]
        ranked.extend(
            file_path
            for file_path, _ in file_scores.most_common(5)
            if file_path not in explicit_set
        )
        return ranked, hits_by_file

    def _summarize_file(self, file_path: str, content: str, question: str, hits: List[dict]) -> str:
        if not content or content.startswith("[Error]"):
            return "I found a likely file match, but I couldn't read it safely."

        module_doc = self._extract_module_doc(content)
        defs = self._extract_defs(content)
        classes = self._extract_classes(content)
        question_identifiers = {token.lower() for token in self._extract_identifier_candidates(question)}

        matching_defs = [item for item in defs if item[0].lower() in question_identifiers]
        matching_classes = [item for item in classes if item[0].lower() in question_identifiers]

        lines = []
        if module_doc:
            lines.append(f"Summary: {module_doc}")

        if matching_classes:
            rendered = ", ".join(f"{name} (line {line})" for name, line in matching_classes[:5])
            lines.append(f"Matching classes: {rendered}")
        elif classes:
            rendered = ", ".join(f"{name} (line {line})" for name, line in classes[:5])
            lines.append(f"Top classes: {rendered}")

        if matching_defs:
            rendered = ", ".join(f"{name} (line {line})" for name, line in matching_defs[:8])
            lines.append(f"Matching functions: {rendered}")
        elif defs:
            rendered = ", ".join(f"{name} (line {line})" for name, line in defs[:8])
            lines.append(f"Top functions: {rendered}")

        if hits:
            preview = self._build_hit_preview(file_path, content, hits[:3])
            if preview:
                lines.append(f"Local evidence:\n{preview}")

        return "\n".join(lines)

    def _extract_module_doc(self, content: str) -> str:
        match = re.search(r'^\s*(?:"""|\'\'\')([\s\S]*?)(?:"""|\'\'\')', content)
        if not match:
            return ""
        first_line = match.group(1).strip().splitlines()[0].strip()
        return first_line

    def _extract_defs(self, content: str) -> List[Tuple[str, int]]:
        results = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = re.match(r"\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if match:
                results.append((match.group(1), line_number))
        return results

    def _extract_classes(self, content: str) -> List[Tuple[str, int]]:
        results = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = re.match(r"\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[:(]", line)
            if match:
                results.append((match.group(1), line_number))
        return results

    def _build_hit_preview(self, file_path: str, content: str, hits: List[dict]) -> str:
        lines = content.splitlines()
        rendered = []
        seen = set()
        display_path = self._display_path(file_path)
        for hit in hits:
            line_number = hit.get("line", 0)
            if not line_number or line_number in seen:
                continue
            seen.add(line_number)
            start = max(1, line_number - 1)
            end = min(len(lines), line_number + 1)
            snippet = []
            for idx in range(start, end + 1):
                snippet.append(f"  {display_path}:{idx}: {lines[idx - 1]}")
            rendered.append("\n".join(snippet))
        return "\n".join(rendered)
