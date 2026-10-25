"""LaTeX validator for checking structural integrity and required editable markers"""
import re
from typing import List, Tuple
from backend.exceptions import ValidationError


def strip_latex_comments(source: str) -> str:
    """
    Remove LaTeX comments (from unescaped % to end of line).
    Preserves newlines for line numbering context.
    """
    cleaned_lines: List[str] = []
    for line in source.splitlines():
        # Match unescaped % (not preceded by odd number of backslashes)
        # Using negative lookbehind for single backslash
        idx = 0
        in_escape = False
        comment_start = -1
        while idx < len(line):
            char = line[idx]
            if char == "\\" and not in_escape:
                in_escape = True
            elif char == "%" and not in_escape:
                comment_start = idx
                break
            else:
                in_escape = False
            idx += 1

        if comment_start != -1:
            cleaned_lines.append(line[:comment_start])
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def validate_latex_source(source: str) -> None:
    """
    Validate that LaTeX source is parseable and contains required editable markers.
    
    Checks:
    1. Source is non-empty.
    2. Contains at least one '%-- AI:EDITABLE START --%' marker.
    3. Environments (\\begin{...} and \\end{...}) are balanced in LIFO order.
    
    Raises ValidationError if any condition is violated.
    """
    if not source or not source.strip():
        raise ValidationError(message="LaTeX validation error: Source code cannot be empty.")

    # 1. Check for AI editable marker (case-insensitive check for resilience, but requiring the marker)
    has_marker = (
        "%-- AI:EDITABLE START --%" in source
        or bool(re.search(r"%\s*--\s*AI:EDITABLE\s+START\s*--%", source, re.IGNORECASE))
    )
    if not has_marker:
        raise ValidationError(
            message="LaTeX validation error: Missing required marker '%-- AI:EDITABLE START --%'. "
                    "Resume template must designate at least one AI-editable section."
        )

    # 2. Check balanced \begin and \end environments
    code_without_comments = strip_latex_comments(source)
    env_pattern = re.compile(r"\\(begin|end)\{([a-zA-Z0-9*_-]+)\}")
    
    stack: List[str] = []
    for match in env_pattern.finditer(code_without_comments):
        action, env_name = match.group(1), match.group(2)
        if action == "begin":
            stack.append(env_name)
        elif action == "end":
            if not stack:
                raise ValidationError(
                    message=f"LaTeX validation error: Unexpected '\\end{{{env_name}}}' with no preceding '\\begin{{{env_name}}}'."
                )
            expected = stack.pop()
            if expected != env_name:
                raise ValidationError(
                    message=f"LaTeX validation error: Mismatched environment. Expected '\\end{{{expected}}}' but found '\\end{{{env_name}}}'."
                )

    if stack:
        unclosed = ", ".join(f"'\\begin{{{env}}}'" for env in stack)
        raise ValidationError(
            message=f"LaTeX validation error: Unclosed LaTeX environment(s): {unclosed}. "
                    "Every \\begin must have a matching \\end."
        )
