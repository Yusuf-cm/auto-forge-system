# vmr_tools/story_weaver.py
# AutoForge: StoryWeaverAI — Build log analyst and Saga producer
import json
from vmr_tools.base_ai import BaseAI


class StoryWeaverAI(BaseAI):
    """
    The Historian. Reads raw pipeline execution logs and produces
    structured Sagas — the diagnostic reports that drive all Director decisions.

    A Saga contains:
      - status:        'success' or 'failure'
      - failed_step:   'install' | 'build' | 'test' | 'deploy' | 'none'
      - error_summary: concise description of the specific error
      - root_cause:    technical hypothesis on why the error occurred
      - suggested_fix: high-level instruction on how to correct the code
    """

    def create_saga(self, log_text):
        """
        Analyses a pipeline log and returns a structured Saga dict.
        Returns None if analysis or parsing fails.
        """
        print("  [StoryWeaver] Analyzing build log for root cause...")

        prompt = f"""
<task>
You are the AutoForge StoryWeaver. Analyse the pipeline execution log below.
Identify precisely where the pipeline failed and why.
Produce a single valid JSON Saga object.
</task>

<log_input>
{log_text}
</log_input>

<required_json_schema>
{{
  "status": "string — 'success' or 'failure'",
  "failed_step": "string — 'install', 'build', 'test', 'deploy', or 'none'",
  "error_summary": "string — concise description of the specific error from stderr",
  "root_cause": "string — your technical hypothesis on why this error occurred",
  "suggested_fix": "string — specific instruction on how to correct the code"
}}
</required_json_schema>

<constraints>
1. Use technical, precise language.
2. CRITICAL: If the log does not contain a success marker the status MUST be 'failure'.
3. If the log is empty or lacks error output, set status='failure' and root_cause='Silent crash or empty log'.
4. For build errors caused by TypeScript syntax like hyphenated object keys 
   (e.g. hero-content: {{...}}), root_cause MUST state: 
   "Hyphenated TypeScript object keys — use camelCase (heroContent not hero-content)"
5. For errors caused by 'vercel: command not found', root_cause MUST state:
   "deploy_command missing npx prefix — change to npx vercel --prod --yes"
6. Output JSON only. No preamble. No commentary.
</constraints>
"""
        raw = self._call_llm(prompt, temperature=0.1)
        if not raw:
            print("  [StoryWeaver] Analysis failed — no LLM response.")
            return None

        saga = self._parse_json_safe(raw)
        if not saga:
            print("  [StoryWeaver] JSON parsing failed.")
            return None

        required_keys = ["status", "failed_step", "error_summary", "root_cause", "suggested_fix"]
        for key in required_keys:
            if key not in saga:
                print(f"  [StoryWeaver] Saga missing key: '{key}'")
                return None

        print(f"  [StoryWeaver] Saga complete. Status: {saga['status']} | Failed step: {saga['failed_step']}")
        return saga
