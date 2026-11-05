import re

FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
MIN_QUOTE_LENGTH = 12


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_snippets(answer: str) -> list[str]:
    snippets = []
    for block in FENCE.findall(answer):
        for piece in re.split(r"\.\.\.|…", block):
            piece = _normalize(piece)
            if len(piece) >= MIN_QUOTE_LENGTH:
                snippets.append(piece)
    return snippets


def check_quotes(answer: str, steps) -> tuple[int, list[str]]:
    corpus_parts = []
    for s in steps:
        if s.tool_name == "read_file" and isinstance(s.result, dict):
            inner = s.result.get("result")
            if isinstance(inner, dict):
                corpus_parts.append(inner.get("content", ""))
    corpus = _normalize(" ".join(corpus_parts))

    snippets = extract_snippets(answer)
    missing = [sn for sn in snippets if sn not in corpus]
    return len(snippets), missing