# Style & Authenticity Rules

These are skill defaults. They apply to ALL generated artifacts: resumes, cover letters, hiring manager messages, application question answers. The user's `CLAUDE.md` may ADD personal rules or overrides, but these defaults hold unless explicitly overridden.

These rules exist because recruiters are saturated with AI-generated applications and have developed pattern recognition for them. An application that reads as generated gets a worse response than a plain one, because it signals lack of authenticity AND lack of judgment. Every rule below is enforced two ways: by `tools/lint_artifacts.py` (deterministic, run before READY) and by the ATS scorer (independent context, evidence required). Do not rely on "I followed the rules" — run the lint.

## Writing style defaults

- **No em-dashes.** Anywhere. Use commas, periods, or restructure.
- **Voice**: first person, conversational and direct. Short declarative sentences mixed with longer ones.
- **Banned phrases**:
  - "I'd love to" / "I'm excited to" / "I look forward to"
  - "I believe that" / "I'm passionate about"
  - "leveraging" / "synergy" / "champion" / "spearheaded" / "transformative"
  - "I'd be a great fit" / "I am writing to apply"
- **No confessional hedging.** Banned: "the honest stretch", "the honest gap", "to be honest", "my honest take", "I'll be straight", "I will be straight", "I want to be straight", "full transparency", "if I'm being honest", and close variants. When a real gap exists, address it forward: state what the candidate HAS done, then frame the gap as the next step they want. Lead with strength, not apology.
- **No defensive authenticity.** Banned: the entire "this is real, not slides" construction family: "not a slide", "not slides", "not a deck", "not a side experiment", "not as a demo", and the contrast-fragment pattern "Not as X. As Y." Concreteness proves authenticity; protesting it is itself an AI tell. If the work is real, the specifics carry it.
- **No unfalsifiable boost pairs.** Banned: "measurable, provable", "real, tangible", "concrete, demonstrable" and similar adjective pairs standing in for an actual number. Use one real number, or defer cleanly ("happy to walk through the numbers"), once, in the letter only.
- **Never reuse example sentences from this file, `CLAUDE.md`, or any agent prompt verbatim in an artifact.** Examples illustrate a shape; copying them ships the same sentence to multiple companies.

## Sentence-level AI tells (the mechanical fingerprints)

Recruiters now pattern-match the *mechanics* of generated prose, not just its filler phrases. A resume can be free of every banned phrase and still read as machine-written because the rhythm gives it away. These are the fingerprints. The lint flags them, but write to avoid them in the first place; a flagged artifact is a rewrite, not a debate.

- **Break the rule of three.** The single clearest machine tell is the relentless three-item list: "embeddings, vector search, and tool-calling," "strategy, architecture, and roadmaps," "X, Y, and Z" over and over. One or two triples in a document is human; five is a model. Vary list length deliberately, cut to two, push to four, or restructure into a clause. If three bullets in a row all resolve to a tidy triple, rewrite at least one. The lint warns past a density threshold.
- **No closing-appositive flourishes.** Do not end a sentence with a comma and a coda that restates its value: "...feeding a BigQuery warehouse, the data estate the business ran on," or "...budget limits, with usage shown back to the teams driving it." State the fact and stop. That tacked-on "main clause, comma, restated value" shape is the most recognizable LLM sentence in existence.
- **No balanced antithesis openers.** Banned (lint errors): "Equally at home in X and Y," "Equal parts X and Y," "Part engineer, part operator," "as comfortable in the code as in the boardroom." These workshopped, quotable lines read as written, not lived. A doer states what they did; only a copywriter balances a clause.
- **Name a fact, not a virtue.** Aphoristic value statements, "owns compliance as part of the platform," "with reliability built in from day one," "spend visibility baked in," assert a posture where the bullet should give the audit, the SLA, the dollar, or the number. If you cannot attach a concrete to the claim, cut the line.
- **No elevated or literary diction.** This is an engineer's resume, not an essay. Avoid "estate," "tapestry," "realm," "ethos," "underpin," "seamless," "harness," "unlock," "elevate," "pivotal," "myriad." Use the plain word ("environment," not "estate"; "built," not "harnessed").
- **Do not repeat a flagship phrase or claim.** If "stood up" or "from zero" lands once, it must not reappear two more times across the summary, highlights, and bullets, that is a model redeploying its favorite tokens. And assert any single claim once, with the strongest evidence: executive proximity stated three times in three costumes ("technical voice alongside the C-suite" / "partner to the C-suite" / "trusted advisor to the C-suite") reads as insecurity, not strength. Say it once and move on.

## Cross-application freshness

Every artifact must be written fresh. The lint compares new letters and summaries against all prior applications and flags shared word sequences. Specific rules:

- **Rotate closers.** "Happy to talk." has been used to death. Vary the closing line per letter.
- **Rotate proof points.** When the candidate has a set of recurring proof points (e.g. three AI credentials), pick the two most relevant to THIS role and vary the order and framing. Never recite the full set in canonical order; that is the template showing.
- **Vary the skeleton.** Do not use the same paragraph structure (hook, proof, gap, close) in every letter. Sometimes lead with a story. Sometimes put the gap up front. Sometimes skip the gap paragraph entirely when the fit is strong. A reader of any two letters should not be able to derive the template.

## Resume voice rules

The resume must NOT look custom-built for the specific JD. Tailoring is real (reordering, emphasis, surfacing relevant accomplishments) but must remain invisible. Specific JD references belong in cover letters and hiring manager messages, never in the resume.

- **The summary is identity, not response, and short.** Write it as "who I am as an engineer," not "why I fit this role." Do not name the target company. Do not name the target domain as a thing the candidate is moving toward. Do not echo JD phrases. Do not include lines that answer JD asks ("US work authorization", "Eastern Time"); those belong in the cover letter or header. If a recruiter read the summary cold across ten different JDs, it should sound like the same person every time.
  - **Keep it tight: three to four sentences, well under ~75 words.** A dense, six-line summary is a place recruiters skip, not read, and the keyword density itself signals an over-tuned, generated document. The lint warns past the limit.
  - **Limit embellishment and role-specific detail.** Do not pack the summary with acronyms, a catalog of technologies, or specifics aimed at one posting, that targeted density is the dead giveaway that the summary was built for a single JD. Surface the durable signal (who the candidate is, the scale they operate at) and let the experience section carry the technical proof. One or two genuinely-owned domain words are fine; a stuffed list is not.
- **Highlights headers use career-pattern phrasing, not JD-response phrasing.** "Builder Track Record", not "Building From Zero" when the JD asks for build-from-zero. Surface the substance; do not mirror the headline.
- **Bullets may emphasize relevant facts but must not mirror JD vocabulary verbatim.** One owned phrase is fine. Three echoes across the document is pandering.
- **Read-aloud test**: if the summary sounds like the first paragraph of the cover letter, it is over-tailored. Rewrite to identity voice.

What remains legitimate: reordering so the most relevant role leads; bullet selection; emphasis (hero role 4-5 bullets, credibility role 1-2); domain vocabulary the candidate genuinely owns (e.g. "HIPAA" when they have HIPAA experience, regardless of whether the JD asks).

## Altitude rules

Match the resume's vocabulary to the level of the role. This matters most ABOVE Director:

- **VP and above**: lead with org design, business outcomes, exec partnership, budget and capital decisions, multi-year strategy. CUT stack enumeration. A VP resume that lists "Kotlin microservices on Azure and Kubernetes with Kafka and Postgres" reads as senior-manager. Name a technology only when it IS the business story (e.g. a replatform).
- **Never name IDE plugins or dev tools (Cursor, Cline, Copilot) above Senior Manager level.** "Runs an AI-first engineering practice" with one shipped-product proof point carries the same signal at the right altitude. Tool names belong on IC and hands-on-architect resumes only.
- **Director and below / player-coach roles**: technical specificity is an asset. Hands-on currency, real tools, real architecture decisions.
- **Down-level applications** (candidate applying below their proven scope): do not flag or apologize for overqualification in the resume. Frame as deliberate (hands-on by choice). Prepare the commitment story for the screen instead.

## Length

There is no single-page rule. Resume length follows seniority:

- **Under ~10 years of experience**: one page.
- **10+ years, or any leadership resume**: two pages is the standard, and forcing one page is itself a signal (it reads junior, and it forces cutting career history that recruiters expect to see). Use the room for a complete timeline rather than denser text.
- **Never more than two pages.** Past two, cut.
- **Early-career roles belong on the resume**, compressed, not omitted. A career that visibly starts mid-seniority invites timeline questions. Use a compact "Earlier roles" block at the end of experience: title, company, years, with at most one line each (often none). This keeps 25 years of history honest in 4-6 lines.
- **No dangling pages.** A second page with three lines on it is worse than either length. The build step reports the PDF page count; if page two is under roughly a third full, rebalance (expand the hero role, restore an earlier-roles block, or trim back to one page deliberately).

## Numbers

- Use the candidate's verified metrics from `experience-kb.json`, identically, everywhere. Consistency across applications is what truth looks like and it survives reference checks.
- Canonical figures (years of experience, org sizes, revenue numbers) must never drift to fit a JD's band. If the KB says one number, every artifact says that number.
- Never invent, round up, or extrapolate a metric. A bullet with no number beats a bullet with a soft one.
- **Distribute proof across the timeline; don't let the recent roles go metric-thin.** A resume where the older roles are number-dense and the most recent roles are all-qualitative reads as a plateau, a decline, or padding, regardless of how real the recent work is. A hiring manager weighs recent evidence most heavily, so the top of the timeline needs at least one hard concrete per role (adoption, throughput, revenue touched, team size, time recovered), not just responsibilities. If the recent work genuinely has no number yet, that is a knowledge-base gap to fill with a real figure or surface to the user, never a place to compensate with adjectives. Check the distribution before shipping: if every quantified accomplishment is more than a few years old, the resume is telling the wrong story about where the candidate is now.
