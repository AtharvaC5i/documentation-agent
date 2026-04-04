def score_quality(section_name: str, content: str) -> float:
    """
    Scores generated section content from 0.0 to 1.0.
    Checks length, structure, and relevance signals.
    """
    if not content or not content.strip():
        return 0.0

    score = 0.0
    words = content.split()
    word_count = len(words)

    # Length scoring — 0.0 to 0.4
    if word_count >= 300:
        score += 0.4
    elif word_count >= 150:
        score += 0.25
    elif word_count >= 50:
        score += 0.1

    # Structure scoring — 0.0 to 0.3
    has_headers  = "#" in content
    has_bullets  = "- " in content or "* " in content
    has_code     = "```" in content
    has_tables   = "|" in content

    structure_count = sum([has_headers, has_bullets, has_code, has_tables])
    score += min(structure_count * 0.1, 0.3)

    # Relevance scoring — 0.0 to 0.3
    # Check section name keywords appear in content
    section_keywords = section_name.lower().split()
    content_lower    = content.lower()
    matches          = sum(1 for kw in section_keywords if kw in content_lower)
    keyword_ratio    = matches / max(len(section_keywords), 1)
    score += keyword_ratio * 0.3

    return round(min(score, 1.0), 2)
