# vmr_tools/base_ai.py
# AutoForge: BaseAI — Multi-provider LLM communication layer
import os
import json
from dotenv import load_dotenv
from groq import Groq


class BaseAI:
    """
    The foundational layer for all AutoForge AI agents.
    Provides:
      - _call_llm()                  Multi-provider fallback (Groq → Gemini → OpenRouter)
      - _read_directory_to_string()  Token-safe codebase ingestion
      - _parse_json_safe()           Robust JSON extraction from LLM output

    Provider priority:
      1. Groq llama-3.3-70b-versatile                      — fastest, best quality
      2. Groq llama3-70b-8192                              — older but still capable
      3. Groq gemma2-9b-it                                 — last Groq resort
      4. Gemini gemini-2.0-flash                           — cross-provider fallback, free, large context
      5. Gemini gemini-2.0-flash-lite                      — lightweight Gemini fallback
      6. OpenRouter openrouter/auto                        — meta-router, picks best available free model
      7. OpenRouter deepseek/deepseek-chat-v3-0324:free   — confirmed free, DeepSeek V3
      8. OpenRouter deepseek/deepseek-r1:free             — confirmed free, DeepSeek R1

    NOTE: llama-3.1-8b-instant removed — too small for AutoForge prompts (413 errors).
    NOTE: gemini-1.5-flash / gemini-1.5-pro removed — deprecated, return 404.
    NOTE: OpenRouter requires OPENROUTER_API_KEY in .env — free tier, no billing needed.
          Sign up at https://openrouter.ai and generate a free key.
    """

    def __init__(self):
        load_dotenv()

        # ── Groq setup ────────────────────────────────────────────────────
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("FATAL: GROQ_API_KEY not found in .env file.")
        self.groq_client = Groq(api_key=groq_key)

        # ── Gemini setup (optional but strongly recommended) ──────────────
        self.gemini_client = None
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self.gemini_client = genai
            except ImportError:
                print("  [BaseAI] Gemini: INACTIVE (run: pip install google-generativeai)")

        # ── OpenRouter setup (optional, free tier available) ─────────────
        self.openrouter_client = None
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                from openai import OpenAI
                self.openrouter_client = OpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                )
            except ImportError:
                print("  [BaseAI] OpenRouter: INACTIVE (run: pip install openai)")

        # Groq models in priority order
        self.GROQ_MODELS = [
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "gemma2-9b-it",
        ]

        # Gemini models in priority order
        self.GEMINI_MODELS = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ]

        # OpenRouter free models in priority order.
        # openrouter/free is a meta-router that auto-selects from all available
        # free models — most resilient option, never 404s due to individual model removal.
        self.OPENROUTER_MODELS = [
            "openrouter/auto",
            "deepseek/deepseek-chat-v3-0324:free",
            "deepseek/deepseek-r1:free",
        ]

    def _call_llm(self, prompt, temperature=0.2, max_tokens=8000):
        """
        Sends a prompt to the LLM with automatic multi-model, multi-provider fallback.

        Order:
          1. Try each Groq model in order
          2. If all Groq models fail → fall through to Gemini
          3. If all Gemini models fail → fall through to OpenRouter
          4. If everything fails → return None and log clearly

        Returns the response string or None if everything fails.
        """
        # ── Try Groq first ────────────────────────────────────────────────
        for model in self.GROQ_MODELS:
            try:
                response = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                err = str(e)[:120]
                if "decommissioned" in err.lower():
                    continue
                if "429" in err or "rate limit" in err.lower():
                    print(f"  [BaseAI] Groq '{model}' rate limited. Trying next...")
                    continue
                print(f"  [BaseAI] Groq '{model}' failed: {err}. Trying next...")
                continue

        # ── Groq exhausted — try Gemini ───────────────────────────────────
        if self.gemini_client:
            print("  [BaseAI] All Groq models exhausted. Falling back to Gemini...")
            for model_name in self.GEMINI_MODELS:
                try:
                    model = self.gemini_client.GenerativeModel(
                        model_name=model_name,
                        generation_config={
                            "temperature": temperature,
                            "max_output_tokens": max_tokens,
                        }
                    )
                    response = model.generate_content(prompt)
                    print(f"  [BaseAI] Gemini '{model_name}' responded successfully.")
                    return response.text
                except Exception as e:
                    print(f"  [BaseAI] Gemini '{model_name}' failed: {str(e)[:120]}. Trying next...")
                    continue

        # ── Gemini exhausted — try OpenRouter ─────────────────────────────
        if self.openrouter_client:
            print("  [BaseAI] All Gemini models exhausted. Falling back to OpenRouter...")
            for model_name in self.OPENROUTER_MODELS:
                try:
                    response = self.openrouter_client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    print(f"  [BaseAI] OpenRouter '{model_name}' responded successfully.")
                    return response.choices[0].message.content
                except Exception as e:
                    print(f"  [BaseAI] OpenRouter '{model_name}' failed: {str(e)[:120]}. Trying next...")
                    continue

        print("  [BaseAI] FATAL: All providers and models exhausted. No response.")
        return None

    def _read_directory_to_string(self, dir_path):
        """
        Reads all text-based source files in a directory into XML-tagged blocks
        for LLM context. Skips binary files, dependency folders, lock files,
        and files over 10KB to stay within token limits.
        """
        if not os.path.exists(dir_path):
            return ""

        ALLOWED_EXTENSIONS = {
            '.js', '.jsx', '.ts', '.tsx', '.css', '.html',
            '.json', '.md', '.txt', '.env.example', '.gitignore'
        }
        IGNORED_DIRS = {
            'node_modules', '.next', '.git', 'dist',
            'build', '.vercel', '__pycache__', '.turbo'
        }
        IGNORED_FILES = {
            'package-lock.json', 'yarn.lock',
            'pnpm-lock.yaml', 'next-env.d.ts'
        }

        content = ""
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for filename in sorted(files):
                if filename in IGNORED_FILES:
                    continue
                _, ext = os.path.splitext(filename)
                if ext not in ALLOWED_EXTENSIONS:
                    continue
                filepath = os.path.join(root, filename)
                if os.path.getsize(filepath) > 10240:
                    continue
                relative_path = os.path.relpath(filepath, dir_path)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content += f'<file path="{relative_path}">\n{f.read()}\n</file>\n\n'
                except Exception:
                    continue
        return content

    def _parse_json_safe(self, raw_text):
        """
        Robustly extracts a JSON object from LLM output that may contain
        preamble, postamble, markdown fences, or escape characters.

        Three fallback strategies:
          1. Direct parse
          2. Slice from first { to last }
          3. Clean common escape mistakes then retry
        """
        if not raw_text:
            return None

        # Strategy 1: strip markdown fences then direct parse
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: slice from first { to last }
        start = raw_text.find('{')
        end   = raw_text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw_text[start:end + 1])
            except json.JSONDecodeError:
                pass

        # Strategy 3: fix common LLM escape mistakes then retry
        try:
            candidate = raw_text[start:end + 1] if start != -1 else raw_text
            candidate = candidate.replace("\\'", "'")
            candidate = candidate.replace('\\"', '"')
            return json.loads(candidate)
        except Exception:
            pass

        return None