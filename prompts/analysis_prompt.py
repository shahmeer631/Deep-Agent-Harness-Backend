"""Analyze skills and experience depth before job matching."""

ANALYZE_CANDIDATE_PROMPT = """
You are enriching a parsed candidate profile before job matching.

Candidate profile JSON:
{candidate_json}

Resume excerpt:
---
{resume_excerpt}
---

Return JSON with keys:
skills_analysis (string: 2-4 sentences on skill depth and focus areas),
experience_analysis (string: 2-4 sentences on seniority, ownership, and trajectory),
domain_signals (string array: domains like SaaS, AI, fintech, etc.),
seniority_estimate (string: one of "intern", "junior", "mid", "senior", "staff", "unknown"),
red_flags (string array: missing or weak signals only if evidence-based; empty if none).

Rules:
- Do not invent employers, titles, or skills.
- Prefer conservative seniority estimates.
- Be specific and useful for a hiring manager.
""".strip()
