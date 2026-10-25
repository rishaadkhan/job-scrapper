"""Sandboxed Tectonic LaTeX compiler runner with security restrictions and resource timeouts"""
import os
import shutil
import logging
import tempfile
import subprocess
from typing import Tuple, Optional

logger = logging.getLogger("latex.compiler")

DEFAULT_TIMEOUT_SEC = 20
MAX_LOG_LENGTH = 4000


def compile_latex_source(
    latex_source: str,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    subprocess_runner=None
) -> Tuple[bool, Optional[bytes], str]:
    """
    Compile a LaTeX string into PDF bytes within an isolated sandbox.
    
    Security Constraints:
    - Shell-escape disabled (TECTONIC_UNTRUSTED_MODE=1 and --untrusted flag)
    - Network access blocked inside sandbox (--only-cached / -C flag)
    - Strict wall-clock subprocess timeout (default 20 seconds)
    - Isolated temporary directory sandbox
    
    Returns:
        (success: bool, pdf_bytes: Optional[bytes], log_or_error: str)
    """
    if not latex_source or not latex_source.strip():
        return False, None, "Compilation error: LaTeX source code is empty."

    with tempfile.TemporaryDirectory(prefix="tectonic_sandbox_") as temp_dir:
        input_file = os.path.join(temp_dir, "document.tex")
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(latex_source)

        tectonic_bin = shutil.which("tectonic") or "tectonic"
        
        # Hardened CLI flags:
        # -C / --only-cached: Do not access network for packages
        # --untrusted: Disable shell escape and restrict file writes
        # -o / --outdir: Output directory
        cmd = [
            tectonic_bin,
            "-C",
            "--untrusted",
            "-o",
            temp_dir,
            input_file
        ]

        env = os.environ.copy()
        # Enforce untrusted mode and disable network proxies
        env["TECTONIC_UNTRUSTED_MODE"] = "1"
        env["http_proxy"] = ""
        env["https_proxy"] = ""
        env["ALL_PROXY"] = ""
        env["NO_PROXY"] = "*"

        runner = subprocess_runner or subprocess.run

        try:
            result = runner(
                cmd,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout_sec,
                env=env,
                check=False
            )
        except subprocess.TimeoutExpired as exc:
            msg = f"Compilation timed out after {timeout_sec} seconds (wall-clock limit exceeded)."
            logger.warning(msg)
            return False, None, msg
        except FileNotFoundError:
            msg = f"Tectonic executable '{tectonic_bin}' not found on system PATH."
            logger.error(msg)
            return False, None, msg
        except Exception as exc:
            msg = f"Unexpected error during compiler subprocess execution: {str(exc)}"
            logger.error(msg)
            return False, None, msg

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        log_content = f"{stdout}\n{stderr}".strip()

        # Check for generated log file if available
        logfile_path = os.path.join(temp_dir, "document.log")
        if os.path.exists(logfile_path):
            try:
                with open(logfile_path, "r", encoding="utf-8", errors="replace") as lf:
                    log_content = f"{log_content}\n--- document.log ---\n{lf.read()}".strip()
            except Exception:
                pass

        if result.returncode != 0:
            truncated_log = (
                log_content[-MAX_LOG_LENGTH:]
                if len(log_content) > MAX_LOG_LENGTH
                else log_content
            )
            logger.warning(f"Tectonic compilation failed with exit code {result.returncode}")
            return False, None, truncated_log or f"Compilation failed with exit code {result.returncode}"

        pdf_path = os.path.join(temp_dir, "document.pdf")
        if not os.path.exists(pdf_path):
            return False, None, "Compilation succeeded but no output PDF was found in sandbox."

        try:
            with open(pdf_path, "rb") as pf:
                pdf_bytes = pf.read()
            return True, pdf_bytes, ""
        except Exception as e:
            return False, None, f"Failed to read compiled PDF: {str(e)}"
