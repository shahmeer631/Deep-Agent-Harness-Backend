PARSE_RESUME_PROMPT = """
Extract a structured candidate profile from the resume text.

Return JSON with keys:
name, email, skills, education, experience, projects, certifications, summary.

Rules:
- skills: concise skill strings only
- education/experience/projects/certifications: short factual bullets
- If a list field has no data, return [] (never null)
- summary: 2-3 sentences on career focus
- Use null for email only if truly absent
- Do not invent facts

Resume text:
---
{resume_text}
---
""".strip()


MATCH_CANDIDATE_PROMPT = """
Compare this candidate against the job description and produce a calibrated screening assessment.

Candidate profile JSON:
{candidate_json}

Job title: {job_title}

Job description:
---
{job_description}
---

Return JSON with keys:
match_score (0-100 integer),
strengths (string array),
weaknesses (string array),
skills_matched (string array),
skills_missing (string array),
experience_summary (string),
recommendation (string, include clear next step),
recommendation_label ("hire" | "maybe" | "pass"),
reasoning (string explaining the score).

Scoring guidance:
- 85-100: exceptional alignment on must-haves + strong evidence
- 70-84: solid hire-track candidate with manageable gaps
- 55-69: mixed fit; interview only if gaps are trainable
- below 55: weak fit for this role as written
""".strip()


INTERVIEW_QUESTIONS_PROMPT = """
Generate targeted interview questions for this candidate and role.

Candidate profile JSON:
{candidate_json}

Match assessment JSON:
{match_json}

Job title: {job_title}

Job description:
---
{job_description}
---

Return JSON with keys:
technical (3-5 questions),
behavioral (2-3 questions),
follow_up (2-3 questions probing the identified gaps).

Questions must be specific to this candidate's background and the role's requirements.
Avoid generic trivia.
""".strip()
