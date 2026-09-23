# main.py
# AutoForge: Universal Autonomous Website Orchestrator
import sys
import os
import subprocess
import shutil
import json
import shlex
import time
import glob

from vmr.storage import read_seed
from vmr_tools.story_weaver import StoryWeaverAI
from vmr_tools.director_ai import DirectorAI
from vmr_tools.design_critic import DesignCriticAI
from vmr_tools.code_enforcer import CodeEnforcer


class AutoForgeRecipeError(Exception):
    """Raised for pipeline failures, malformed recipes, or command timeouts."""
    pass


class AutoForgeVMR:
    """
    The AutoForge Virtual Machine Runner.
    Orchestrates all agents and pipeline operations.

    Commands:
      weave[project] --using_template [template]  — Generate v1 from seed texts
      evolve [project]                               — Improve to vNext
      run    [project] --version [vN]                — Execute a specific version
      help                                           — Show usage
    """

    def __init__(self):
        self.commands = {
            "weave":  self._command_weave,
            "evolve": self._command_evolve,
            "run":    self._command_run,
            "help":   self._command_help,
        }

    def execute_command(self, args):
        if not args:
            self._command_help()
            return
        command = args[0].lower()
        if command not in self.commands:
            print(f"AutoForge Error: Unknown command '{command}'.")
            self._command_help()
            return
        self.commands[command](args[1:])

    def _command_help(self, args=None):
        print("\n" + "=" * 50)
        print("  AutoForge Universal Code Orchestrator")
        print("=" * 50)
        print("  weave  [name] --using_template [tpl]  Generate v1")
        print("  evolve [name]                          Improve to vNext")
        print("  run    [name] --version [vN]           Run specific version")
        print("=" * 50)

    # ══════════════════════════════════════════════════════════════════════
    # WEAVE — Generate v1
    # ══════════════════════════════════════════════════════════════════════

    def _command_weave(self, args):
        """
        Generates a website candidate from seed texts and runs an autonomous
        repair loop. v1 is promoted only after verification succeeds.
        """
        if len(args) < 3 or "--using_template" not in args:
            print("Usage: python main.py weave [name] --using_template [template]")
            return

        project_name  = args[0]
        template_name = args[args.index("--using_template") + 1]
        project_path  = os.path.join("projects", project_name)
        bootstrap_path = template_name

        print(f"\n{'=' * 50}")
        print(f"  AutoForge WEAVE: '{project_name}'")
        print(f"{'=' * 50}\n")

        os.makedirs(os.path.join(project_path, "seed_texts"), exist_ok=True)
        seed_texts = read_seed(project_name)
        build_log_dir = self._get_build_log_dir(project_path)
        docs_log_dir  = self._get_docs_log_dir(project_path)

        # ── Stage 1: Generate codebase ────────────────────────────────────
        try:
            from vmr_tools.weaver_ai import WeaverAI
            weaver = WeaverAI()
        except Exception as e:
            print(f"  FATAL: WeaverAI init failed: {e}")
            return

        print("  Generating codebase from seed texts...")
        generated_files = weaver.create_universe(seed_texts, bootstrap_path)
        if not generated_files:
            print("  FATAL: WeaverAI returned no files.")
            return

        # ── Stage 2: Write to staging ─────────────────────────────────────
        staging_dir = os.path.join(project_path, "versions", "staging")
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        os.makedirs(staging_dir)

        for filepath, code in generated_files.items():
            full_path = os.path.join(staging_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)

        print(f"  {len(generated_files)} files written to staging.")

        # ── Stage 2b: CodeEnforcer — deterministic pre-build pass ─────────
        pending_violation_brief = ""
        initial_enforcement = CodeEnforcer().enforce(staging_dir)
        if initial_enforcement.has_violations:
            pending_violation_brief = initial_enforcement.violation_brief()

        # ── Stage 3: Verify staging — autonomous fix loop ─────────────────
        max_attempts = 5
        success = False
        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                print(f"\n  Fix attempt {attempt}/{max_attempts}...")

            log_path = self._execute_pipeline(
                project_name, staging_dir, "staging",
                build_log_dir, skip_deploy=True
            )
            pipeline_success = self._pipeline_passed(log_path)

            # --- THE ARCHITECTURAL FIX ---
            # It is only a TRUE success if the pipeline passes AND there are no enforcer violations
            if pipeline_success and not pending_violation_brief:
                success = True
                break

            if attempt == max_attempts:
                print(f"\n  Max attempts reached. Pipeline still failing or violations remain.")
                break

            # If the pipeline failed natively, get the StoryWeaver Saga
            if not pipeline_success:
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    log_text = "".join(log_lines[-150:])

                saga = StoryWeaverAI().create_saga(log_text)
                if not saga:
                    print(f"\n  [AutoForge] StoryWeaver failed to analyze log. Halting fix loop.")
                    break
            else:
                # The pipeline passed, BUT CodeEnforcer found a violation (like missing onClick).
                # Create a synthetic Saga to force the Director into Fix Mode.
                print("\n  [AutoForge] Pipeline passed, but CodeEnforcer violations remain. Forcing Fix Mode.")
                saga = {
                    "status": "failure",
                    "failed_step": "code_enforcer",
                    "error_summary": "CodeEnforcer detected functional violations.",
                    "root_cause": "Deterministic rules (e.g., missing onClick handlers) were violated.",
                    "suggested_fix": "Fix the exact files and lines listed in the enforcement violations."
                }

            # Director fixes build errors + any pending enforcer violations
            director = DirectorAI()
            modifications = director.run_evolution_cycle(
                project_name, staging_dir, saga,
                violation_brief=pending_violation_brief
            )
            pending_violation_brief = ""  # Reset
            
            if not modifications:
                print("\n  [AutoForge] FATAL: Director returned no modifications.")
                print("  (This usually happens when the LLM rate limits or fails to output <file> tags).")
                print("  Halting fix loop early.")
                break

            for rel_path, code in modifications.items():
                full_path = os.path.join(staging_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(code)

            # Re-run enforcer after Director pass — carry new violations forward
            enforcement = CodeEnforcer().enforce(staging_dir)
            if enforcement.has_violations:
                pending_violation_brief = enforcement.violation_brief()

            # API THROTTLE: Pause for 15 seconds to let free-tier API rate limits reset
            if attempt < max_attempts and not success:
                print("  [AutoForge] Throttling for 15 seconds to respect API rate limits...")
                time.sleep(15)

        # ── Stage 4: Promote staging → v1 ────────────────────────────────
        if not success:
            print(f"\n[AutoForge] v1 was NOT promoted because verification did not pass.")
            print("  The generated candidate remains in versions/staging for inspection.")
            return

        v1_dir = os.path.join(project_path, "versions", "v1")
        if os.path.exists(v1_dir):
            shutil.rmtree(v1_dir)

        ignore_func = shutil.ignore_patterns(
            'node_modules', '.next', 'dist', 'build', '.vercel', 'package-lock.json'
        )
        shutil.copytree(staging_dir, v1_dir, ignore=ignore_func)
        print(f"\n  v1 created at: {v1_dir}")

        self._write_doc_log(
            docs_log_dir, "v1", "GENESIS",
            f"v1 generated from seed texts using template '{template_name}'.",
            f"Files: {list(generated_files.keys())}"
        )

    # ══════════════════════════════════════════════════════════════════════
    # EVOLVE — Improve to vNext
    # ══════════════════════════════════════════════════════════════════════

    def _command_evolve(self, args):
        """
        Takes the latest stable version and produces an improved vNext.
        """
        if not args:
            print("Usage: python main.py evolve [project_name]")
            return

        project_name = args[0]
        project_path = os.path.join("projects", project_name)

        print(f"\n{'=' * 50}")
        print(f"  AutoForge EVOLVE: '{project_name}'")
        print(f"{'=' * 50}\n")

        latest_v = self._get_latest_version(project_path)
        if not latest_v:
            print(f"  No versions found. Run 'weave {project_name}' first.")
            return

        print(f"  Latest version: {latest_v}")

        build_log_dir = self._get_build_log_dir(project_path)
        docs_log_dir  = self._get_docs_log_dir(project_path)
        source_dir    = os.path.join(project_path, "versions", latest_v)

        # ── Get or create build log for latest version ────────────────────
        log_path = self._get_latest_log_for_version(build_log_dir, latest_v)

        if not log_path:
            print(f"  No build log found for {latest_v}. Running pipeline first...")
            log_path = self._execute_pipeline(
                project_name, source_dir, latest_v,
                build_log_dir, skip_deploy=True
            )

        with open(log_path, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
            log_text = "".join(log_lines[-150:])

        # ── StoryWeaver analyses the log ──────────────────────────────────
        saga = StoryWeaverAI().create_saga(log_text)
        if not saga:
            print("  StoryWeaver failed. Cannot proceed.")
            return

        status = saga.get('status', 'failure')

        # --- PRE-FLIGHT ENFORCER CHECK ---
        # Run CodeEnforcer on the latest stable version to catch if it has functional violations
        print("[AutoForge] Running CodeEnforcer pre-flight check...")
        enforcement = CodeEnforcer().enforce(source_dir)
        pending_violation_brief = ""
        
        if enforcement.has_violations:
            print("  [AutoForge] CodeEnforcer found violations in the stable version. Forcing FIX MODE.")
            status = 'failure'
            saga = {
                "status": "failure",
                "failed_step": "code_enforcer",
                "error_summary": "CodeEnforcer detected functional violations.",
                "root_cause": "Deterministic rules (e.g., missing onClick handlers) were violated.",
                "suggested_fix": "Fix the exact files and lines listed in the enforcement violations."
            }
            pending_violation_brief = enforcement.violation_brief()

        # ── Compute vNext version ─────────────────────────────────────────
        next_n = int(latest_v[1:]) + 1
        next_v = f"v{next_n}"

        # ═══════════════════════════════════════════════════════
        # FIX MODE
        # ═══════════════════════════════════════════════════════
        if status == 'failure':
            failed_step = saga.get('failed_step', 'unknown')
            print(f"  Failure detected at step: {failed_step}")
            print(f"  Root cause: {saga.get('root_cause', 'unknown')}")
            print()

            director = DirectorAI()
            modifications = director.run_evolution_cycle(
                project_name, source_dir, saga, 
                violation_brief=pending_violation_brief
            )

            if not modifications:
                print("  Director returned no modifications.")
                return

            print(f"  Director produced {len(modifications)} modification(s).")
            next_dir = self._branch_version(project_path, latest_v, next_v)

            for rel_path, code in modifications.items():
                full_path = os.path.join(next_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                print(f"  Applied: {rel_path}")

            CodeEnforcer().enforce(next_dir)

            print(f"\n  Running verification pipeline on {next_v}...")
            log_path = self._execute_pipeline(
                project_name, next_dir, next_v,
                build_log_dir, skip_deploy=True
            )
            passed = self._pipeline_passed(log_path)

            if passed:
                print(f"  {next_v} passed verification.")
                self._write_doc_log(
                    docs_log_dir, next_v, "FIX",
                    f"Fixed '{failed_step}' failure from {latest_v}.",
                    f"Root cause: {saga.get('root_cause')}\nFiles modified: {list(modifications.keys())}"
                )
            else:
                print(f"  Verification failed for {next_v}. Run 'evolve' again to continue.")
                self._write_doc_log(
                    docs_log_dir, next_v, "FIX_FAILED",
                    f"Fix attempt for '{failed_step}' did not pass verification.",
                    f"Files modified: {list(modifications.keys())}"
                )
            return

        # ═══════════════════════════════════════════════════════
        # IMPROVE MODE
        # ═══════════════════════════════════════════════════════
        print(f"  {latest_v} is stable. Engaging Design Critic for improvement analysis...")

        seed_texts = read_seed(project_name)
        codebase   = self._read_codebase(source_dir)

        previous_critique = self._load_last_critique(docs_log_dir)
        if previous_critique:
            prev_score = previous_critique.get('design_score', '?')
            print(f"  Previous critique loaded (score: {prev_score}/10)")

        critic   = DesignCriticAI()
        critique = critic.critique(codebase, seed_texts, previous_critique)

        if not critique:
            print("  Design Critic failed. Cannot proceed.")
            return

        self._save_critique(docs_log_dir, latest_v, critique)

        score = critique.get('design_score', 0)
        if score >= 9:
            print(f"  Design score {score}/10 — design is excellent. No improvements needed.")
            return

        print()
        director      = DirectorAI()
        modifications = director.run_improvement_cycle(project_name, source_dir, critique, seed_texts)

        if not modifications:
            print("  Director returned no modifications.")
            return

        print(f"  Director produced {len(modifications)} modification(s).")
        next_dir = self._branch_version(project_path, latest_v, next_v)

        for rel_path, code in modifications.items():
            full_path = os.path.join(next_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"  Applied: {rel_path}")

        CodeEnforcer().enforce(next_dir)

        print(f"\n  Running verification pipeline on {next_v}...")
        log_path = self._execute_pipeline(
            project_name, next_dir, next_v,
            build_log_dir, skip_deploy=True
        )
        passed = self._pipeline_passed(log_path)

        if passed:
            print(f"  {next_v} passed verification.")
            self._write_doc_log(
                docs_log_dir, next_v, "IMPROVE",
                f"Design improved from {latest_v}. Score was {score}/10.",
                f"Weaknesses addressed: {critique.get('weaknesses',[])}\nFiles: {list(modifications.keys())}"
            )
        else:
            print(f"  Verification failed for {next_v}. Run 'evolve' again to continue.")
            self._write_doc_log(
                docs_log_dir, next_v, "IMPROVE_FAILED",
                f"Design improvement from {latest_v} did not pass verification.",
                f"Files: {list(modifications.keys())}"
            )

    # ══════════════════════════════════════════════════════════════════════
    # RUN — Execute specific version
    # ══════════════════════════════════════════════════════════════════════

    def _command_run(self, args):
        if len(args) < 3 or "--version" not in args:
            print("Usage: python main.py run [name] --version [vN]")
            return

        project_name = args[0]
        version      = args[args.index("--version") + 1]
        source_dir   = os.path.join("projects", project_name, "versions", version)
        build_log_dir = self._get_build_log_dir(os.path.join("projects", project_name))

        print(f"\n  Running pipeline for {project_name} {version}...")
        try:
            log_path = self._execute_pipeline(
                project_name, source_dir, version,
                build_log_dir, skip_deploy=False
            )
            print(f"  Pipeline complete. Log: {log_path}")
        except Exception as e:
            print(f"  Pipeline failed: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # PIPELINE EXECUTION
    # ══════════════════════════════════════════════════════════════════════

    def _execute_pipeline(self, project_name, source_dir, version_tag,
                          build_log_dir, skip_deploy=False):
        """
        Runs the full pipeline defined in autoforge.json.
        Writes a timestamped log file to build_log_dir.
        Returns the log file path.
        """
        recipe_path = os.path.join(source_dir, "autoforge.json")
        if not os.path.exists(recipe_path):
            raise AutoForgeRecipeError(f"autoforge.json missing in {source_dir}")

        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe = json.load(f)

        timeout = recipe.get("timeout_seconds", 300)
        timestamp = int(time.time())
        log_path = os.path.join(build_log_dir, f"run_{version_tag}_{timestamp}.log")

        steps = ["install_command", "build_command", "test_command"]
        if not skip_deploy:
            steps.append("deploy_command")

        with open(log_path, 'w', encoding='utf-8') as log:
            log.write(f"{'=' * 40}\n")
            log.write(f"PROJECT : {project_name}\n")
            log.write(f"VERSION : {version_tag}\n")
            log.write(f"STARTED : {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write(f"TIMEOUT : {timeout}s per command\n")
            log.write(f"DEPLOY  : {'SKIPPED (local)' if skip_deploy else 'ENABLED'}\n")
            log.write(f"{'=' * 40}\n\n")

            for step_name in steps:
                cmd_string = recipe.get(step_name)
                if not cmd_string:
                    continue

                print(f"    [{step_name.upper().replace('_COMMAND', '')}] Running: {cmd_string}")
                log.write(f"--- {step_name.upper()}: {cmd_string} ---\n")

                try:
                    cmd_args = shlex.split(cmd_string)
                    proc = subprocess.run(
                        cmd_args,
                        cwd=source_dir,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=timeout
                    )

                    log.write(f"STDOUT:\n{proc.stdout}\n")
                    log.write(f"STDERR:\n{proc.stderr}\n")
                    log.write(f"EXIT CODE: {proc.returncode}\n\n")

                    if proc.returncode == 0:
                        print(f"    [{step_name.upper().replace('_COMMAND', '')}] OK")
                    else:
                        print(f"    [{step_name.upper().replace('_COMMAND', '')}] FAILED (exit {proc.returncode})")
                        
                        # Show the error tail in the console so the user doesn't fly blind
                        error_output = proc.stderr.strip() if proc.stderr.strip() else proc.stdout.strip()
                        if error_output:
                            lines = error_output.split('\n')
                            tail = '\n'.join(lines[-20:]) # Show last 20 lines
                            print(f"\n      --- ERROR OUTPUT TAIL ---")
                            for line in tail.split('\n'):
                                print(f"      {line}")
                            print(f"      -------------------------\n")

                        log.write(f"!!! PIPELINE HALTED: {step_name} failed with exit code {proc.returncode}. !!!\n")
                        return log_path

                except FileNotFoundError:
                    msg = f"{cmd_string.split()[0]} not found"
                    log.write(f"FATAL: {msg}\n")
                    print(f"    [{step_name.upper()}] FATAL: {msg}")
                    return log_path

                except subprocess.TimeoutExpired:
                    msg = f"{step_name} timed out after {timeout}s"
                    log.write(f"FATAL: {msg}\n")
                    print(f"    [{step_name.upper()}] FATAL: timed out")
                    return log_path

            log.write("PIPELINE COMPLETED SUCCESSFULLY\n")

        return log_path

    def _pipeline_passed(self, log_path):
        """Returns True if the pipeline log contains the success marker."""
        if not log_path or not os.path.exists(log_path):
            return False
        with open(log_path, 'r', encoding='utf-8') as f:
            return "PIPELINE COMPLETED SUCCESSFULLY" in f.read()

    # ══════════════════════════════════════════════════════════════════════
    # VERSION MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════

    def _get_latest_version(self, project_path):
        """Returns the highest verified vN version, or None if none pass."""
        versions_path = os.path.join(project_path, "versions")
        if not os.path.exists(versions_path):
            return None
        versions = [
            d for d in os.listdir(versions_path)
            if d.startswith("v") and d[1:].isdigit()
        ]
        versions.sort(key=lambda x: int(x[1:]), reverse=True)
        build_log_dir = self._get_build_log_dir(project_path)
        for version in versions:
            log_path = self._get_latest_log_for_version(build_log_dir, version)
            if log_path and self._pipeline_passed(log_path):
                return version
        return None

    def _branch_version(self, project_path, source_v, target_v):
        """
        Creates target_v as a clean copy of source_v.
        Excludes node_modules, .next, build artifacts, and lock files.
        Returns the path to the new version directory.
        """
        source_dir = os.path.join(project_path, "versions", source_v)
        target_dir = os.path.join(project_path, "versions", target_v)

        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        ignore_func = shutil.ignore_patterns(
            'node_modules', '.next', 'dist', 'build',
            '.vercel', 'package-lock.json', '__pycache__'
        )
        shutil.copytree(source_dir, target_dir, ignore=ignore_func)
        print(f"\n  Branching {source_v} -> {target_v}...")
        return target_dir

    def _get_latest_log_for_version(self, build_log_dir, version):
        """Returns the most recent log file for a given version, or None."""
        pattern = os.path.join(build_log_dir, f"run_{version}_*.log")
        logs = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        return logs[0] if logs else None

    def _read_codebase(self, source_dir):
        """Reads codebase into XML-tagged string using BaseAI-compatible logic."""
        from vmr_tools.base_ai import BaseAI
        return BaseAI()._read_directory_to_string(source_dir)

    # ══════════════════════════════════════════════════════════════════════
    # LOG AND PATH HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _get_build_log_dir(self, project_path):
        path = os.path.join(project_path, "logs", "build")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_docs_log_dir(self, project_path):
        path = os.path.join(project_path, "logs", "docs")
        os.makedirs(path, exist_ok=True)
        return path

    def _save_critique(self, docs_log_dir, version, critique):
        """Saves the latest Design Critic output for memory on next cycle."""
        path = os.path.join(docs_log_dir, "last_critique.json")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"version": version, "critique": critique}, f, indent=2)
        except Exception as e:
            print(f"  [main] Could not save critique: {e}")

    def _load_last_critique(self, docs_log_dir):
        """Loads the previous Design Critic output, or None if not found."""
        path = os.path.join(docs_log_dir, "last_critique.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get("critique")
        except Exception:
            return None

    def _write_doc_log(self, docs_log_dir, version, event, summary, details):
        """
        Appends a human-readable entry to the project documentation log.
        Separate from build logs — intended for developer review.
        """
        doc_log_path = os.path.join(docs_log_dir, "project_history.md")
        timestamp    = time.strftime('%Y-%m-%d %H:%M:%S')

        entry = (
            f"\n---\n"
            f"## [{event}] {version} — {timestamp}\n\n"
            f"**Summary:** {summary}\n\n"
            f"**Details:**\n{details}\n"
        )

        with open(doc_log_path, 'a', encoding='utf-8') as f:
            if os.path.getsize(doc_log_path) == 0:
                f.write("# AutoForge Project History\n")
                f.write("Auto-generated by AutoForge. Do not edit manually.\n")
            f.write(entry)


if __name__ == "__main__":
    AutoForgeVMR().execute_command(sys.argv[1:])