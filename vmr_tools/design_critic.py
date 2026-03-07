# vmr_tools/design_critic.py
# AutoForge: DesignCriticAI — Brand-driven visual analysis with memory
import json
from vmr_tools.base_ai import BaseAI


class DesignCriticAI(BaseAI):
    """
    The Brand Enforcer. Scores the visual design of a passing website
    against its brand brief on a 1-10 scale.

    Scoring is brand-alignment-first:
      1-4:  Brand colors/fonts completely absent — generic site
      5-6:  Some brand elements present but inconsistent
      7-8:  Brand clearly visible, needs polish
      9-10: Strong brand identity, professional execution

    Accepts previous_critique for memory across cycles — escalates
    score downward if previous weaknesses were not resolved.

    Produces specific, code-level improvement instructions with exact
    hex codes, font names, CSS values, and files to modify.
    """

    def critique(self, codebase, seed_texts, previous_critique=None, metrics_trend=None):
        """
        Analyses the codebase against the brand brief.

        Args:
            codebase:          string of all source files (XML-tagged)
            seed_texts:        dict of {filename: content}
            previous_critique: dict from last_critique.json or None
            metrics_trend:     dict from MetricsCollector.get_trend() or None (Phase 3)

        Returns:
            dict with design_score, weaknesses, improvements, files_to_modify
            or None on failure
        """
        print("  [DesignCritic] Analysing design against brand brief...")

        brand   = seed_texts.get('brand.txt', '')
        brief   = seed_texts.get('brief.txt', '')
        audience = seed_texts.get('audience.txt', '')

        # ── Build memory context block ────────────────────────────────────
        memory_block = ""
        if previous_critique:
            prev_score = previous_critique.get('design_score', 'unknown')
            prev_weaknesses = previous_critique.get('weaknesses', [])
            memory_block = f"""
<previous_critique_memory>
IMPORTANT: The previous evolution cycle scored {prev_score}/10 with these weaknesses:
{json.dumps(prev_weaknesses, indent=2)}

You MUST check whether those weaknesses have been resolved in the current codebase.
If they have NOT been resolved, score lower than {prev_score}/10 to force escalation.
If they HAVE been resolved, acknowledge that and focus on new weaknesses.
Do not repeat the same soft suggestions that were already tried and failed.
</previous_critique_memory>
"""

        # ── Build metrics context block (Phase 3) ─────────────────────────
        metrics_block = ""
        if metrics_trend:
            metrics_block = f"""
<metrics_context>
Objective performance data from the last pipeline run:
{json.dumps(metrics_trend, indent=2)}

When identifying improvements, weight issues that address metric weaknesses:
- If Lighthouse performance < 75: prioritise removing unused components, reducing bundle size
- If Lighthouse SEO < 80: prioritise meta tags, semantic HTML, heading hierarchy
- If bundle JS is increasing across versions: flag unnecessary dependencies
</metrics_context>
"""

        prompt = f"""
<task>
You are the AutoForge Design Critic. Analyse the website codebase against
the brand brief. Score it 1-10 based on brand alignment. Produce specific,
code-level improvement instructions.
</task>

<brand_brief>
Brand:    {brand}
Brief:    {brief}
Audience: {audience}
</brand_brief>

<current_codebase>
{codebase}
</current_codebase>

{memory_block}
{metrics_block}

<scoring_guide>
Score based on brand alignment, not generic design quality:

1-4:  Brand colors and fonts are completely absent. The site looks generic.
      Background is white or default. No brand personality visible.

5-6:  Some brand elements present but inconsistently applied.
      Brand colors appear in some places but not others.
      Font may be correct in headings but not body.

7-8:  Brand is clearly visible. Colors, fonts, and personality are consistent.
      Minor polish issues remain — spacing, sizing, mobile responsiveness.

9-10: Strong brand identity. Every element reflects the brief.
      Professional execution. No generic placeholders remain.
</scoring_guide>

<brand_checklist>
Check each item. Mark PASS or FAIL with specific evidence from the code:

1. COLORS: Are the exact hex codes from the brand brief literally present in CSS?
   FAIL example: "background-color: white" when brand requires #1A1A1A
   PASS example: "--color-bg: #1A1A1A; background-color: var(--color-bg)"

2. TYPOGRAPHY: Is the exact font name from the brand brief imported and applied?
   FAIL example: "font-family: Arial" when brand requires Bebas Neue
   PASS example: "@import url('...Bebas+Neue...'); font-family: 'Bebas Neue'"

3. BACKGROUND: Does the page background match the brand palette?
   FAIL example: white background for a dark industrial brand
   PASS example: body {{ background-color: #1A1A1A }}

4. HERO: Is the hero section visually strong and brand-aligned?

5. CTA BUTTONS: Are buttons styled with brand colors?
   FAIL example: default blue button
   PASS example: background: #CCFF00; color: #1A1A1A; border-radius: 0

6. CONTENT: Has placeholder text been replaced with brand-specific copy?

7. RESPONSIVE: Are there media queries or responsive Tailwind classes?

8. PERSONALITY: Does the overall visual feel match the brand description?
</brand_checklist>

<instruction>
1. Score the design 1-10 using the scoring guide and brand checklist.
2. Identify the 3-5 most important weaknesses.
3. For each weakness, provide a SPECIFIC code-level fix — not vague suggestions.

BAD improvement: "Use brand colors consistently"
GOOD improvement: "In globals.css, add to :root: --color-bg: #1A1A1A; --color-accent: #CCFF00.
Set body {{ background-color: var(--color-bg); color: #FFFFFF }}.
Set all h1, h2 {{ color: var(--color-accent) }}"

BAD improvement: "Improve typography"
GOOD improvement: "In globals.css line 1, add:
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap');
In :root add: --font-heading: 'Bebas Neue', sans-serif; --font-body: 'Inter', sans-serif;
Set h1, h2, h3 {{ font-family: var(--font-heading); font-size: 5rem; letter-spacing: -0.02em }}"

4. List the specific files to modify (usually app/globals.css and app/page.tsx).
</instruction>

<output_format>
Output a single valid JSON object only:
{{
  "design_score": number (1-10),
  "checklist": {{
    "colors": "PASS or FAIL — evidence",
    "typography": "PASS or FAIL — evidence",
    "background": "PASS or FAIL — evidence",
    "hero": "PASS or FAIL — evidence",
    "cta_buttons": "PASS or FAIL — evidence",
    "content": "PASS or FAIL — evidence",
    "responsive": "PASS or FAIL — evidence",
    "personality": "PASS or FAIL — evidence"
  }},
  "weaknesses": ["string", "string", "string"],
  "improvements": [
    "Specific code-level fix with exact values",
    "Specific code-level fix with exact values"
  ],
  "files_to_modify": ["app/globals.css", "app/page.tsx"]
}}
</output_format>
"""
        raw = self._call_llm(prompt, temperature=0.2)
        if not raw:
            print("  [DesignCritic] No LLM response.")
            return None

        critique = self._parse_json_safe(raw)
        if not critique:
            print("  [DesignCritic] JSON parsing failed.")
            return None

        score = critique.get('design_score', 0)
        weaknesses = critique.get('weaknesses', [])
        print(f"  [DesignCritic] Design score: {score}/10")
        print(f"  [DesignCritic] Weaknesses found: {len(weaknesses)}")
        for w in weaknesses:
            print(f"    - {w}")

        return critique
