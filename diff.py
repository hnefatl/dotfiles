import difflib


def diff(a: str, b: str) -> list[str]:
    return list(difflib.ndiff(a.splitlines(), b.splitlines()))


def pretty_print(diff: list[str], context_lines: int = 2):
    relevant_lines = set[int]()
    for i, line in enumerate(diff):
        if not line.startswith("  "):
            relevant_lines.update(range(i - context_lines, i + context_lines))

    last_i = None
    for i in sorted(relevant_lines):
        if i < 0 or i >= len(diff):
            continue

        # If we've skipped a range, show a marker
        if last_i is not None and i != last_i + 1:
            print("...")
        print(_format_colourful(diff[i]))
        last_i = i


def _format_colourful(line: str) -> str:
    if line.startswith("-"):
        return f"\033[38;2;255;0;0m{line}\033[38;2;255;255;255m"
    elif line.startswith("+"):
        return f"\033[38;2;0;255;0m{line}\033[38;2;255;255;255m"
    else:
        return line
