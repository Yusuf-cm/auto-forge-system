# vmr_tools/director_ai.py
# AutoForge: DirectorAI — Fix Mode + Improve Mode orchestrator
import os
import json
import re
from vmr_tools.base_ai import BaseAI


class DirectorAI(BaseAI):
    """
    The Orchestrator of Evolution.

    FIX MODE    — Two-stage Socratic repair loop.
                  Stage 1: Manifesto (diagnose why it failed)
                  Stage 2: Apply Fix (rewrite only targeted files)

    IMPROVE MODE — Brand-driven visual redesign guided by Design Critic.
                   Reads functionality.txt to preserve all working behaviour.
                   Hard safety gate blocks modification of config/test files.
    """

    TS_RULES = """
<typescript_rules>
RULE 1 — CAMELCASE KEYS (CRITICAL):
JavaScript and TypeScript style objects MUST use camelCase keys ONLY.
NEVER use hyphenated keys like 'hero-content', 'stats-bar', 'program-card'.
Hyphenated keys are CSS syntax. In TypeScript they cause "Expected a semicolon" errors.
CORRECT:   heroContent, statsBar, programCard, contactSection
INCORRECT: hero-content, stats-bar, program-card, contact-section

RULE 2 — FULL FILE OUTPUT:
Every <file> block MUST contain the COMPLETE file content from first to last line.
NEVER truncate. NEVER write "// ... rest of file" or similar shortcuts.

RULE 3 — NO CONSOLE.LOG in production files.

RULE 4 — NO body height:100vh.
Setting height:100vh on body collapses multi-section pages. Use min-height on sections.

RULE 5 — REAL TAILWIND OR PURE CSS ONLY.
Do not invent Tailwind class names that reference CSS variables.
bg-primary-accent is NOT a real Tailwind class. Use inline styles or standard utilities.

RULE 6 — CSS VARIABLES: All brand colors must be defined in :root in globals.css
and referenced via var(--name) everywhere. Never hardcode hex values in components.

RULE 7 — ONE DEFAULT EXPORT per React component file.
</typescript_rules>"""

    # ── Protection Lists ──────────────────────────────────────────────────
    
    # IMPROVE MODE: Never touch config or tests during visual redesign
    IMPROVE_PROTECTED_FILES = {
        'autoforge.json', 'package.json', 'tsconfig.json',
        'next.config.js', 'next.config.ts', 'next.config.mjs',
        'jest.config.js', 'jest.config.ts',
        '.eslintrc.json', '.prettierrc',
        'tailwind.config.js', 'tailwind.config.ts',
    }
    IMPROVE_PROTECTED_PATTERNS = ['tests/', '__tests__/', '.test.', '.spec.']

    # FIX MODE: Can modify almost anything to get the build passing, except the orchestration recipe
    FIX_PROTECTED_FILES = {'autoforge.json'}
    FIX_PROTECTED_PATTERNS =[]

    def __init__(self):
        super().__init__()
        self.RECIPE_SCHEMA = {
            "project_name": "string",
            "version": "string",
            "framework": "string",
            "language": "string",
            "install_command": "string",
            "build_command": "string",
            "test_command": "string",
            "start_command": "string",
            "deploy_command": "string (MUST start with npx)",
            "entry_point": "string",
            "timeout_seconds": 300
        }

    # ══════════════════════════════════════════════════════════
    # FIX MODE
    # ══════════════════════════════════════════════════════════

    def run_evolution_cycle(self, project_name, source_dir, saga, violation_brief: str = ""):
        """
        FIX MODE: Two-stage Socratic repair loop.
        Called when the pipeline is failing.
        """
        print(f"  [Director] FIX MODE: Diagnosing '{project_name}'...")
        codebase = self._read_directory_to_string(source_dir)
        if not codebase:
            print("[Director] ERROR: Could not read codebase.")
            return None

        manifesto = self._generate_manifesto(codebase, saga, violation_brief)
        if not manifesto:
            print("  [Director] Stage 1 (Manifesto) failed.")
            return None

        files_targeted = manifesto.get('files_to_modify',[])
        
        # ── Fix Mode Safety Gate: Only block autoforge.json ─────────
        safe_targets = []
        blocked_targets =[]
        for f in files_targeted:
            filename = f.split('/')[-1]
            if filename in self.FIX_PROTECTED_FILES:
                blocked_targets.append(f)
            else:
                safe_targets.append(f)
                
        if blocked_targets:
            print(f"  [Director] FIX MODE safety gate blocked targeting: {blocked_targets}")
            
        manifesto['files_to_modify'] = safe_targets
        
        print(f"  [Director] Manifesto accepted. Targeting: {safe_targets}")
        
        # Token Diet: Pass source_dir instead of full codebase so we only read targeted files
        return self._apply_fix(manifesto, source_dir)

    def _generate_manifesto(self, codebase, saga, violation_brief: str = ""):
        """Stage 1 of FIX MODE — diagnose and plan."""

        enforcer_block = ""
        if violation_brief:
            enforcer_block = f"""
<enforcer_violations>
{violation_brief}

These violations were caught by the deterministic CodeEnforcer pre-build scan.
They MUST be included in files_to_modify and corrected.
Do NOT omit them even if the build log does not mention them.
</enforcer_violations>
"""

        prompt = f"""
<task>
You are the AutoForge Director in DIAGNOSTIC MODE.
Analyse the codebase and the Saga (pipeline failure report).
Produce a precise JSON Evolution Manifesto identifying what must change and why.
</task>

<input_saga>
{json.dumps(saga, indent=2)}
</input_saga>
{enforcer_block}
<input_codebase>
{codebase}
</input_codebase>

<instruction>
1. Focus on failed_step and error_summary in the Saga.
2. Identify the MINIMUM set of files that must change to fix the failure.
3. Do NOT include files that do not need changes.
4. If error is in autoforge.json commands, propose using 'npx' prefix.
5. Include any files flagged in enforcer_violations above.
6. Produce JSON with these exact keys:
   - files_to_modify: array of file path strings
   - reason: string — root cause explanation
   - correction: string — exact change needed
   - recipe_constraints: object — autoforge.json schema reminders
</instruction>

<output_format>
Single valid JSON object only. No preamble. No commentary.
</output_format>
"""
        raw = self._call_llm(prompt, temperature=0.1)
        if not raw:
            return None
        return self._parse_json_safe(raw)

    def _apply_fix(self, manifesto, source_dir):
        """Stage 2 of FIX MODE — rewrite targeted files."""
        
        # TOKEN DIET: Read ONLY the files we actually need to fix
        targeted_code = ""
        for rel_path in manifesto.get('files_to_modify',[]):
            full_path = os.path.join(source_dir, rel_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    targeted_code += f'<file path="{rel_path}">\n{f.read()}\n</file>\n\n'
            else:
                targeted_code += f'<file path="{rel_path}">\n// File does not exist yet. Please create it.\n</file>\n\n'

        prompt = f"""
<task>
You are the AutoForge Director in FIX MODE.
Apply the corrections defined in the Evolution Manifesto.
Rewrite ONLY the files listed in files_to_modify.
</task>

<evolution_manifesto>
{json.dumps(manifesto, indent=2)}
</evolution_manifesto>

<original_targeted_files>
{targeted_code}
</original_targeted_files>

{self.TS_RULES}

<instruction>
1. Rewrite ONLY files in files_to_modify.
2. Apply the correction precisely.
3. Preserve all standard scripts in package.json (dev, build, start, test).
4. deploy_command in autoforge.json MUST start with 'npx'.
   Schema: {json.dumps(self.RECIPE_SCHEMA)}
</instruction>

<output_format>
Output ONLY <file path="path/to/file">FULL FILE CONTENT</file> blocks.
No preamble. No commentary. No partial files.
</output_format>
"""
        raw = self._call_llm(prompt, temperature=0.2, max_tokens=8000)
        if not raw:
            return None
            
        modifications = self._parse_file_blocks(raw)
        if not modifications:
            return None
            
        # ── Final safety check on output (Fix Mode) ─────────────────
        safe_modifications = {}
        for filepath, code in modifications.items():
            filename = filepath.split('/')[-1]
            if filename not in self.FIX_PROTECTED_FILES:
                safe_modifications[filepath] = code
            else:
                print(f"  [Director] FIX MODE safety gate removed output: {filepath}")

        return safe_modifications

    # ══════════════════════════════════════════════════════════
    # IMPROVE MODE
    # ══════════════════════════════════════════════════════════

    def run_improvement_cycle(self, project_name, source_dir, design_critique, seed_texts=None):
        """
        IMPROVE MODE: Rewrites UI files based on Design Critic brief.
        Reads functionality.txt to preserve all working behaviour.
        Called when the pipeline is passing and design needs improvement.
        """
        print(f"  [Director] IMPROVE MODE: Applying design improvements to '{project_name}'...")
        codebase = self._read_directory_to_string(source_dir)
        if not codebase:
            print("[Director] ERROR: Could not read codebase.")
            return None

        files_to_modify = design_critique.get('files_to_modify',[
            'app/page.tsx', 'app/globals.css', 'app/layout.tsx'
        ])

        # ── Improve Mode Safety gate: strip tests and configs ────────────────
        safe_files = []
        blocked_files =[]
        for f in files_to_modify:
            filename = f.split('/')[-1]
            is_protected = (
                filename in self.IMPROVE_PROTECTED_FILES or
                any(pattern in f for pattern in self.IMPROVE_PROTECTED_PATTERNS)
            )
            if is_protected:
                blocked_files.append(f)
            else:
                safe_files.append(f)

        if blocked_files:
            print(f"  [Director] IMPROVE MODE safety gate blocked: {blocked_files}")
        if not safe_files:
            print("  [Director] No safe files to modify. Aborting.")
            return None

        # ── Build functionality preservation block ─────────────
        functionality_block = ""
        if seed_texts:
            functionality = seed_texts.get('functionality.txt', '')
            if functionality:
                functionality_block = f"""
<functionality_preservation>
CRITICAL: This site has required capabilities that MUST be preserved.
When rewriting UI files you must keep all interactive behaviour intact.

Capability specification:
{functionality}

NEVER remove or break any of the following when rewriting files:
- onClick handlers on buttons (especially Add to Cart, form submit, nav toggle)
- onSubmit handlers on forms
- useState and useReducer calls
- fetch() calls to API routes in form submission handlers
- localStorage read/write in useEffect
- Prop types and signatures that components receive from page.tsx
- The useReducer dispatch calls in page.tsx (ADD_ITEM, REMOVE_ITEM, etc.)
- API route files (app/api/**) — these are in PROTECTED and should not appear in files_to_modify anyway

You MAY change: colors, fonts, spacing, layout, copy, animations, hover effects.
You MUST NOT change: any working interactive functionality.
</functionality_preservation>
"""

        score = design_critique.get('design_score', 'unknown')
        improvements = design_critique.get('improvements',[])

        prompt = f"""
<task>
You are the AutoForge Director in IMPROVE MODE.
The Design Critic has scored the current website and identified weaknesses.
Rewrite ONLY the UI files listed below to implement the improvements.
</task>

<design_critic_brief>
Current design score: {score}/10

Improvements required:
{json.dumps(improvements, indent=2)}

Full critique:
{json.dumps(design_critique, indent=2)}
</design_critic_brief>

<current_codebase>
{codebase}
</current_codebase>

{functionality_block}

{self.TS_RULES}

<files_to_rewrite>
{json.dumps(safe_files, indent=2)}
</files_to_rewrite>

<instruction>
1. Rewrite ONLY the files listed in files_to_rewrite.
2. Implement ALL improvements from the Design Critic brief.
3. Brand colors from the brief MUST appear as CSS variables in :root.
   Use exact hex codes — never approximate.
4. If a Google Font is specified, add the @import to globals.css.
5. NEVER set height:100vh on body — it collapses multi-section pages.
6. NEVER invent Tailwind class names that reference CSS variables.
7. Preserve all working interactive functionality as defined above.
</instruction>

<output_format>
Output ONLY <file path="path/to/file">FULL FILE CONTENT</file> blocks.
No preamble. No commentary. No partial files.
</output_format>
"""
        raw = self._call_llm(prompt, temperature=0.3, max_tokens=8000)
        if not raw:
            return None

        modifications = self._parse_file_blocks(raw)
        if not modifications:
            return None

        # ── Final safety check on output (Improve Mode) ──────────────────────
        safe_modifications = {}
        for filepath, code in modifications.items():
            filename = filepath.split('/')[-1]
            is_protected = (
                filename in self.IMPROVE_PROTECTED_FILES or
                any(pattern in filepath for pattern in self.IMPROVE_PROTECTED_PATTERNS)
            )
            if not is_protected:
                safe_modifications[filepath] = code
            else:
                print(f"  [Director] IMPROVE MODE safety gate removed output: {filepath}")

        print(f"  [Director] Files produced: {list(safe_modifications.keys())}")
        return safe_modifications

    # ══════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════

    def _parse_file_blocks(self, raw_output):
        """Extracts <file path="...">content</file> blocks."""
        files = {}
        blocks = re.findall(r'<file path="(.*?)">(.*?)</file>', raw_output, re.DOTALL)
        for path, code in blocks:
            files[path.strip()] = code.strip()
        return files