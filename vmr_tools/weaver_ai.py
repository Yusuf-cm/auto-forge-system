# vmr_tools/weaver_ai.py
# AutoForge: WeaverAI — Functional codebase generation from seed texts
import os
import json
import re
from vmr_tools.base_ai import BaseAI


class WeaverAI(BaseAI):
    """
    The Architect. Generates a complete, functional, working codebase
    from seed texts and a bootstrap reference.

    The bootstrap teaches HOW to structure a Next.js project.
    The seed texts define WHAT to build.
    These are never the same thing.

    Generation flow:
      1. Read bootstrap (structure reference) + project seed texts
      2. Inject functionality.txt as hard capability requirements
      3. Generate full codebase via LLM
      4. Recover autoforge.json if omitted (stage 2)
      5. Enforce deploy_command npx prefix
    """

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
            "deploy_command": "string — MUST start with 'npx'",
            "entry_point": "string",
            "timeout_seconds": 300
        }

    def create_universe(self, seed_texts, bootstrap_path, template_content=None):
        """
        Generates a complete project codebase from seed texts.

        Args:
            seed_texts:       dict of {filename: content} from project seed_texts/
            bootstrap_path:   path to bootstrap template folder
            template_content: optional dict of selected templates (Phase 2)

        Returns:
            dict of {filepath: code} or None on total failure
        """
        print("  [WeaverAI] Ingesting bootstrap reference and seed texts...")

        source_path = os.path.join(bootstrap_path, "source_code")
        seed_path   = os.path.join(bootstrap_path, "seed_texts")

        bootstrap_code  = self._read_directory_to_string(source_path)
        bootstrap_brief = self._read_directory_to_string(seed_path)

        # ── Extract seed text sections ────────────────────────────
        brief        = seed_texts.get('brief.txt', 'N/A')
        brand        = seed_texts.get('brand.txt', 'N/A')
        audience     = seed_texts.get('audience.txt', 'N/A')
        functionality = seed_texts.get('functionality.txt', '')

        # ── Build functionality requirements block ────────────────
        # This is the critical injection — functionality.txt becomes
        # a HARD REQUIREMENT block, not optional context.
        if functionality:
            functionality_block = f"""
<functionality_requirements>
CRITICAL: The following capability specification defines what this site MUST DO.
Every capability listed here is mandatory. The pipeline will be tested against
each one. Missing functionality = failed verification.

{functionality}

Implementation rules:
1. Every capability listed must be implemented with real working code.
2. Forms must validate client-side AND call the specified API route.
3. State must use the specified management pattern (useState/useReducer).
4. All data must live in lib/ files with TypeScript interfaces in types/.
5. Components must receive state as props — no internal state for shared data.
6. localStorage persistence must be implemented where specified.
7. The required_file_structure section defines the EXACT files you must produce.
   You MUST generate every file listed there.
</functionality_requirements>
"""
        else:
            functionality_block = """
<functionality_requirements>
WARNING: No functionality.txt found in seed texts.
Implement sensible interactive features based on the brief:
- Any forms must validate and submit to an API route
- Navigation must have mobile toggle and smooth scroll
- Any products or services must be stored in lib/ with TypeScript interfaces
</functionality_requirements>
"""

        # ── Build optional template reference block (Phase 2) ─────
        template_block = ""
        if template_content:
            template_block = f"""
<template_references>
The following curated UI templates have been selected for this project.
Use them as visual reference only. Adapt layout and style to the brand.
Never copy component names, copy text, or color values from templates.
{json.dumps(template_content, indent=2)}
</template_references>
"""

        master_prompt = f"""
<task>
You are the AutoForge Architect. Generate a complete, production-ready,
FULLY FUNCTIONAL website codebase from the project seed texts below.
Your output runs through a pipeline: INSTALL → BUILD → TEST → DEPLOY.
</task>

<bootstrap_reference>
The following bootstrap is a TEACHING EXAMPLE ONLY.
It shows you HOW to structure a Next.js project with proper TypeScript,
React hooks, component separation, API routes, and state management.

CRITICAL RULES FOR USING THE BOOTSTRAP:
1. NEVER copy any text, names, colors, or copy from the bootstrap example.
   The bootstrap is about "Volt Coffee". Your project is NOT about coffee.
2. NEVER use Bebas Neue font, #CCFF00 color, or any Volt Coffee branding.
3. NEVER copy component structure — redesign components for this brand.
4. USE the bootstrap to understand: file structure, hook patterns, API routes,
   TypeScript interface patterns, useReducer for cart, form submission patterns.
5. BUILD something completely different in every way: industry, tone,
   visual language, component names, copy, data structures.

Bootstrap seed (what the example project is about):
{bootstrap_brief}

Bootstrap source code (HOW a project should be structured):
{bootstrap_code}
</bootstrap_reference>

{functionality_block}

{template_block}

<new_project_seed>
Brief (what to build):
{brief}

Brand (visual identity — use THESE colors, fonts, and style):
{brand}

Audience (who this is for):
{audience}
</new_project_seed>

<autoforge_recipe_requirement>
You MUST generate a root-level file named 'autoforge.json'.
Without it the pipeline cannot execute. Schema:
{json.dumps(self.RECIPE_SCHEMA, indent=2)}
CRITICAL: deploy_command MUST start with 'npx'. Example: "npx vercel --prod --yes"
</autoforge_recipe_requirement>

<typescript_rules>
RULE 1 — CAMELCASE KEYS: Never use hyphenated keys in JS/TS objects.
  CORRECT: heroContent, statsBar, programCard
  WRONG: hero-content, stats-bar, program-card

RULE 2 — FULL FILES: Every <file> block must contain the COMPLETE file.
  Never truncate. Never write "// ... rest of file".

RULE 3 — CSS VARIABLES: Define ALL colors in :root in globals.css.
  Use the exact hex values from the brand seed text. Never approximate.

RULE 4 — NO body height:100vh: Never set height:100vh on body or html.
  This collapses multi-section pages. Use min-height on sections instead.

RULE 5 — REAL TAILWIND OR PURE CSS: Do not invent Tailwind class names
  that reference CSS variables (e.g. bg-primary-accent is NOT a real class).
  Either use standard Tailwind utilities OR use inline styles with CSS variables.
  Never mix invented class names with real ones.

RULE 6 — NO CONSOLE.LOG in production files.

RULE 7 — ONE DEFAULT EXPORT per component file.
</typescript_rules>

<output_format>
Output ONLY <file path="path/to/file">COMPLETE FILE CONTENT</file> blocks.
No preamble. No commentary. No partial files. No explanations.
Generate every file listed in the functionality requirements file structure.
</output_format>
"""
        raw = self._call_llm(master_prompt, max_tokens=8000)
        if not raw:
            print("  [WeaverAI] Generation failed — no LLM response.")
            return None

        generated_files = self._parse_blocks(raw)
        print(f"  [WeaverAI] {len(generated_files)} files generated.")

        # ── autoforge.json recovery ───────────────────────────────
        if "autoforge.json" not in generated_files:
            print("  [WeaverAI] WARNING: autoforge.json missing. Triggering recovery...")
            generated_files = self._recover_recipe(generated_files, seed_texts)
            if generated_files is None:
                return None

        # ── deploy_command enforcement ────────────────────────────
        generated_files = self._enforce_deploy_command(generated_files)

        return generated_files

    def _recover_recipe(self, generated_files, seed_texts):
        """Stage 2: Generate autoforge.json if Stage 1 omitted it."""
        file_list = "\n".join(generated_files.keys())
        recovery_prompt = f"""
<task>
You generated a codebase but omitted the critical 'autoforge.json' file.
Generate it now based on the files you produced.
</task>

<generated_files>
{file_list}
</generated_files>

<project_brief>
{seed_texts.get('brief.txt', 'N/A')}
</project_brief>

<required_schema>
{json.dumps(self.RECIPE_SCHEMA, indent=2)}
</required_schema>

<rules>
- deploy_command MUST start with 'npx'
- test_command and build_command must match the framework detected from the files
- Output ONLY: <file path="autoforge.json">{{...}}</file>
</rules>
"""
        raw = self._call_llm(recovery_prompt, temperature=0.1)
        if not raw:
            print("  [WeaverAI] Recovery failed — no LLM response.")
            return None

        recovered = self._parse_blocks(raw)
        if "autoforge.json" in recovered:
            print("  [WeaverAI] autoforge.json recovered.")
            generated_files["autoforge.json"] = recovered["autoforge.json"]
            return generated_files

        print("  [WeaverAI] Double failure — autoforge.json recovery failed.")
        return None

    def _enforce_deploy_command(self, generated_files):
        """Silently fix deploy_command if it's missing the npx prefix."""
        if "autoforge.json" not in generated_files:
            return generated_files
        try:
            recipe = json.loads(generated_files["autoforge.json"])
            deploy = recipe.get("deploy_command", "")
            if deploy and not deploy.strip().startswith("npx"):
                recipe["deploy_command"] = "npx " + deploy.strip()
                generated_files["autoforge.json"] = json.dumps(recipe, indent=2)
                print("  [WeaverAI] Fixed deploy_command: added npx prefix.")
        except json.JSONDecodeError:
            pass
        return generated_files

    def _parse_blocks(self, text):
        """Extracts <file path="...">content</file> blocks from LLM output."""
        files = {}
        blocks = re.findall(r'<file path="(.*?)">(.*?)</file>', text, re.DOTALL)
        for path, code in blocks:
            files[path.strip()] = code.strip()
        return files