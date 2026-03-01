import re
import shlex


def handle_regex(args: list, reply):
    if reply is None:
        return """
Please reply to a message to use this command.
Usage: `;;s <pattern> <replacement> [flags g, i]`
        """

    if not reply.resolved.content:
        return """
Cannot regex an empty message or a message with only attachments.
Usage: `;;s <pattern> <replacement> [flags g, i]`
        """

    if len(args) < 3:
        return "Usage: `;;s <pattern> <replacement> [flags]`"

    try:
        raw = " ".join(args[1:])
        parts = shlex.split(raw)
    except ValueError as e:
        return f"Parsing error: `{e}`"

    if len(parts) < 2:
        return "Usage: `;;s <pattern> <replacement> [flags]`"

    pattern, replacement, *rest = parts
    flags_str = rest[0] if rest else ""

    flags = 0
    count = 1

    flags_set = set(flags_str)
    digits = re.search(r"\d+", flags_str)

    if "g" in flags_set:
        count = 0
    if digits:
        count = int(digits.group())
    if "i" in flags_set:
        flags |= re.IGNORECASE

    string = reply.resolved.content

    try:
        result = re.sub(pattern, replacement, string, count=count, flags=flags)
    except re.error as e:
        return f"Invalid regex pattern: `{e}`"

    if result == string:
        return "No matching pattern found."

    return result
