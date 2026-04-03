"""
Console logger — prints structured, coloured pipeline logs to terminal.
Import and call anywhere in the pipeline.
"""

import datetime

# ANSI colour codes
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
GREY   = "\033[90m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"

def _ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def info(stage: str, msg: str):
    print(f"{GREY}[{_ts()}]{RESET} {CYAN}{BOLD}[{stage}]{RESET} {msg}")

def success(stage: str, msg: str):
    print(f"{GREY}[{_ts()}]{RESET} {GREEN}{BOLD}[{stage}]{RESET} ✓ {msg}")

def warn(stage: str, msg: str):
    print(f"{GREY}[{_ts()}]{RESET} {YELLOW}{BOLD}[{stage}]{RESET} ⚠ {msg}")

def error(stage: str, msg: str):
    print(f"{GREY}[{_ts()}]{RESET} {RED}{BOLD}[{stage}]{RESET} ✗ {msg}")

def step(stage: str, n: int, total: int, msg: str):
    bar_filled = int((n / total) * 20)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    print(f"{GREY}[{_ts()}]{RESET} {MAGENTA}{BOLD}[{stage}]{RESET} [{bar}] {n}/{total} {msg}")

def divider(title: str = ""):
    line = "─" * 55
    if title:
        print(f"\n{BLUE}{BOLD}{line}{RESET}")
        print(f"{BLUE}{BOLD}  {title}{RESET}")
        print(f"{BLUE}{BOLD}{line}{RESET}")
    else:
        print(f"{GREY}{line}{RESET}")

def llm_call(stage: str, purpose: str, tokens_in: int = 0):
    print(f"{GREY}[{_ts()}]{RESET} {YELLOW}[{stage} → Databricks]{RESET} {purpose}" +
          (f" | input ~{tokens_in} chars" if tokens_in else ""))

def llm_response(stage: str, chars_out: int, recovered: bool = False):
    note = f" {YELLOW}(truncation recovered){RESET}" if recovered else ""
    print(f"{GREY}[{_ts()}]{RESET} {GREEN}[{stage} ← Databricks]{RESET} {chars_out} chars received{note}")
