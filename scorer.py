def judge(question: str, expects: str, answer: str, results) -> bool:
    """Return True when the generated answer contains the expected phrase."""
    if not expects:
        return False
    return expects.strip().lower() in (answer or "").lower()
