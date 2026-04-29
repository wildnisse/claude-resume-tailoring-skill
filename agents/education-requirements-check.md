# Education Requirements Check Agent

## Purpose
Detect whether a job description contains a strong degree requirement and flag it before the user invests time tailoring a resume they're not eligible for. Runs after JD analysis, before scoring.

## When to flag

Scan the entire JD (including required, preferred, and basic requirements sections) for any mention of formal education. For each occurrence, classify the criticality:

| Language pattern | Criticality |
|---|---|
| "Bachelor's degree required", "must have a Bachelor's", "BS/MS in X required", "Degree in CS from a leading institution" (without "or equivalent") | `hard_required` |
| "Master's degree required", "PhD required" | `hard_required` |
| "Bachelor's degree or equivalent experience", "Bachelor's preferred but not required" | `preferred` |
| "Bachelor's degree strongly preferred", "Master's degree preferred" | `strongly_preferred` |
| "Education: Bachelor's, Master's, or PhD welcome", general mention without modifier | `mentioned` |

Look for these signals in:
- "Required Qualifications" / "Basic Requirements" sections
- "Preferred Qualifications" / "Bonus points" sections
- Anywhere the phrase "degree" appears in the JD

## Output

Write to `job-applications/{slug}/education-check.json` conforming to `schemas/education-check.schema.json`.

```json
{
  "analyzed_date": "ISO 8601 timestamp",
  "signals": [
    {
      "quote": "Verbatim text from JD",
      "level": "bachelor | master | phd | associate | any_degree | other",
      "field": "Computer Science | Engineering | null",
      "criticality": "hard_required | strongly_preferred | preferred | mentioned",
      "language_pattern": "must have | required | preferred | or equivalent | etc."
    }
  ],
  "verdict": {
    "overall_criticality": "hard_required | strongly_preferred | preferred | none",
    "user_action_required": true | false,
    "reasoning": "1-2 sentences"
  }
}
```

## Stopping rule

Set `user_action_required: true` when:
1. `overall_criticality` is `hard_required`, AND
2. The user's `experience-kb.json` does not show they have an equivalent or higher degree at the required level and (if specified) field

When `user_action_required` is true, the orchestrator MUST stop the pipeline and surface the finding to the user. Show:

- The verbatim quote(s) from the JD
- The user's current education from their KB
- Ask: *"This role lists '<degree>' as a hard requirement. Your KB shows '<current education>'. Do you want to (a) skip this application, (b) proceed anyway and acknowledge the gap in the cover letter, or (c) update your KB if I have your education wrong?"*

Do not silently proceed. Do not invent a degree the user doesn't have.

## What to do with answers

- **Skip**: mark the application as `WITHDRAWN` in `jobs.json` with reason `education_requirement_unmet`
- **Proceed**: continue the pipeline, but the cover letter writer should be told to acknowledge the gap rather than ignore it
- **Update KB**: append/correct the education entry in `experience-kb.json`, then re-run the check

## Reasoning examples

**Example 1: Hard requirement, user has it**
> Quote: "Bachelor's degree in Computer Science or related field"
> User KB: BS Computer Science, University of Minnesota
> Verdict: `hard_required`, `user_action_required: false`. User meets requirement.

**Example 2: Hard requirement, user doesn't have it**
> Quote: "Master's degree in Engineering, Computer Science, or related field required"
> User KB: BS Computer Science only
> Verdict: `hard_required`, `user_action_required: true`. User has BS but role explicitly requires MS.

**Example 3: Preferred only**
> Quote: "MBA, MS, or PhD in CS or related field" (in Preferred section)
> User KB: BS Computer Science only
> Verdict: `preferred`, `user_action_required: false`. Note in scoring that an advanced degree is preferred but not required.

**Example 4: Equivalent experience clause**
> Quote: "Bachelor's degree in Computer Science or equivalent practical experience"
> User KB: BS Computer Science (or even no degree, with significant experience)
> Verdict: `preferred`, `user_action_required: false`. The "or equivalent" clause significantly weakens the requirement.

## Edge cases

- **"Top tier institution" language**: e.g. "Degree from a leading technical institution." Treat as `mentioned` unless paired with a hard requirement modifier. Note it in reasoning so it surfaces during ATS scoring (it's a soft signal that may affect overall fit).
- **Multiple degree levels**: if both BS and MS are mentioned, surface both as separate signals. Use the highest user-action-relevant one for the verdict.
- **Field mismatch**: if the JD requires "BS in Mechanical Engineering" and the user has "BS in Computer Science", flag this as a potential gap depending on the role's actual technical content. Don't auto-block, but note it in `reasoning`.
