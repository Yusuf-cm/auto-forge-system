# vmr_tools/code_enforcer.py
# Phase 1: Deterministic pre-build enforcement layer. No LLM calls.

import os
import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class EnforcementReport:
    auto_fixed: List[str] = field(default_factory=list)
    violations: List[dict] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    def summary(self) -> str:
        lines = ["\n[CodeEnforcer] Pre-build scan:"]
        if self.auto_fixed:
            lines.append(f"  Auto-fixed {len(self.auto_fixed)} file(s):")
            for f in self.auto_fixed:
                lines.append(f"    ✓ {f}")
        if self.violations:
            lines.append(f"  {len(self.violations)} violation(s) escalated to Director:")
            for v in self.violations:
                lines.append(f"    ✗ {v['file']}:{v['line']} — {v['message']}")
        if not self.auto_fixed and not self.violations:
            lines.append("  All checks passed. No issues found.")
        return "\n".join(lines)

    def violation_brief(self) -> str:
        if not self.violations:
            return ""
        lines =[
            "CODEENFORCER VIOLATIONS — these must be fixed in the next cycle:",
            "These are functional defects, not style issues. Fix every one.",
        ]
        for v in self.violations:
            lines.append(f"  - {v['file']} (line {v['line']}): {v['message']}")
            if v.get("context"):
                lines.append(f"    Context: {v['context']}")
        return "\n".join(lines)


class CodeEnforcer:
    USE_CLIENT_DIRECTIVE = "'use client'"

    HOOK_PATTERN = re.compile(
        r'\b(useState|useEffect|useReducer|useCallback|useRef|useMemo|useContext|useId|useTransition|useDeferredValue)\b'
    )
    EVENT_HANDLER_PROP_PATTERN = re.compile(r'\bon[A-Z]\w+=\{')
    BUTTON_OPEN_TAG_PATTERN = re.compile(r'<button\b((?:[^>]|(?<=\\)>)*?)>', re.DOTALL)
    ON_CLICK_ATTR_PATTERN = re.compile(r'\bonClick\b')

    FAKE_TAILWIND_CLASSES =[
        (re.compile(r'\btext-text-muted\b'),    "style={{ color: 'var(--text-muted)' }}"),
        (re.compile(r'\btext-text\b'),           "style={{ color: 'var(--text)' }}"),
        (re.compile(r'\btext-accent-warm\b'),    "style={{ color: 'var(--accent-warm)' }}"),
        (re.compile(r'\btext-accent\b'),         "style={{ color: 'var(--accent)' }}"),
        (re.compile(r'\btext-bg\b'),             "style={{ color: 'var(--bg)' }}"),
        (re.compile(r'\bbg-surface\b'),          "style={{ backgroundColor: 'var(--surface)' }}"),
        (re.compile(r'\bbg-accent\b'),           "style={{ backgroundColor: 'var(--accent)' }}"),
        (re.compile(r'\bbg-accent-warm\b'),      "style={{ backgroundColor: 'var(--accent-warm)' }}"),
        (re.compile(r'\bbg-bg\b'),               "style={{ backgroundColor: 'var(--bg)' }}"),
        (re.compile(r'\bborder-border\b'),       "style={{ borderColor: 'var(--border)' }}"),
        (re.compile(r'\bborder-accent\b'),       "style={{ borderColor: 'var(--accent)' }}"),
        (re.compile(r'\bborder-accent-warm\b'),  "style={{ borderColor: 'var(--accent-warm)' }}"),
        (re.compile(r'\bfont-playfair\b'),       "style={{ fontFamily: 'Playfair Display, serif' }}"),
        (re.compile(r'\bfont-dm-sans\b'),        "style={{ fontFamily: 'DM Sans, sans-serif' }}"),
    ]

    CLASSNAME_PATTERN = re.compile(r'className=["\`]([^"\`]+)["\`]')
    SKIP_DIRS = {'node_modules', '.next', 'dist', 'build', '.vercel', '.git', '__pycache__'}

    def enforce(self, project_dir: str) -> EnforcementReport:
        report = EnforcementReport()

        # RULE 5: Core File Existence Check
        self._rule5_core_files_exist(report, project_dir)

        components_dir = os.path.join(project_dir, "components")
        if os.path.isdir(components_dir):
            for fname in sorted(os.listdir(components_dir)):
                if fname.endswith(".tsx"):
                    fpath = os.path.join(components_dir, fname)
                    self._rule1_component_use_client(fpath, report, project_dir)

        page_path = os.path.join(project_dir, "app", "page.tsx")
        if os.path.isfile(page_path):
            self._rule2_page_use_client(page_path, report, project_dir)

        for fpath in self._walk_tsx(project_dir):
            self._rule3_button_onclick(fpath, report, project_dir)
            self._rule4_fake_tailwind_classes(fpath, report, project_dir)

        print(report.summary())
        return report

    def _rule1_component_use_client(self, fpath: str, report: EnforcementReport, project_dir: str):
        content = self._read(fpath)
        if self._has_use_client(content):
            return
        if self.HOOK_PATTERN.search(content):
            self._write(fpath, self._prepend_directive(content))
            rel = os.path.relpath(fpath, project_dir)
            report.auto_fixed.append(f"{rel} → added 'use client' (uses React hooks)")

    def _rule2_page_use_client(self, fpath: str, report: EnforcementReport, project_dir: str):
        content = self._read(fpath)
        if self._has_use_client(content):
            return
        uses_hooks = bool(self.HOOK_PATTERN.search(content))
        passes_handlers = bool(self.EVENT_HANDLER_PROP_PATTERN.search(content))
        if uses_hooks or passes_handlers:
            self._write(fpath, self._prepend_directive(content))
            reason =[]
            if uses_hooks:
                reason.append("uses React hooks")
            if passes_handlers:
                reason.append("passes event handler props to components")
            report.auto_fixed.append(f"app/page.tsx → added 'use client' ({'; '.join(reason)})")

    def _rule3_button_onclick(self, fpath: str, report: EnforcementReport, project_dir: str):
        content = self._read(fpath)
        for match in self.BUTTON_OPEN_TAG_PATTERN.finditer(content):
            attrs = match.group(1)
            if self.ON_CLICK_ATTR_PATTERN.search(attrs):
                continue
            if 'type="submit"' in attrs or "type='submit'" in attrs:
                continue
            line_num = content[: match.start()].count("\n") + 1
            rel = os.path.relpath(fpath, project_dir)
            context_snippet = match.group(0)
            if len(context_snippet) > 100:
                context_snippet = context_snippet[:97] + "..."
            report.violations.append({
                "file": rel,
                "line": line_num,
                "message": "<button> has no onClick handler — will render but do nothing",
                "context": context_snippet,
                "rule": 3,
            })

    def _rule4_fake_tailwind_classes(self, fpath: str, report: EnforcementReport, project_dir: str):
        content = self._read(fpath)
        rel = os.path.relpath(fpath, project_dir)

        for cm in self.CLASSNAME_PATTERN.finditer(content):
            class_string = cm.group(1)
            line_num = content[: cm.start()].count("\n") + 1

            for fake_pattern, replacement in self.FAKE_TAILWIND_CLASSES:
                if fake_pattern.search(class_string):
                    fake_class = fake_pattern.pattern.replace(r'\b', '')
                    report.violations.append({
                        "file": rel,
                        "line": line_num,
                        "message": (
                            f"Fake Tailwind class '{fake_class}' — not a real utility, "
                            f"silently ignored at build time. "
                            f"Replace with: {replacement}"
                        ),
                        "context": f'className="...{fake_class}..."',
                        "rule": 4,
                    })

    def _rule5_core_files_exist(self, report: EnforcementReport, project_dir: str):
        """
        Rule 5: Ensures the absolute minimum files needed to render a Next.js App Router
        site exist. If the LLM rate limited and forgot to generate the page, escalate it.
        """
        required_files =[
            "app/page.tsx",
            "app/layout.tsx",
            "app/globals.css"
        ]
        
        for rel_path in required_files:
            full_path = os.path.join(project_dir, rel_path)
            if not os.path.isfile(full_path):
                report.violations.append({
                    "file": rel_path,
                    "line": 1,
                    "message": f"CRITICAL: {rel_path} is completely missing. You MUST generate this file for the Next.js app to render.",
                    "context": "File missing due to LLM generation truncation.",
                    "rule": 5,
                })

    def _has_use_client(self, content: str) -> bool:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped in ("'use client'", '"use client"', "'use client';", '"use client";')
        return False

    def _prepend_directive(self, content: str) -> str:
        return f"{self.USE_CLIENT_DIRECTIVE}\n\n{content}"

    def _walk_tsx(self, root: str) -> List[str]:
        results =[]
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] =[d for d in dirnames if d not in self.SKIP_DIRS]
            for fname in filenames:
                if fname.endswith(".tsx"):
                    results.append(os.path.join(dirpath, fname))
        return results

    def _read(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write(self, path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)