# The Unofficial Guide

Manushri - corpus: `campus_life`

---

# Unit 1

## What This Does

This project builds a retrieval-augmented question-answering guide for the `campus_life` corpus. The corpus contains 88 short student-life posts about university dining, housing, courses, transportation, studying, money, health, and administrative rules. Users can ask specific factual questions such as when housing lottery numbers come out, how often the shuttle runs, or which study rooms have usable whiteboards. The system retrieves relevant chunks from Chroma, applies a relevance gate before generation, and asks the model to answer only from the retrieved documents while naming source filenames.

## Chunking Strategy

**Chunk size:** 700 characters target maximum
**Overlap:** 0 characters

The selected corpus is made of short posts rather than long guides: `corpora/README.md` describes `campus_life` as 88 documents averaging about 317 characters, and the measured corpus ranged from 178 to 549 characters per document. Useful information usually sits in one sentence or paragraph, but the title gives important context, so keeping each post whole makes more sense than splitting inside the post. The starter strategy used fixed-size character windows with 120 characters of overlap; for this corpus, that did not usually cut documents, but it still treated chunking as a character-count problem instead of a post-boundary problem.

The final chunker is `chunker.py::split_documents`. It keeps short posts whole, packs longer documents by paragraph if needed, and only falls back to sentence-aware splitting for unusually long paragraphs. With the final chunker, `campus_life` has 88 documents and 88 chunks, with an average chunk length of 317 characters, shortest chunk 178, and longest chunk 549.

## Sample Chunks

**Chunk 1** - source: `admin_add_drop_deadline.txt#0` - produced by: `chunker.py::split_documents`

```text
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** - source: `course_biol_160.txt#0` - produced by: `chunker.py::split_documents`

```text
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

Expect 9 to 11 hours a week, the heaviest first-year course by reputation.

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

**Chunk 3** - source: `course_hist_118_workload.txt#0` - produced by: `chunker.py::split_documents`

```text
Workload for HIST 118 Modern World History

People keep asking so: a lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** - source: `dining_pellew_dining_hall_followup.txt#0` - produced by: `chunker.py::split_documents`

```text
Re: Pellew Dining Hall

Adding to what people have said about Pellew Dining Hall. The wait figure of 12 to 18 minutes at peak matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: the furthest hall from anywhere, next to the athletics centre. Nobody tells you this at orientation.
```

**Chunk 5** - source: `housing_innisfree_hall.txt#0` - produced by: `chunker.py::split_documents`

```text
Innisfree Hall — what it's actually like

Transferred in last year, so take this with a grain of salt. Built 1991, renovated 2022. Rooms are doubles arranged as pairs sharing one bathroom between two rooms.

The good: the shared-bathroom-between-two-rooms arrangement is the best compromise on campus.

The bad: no air conditioning, which matters for the first three weeks of September.

Laundry costs $1.75 wash, $1.75 dry, app-based. On noise: moderate; the building is L-shaped and the short wing is much quieter.
```

## Sample Answer

**Question:** When do housing lottery numbers come out?

**Answer:**

```text
Housing lottery numbers come out the second week of March (admin_housing_lottery.txt).
```

**Source line/document visible:** `Sources retrieved: admin_housing_lottery.txt, admin_parking_permits.txt, admin_withdrawal_deadline.txt, advising_registration.txt, dining_halden_hall_followup.txt`

**My relevance cutoff:** 0.62

I chose 0.62 after measuring the five in-corpus questions and the five `OUT_OF_SCOPE` questions. The in-scope best distances ranged from 0.2316 to 0.4251. The out-of-scope best distances ranged from 0.8246 to 0.9340. There was a clean gap between the two groups, so 0.62 sits between the hardest in-scope question and the closest out-of-scope question. What could go wrong: a future valid question worded very differently from the corpus could land above 0.62 and be refused, or a future off-topic question about campus-like language could land below 0.62.

| Question | In corpus? | Best distance |
|---|---|---:|
| When do housing lottery numbers come out? | Yes | 0.3453 |
| What is the best time to do laundry in Calder Annexe? | Yes | 0.2972 |
| How often does the campus shuttle run on weekdays? | Yes | 0.4251 |
| How late can a student declare a course pass/fail? | Yes | 0.2316 |
| Which group study rooms have whiteboards that actually erase? | Yes | 0.3436 |
| What is the capital of Mongolia? | No | 0.8246 |
| How do I change the oil in a diesel engine? | No | 0.9340 |
| Who won the 1994 World Cup? | No | 0.8859 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.8442 |
| How do I write a for loop in Rust? | No | 0.8960 |

## How I Used AI

**1.** I asked Codex to inspect the actual repository and corpus before changing code. Codex read the project instructions, starter files, corpus documentation, and multiple `campus_life` documents; it found that my corpus uses short post-style documents and implemented a post-aware chunker that keeps each short source document intact.

**2.** I asked Codex to measure retrieval distances and choose a relevance cutoff from real outputs. Codex ran all five in-scope questions and all five out-of-scope questions, found a clear distance gap, and set the cutoff to 0.62 based on that evidence.

---

# Unit 2

This unit tested the five criteria in `criteria.md` against real runs, then made one measured improvement. The baseline evidence came from `results/run_2026-09-27_1847_before.md`, produced by `run_eval.py::main`. Retrieval came from `store.py::search`, chunks came from `chunker.py::split_documents`, and generation ran with caching off.

## Run Log - Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks do not cut off sentences | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Answers include the expected phrase | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Representative baseline output from `results/run_2026-09-27_1847_before.md`:

```text
When do housing lottery numbers come out? - run 1
Best distance: 0.3453 (passed the gate)
Sources retrieved: admin_housing_lottery.txt, admin_parking_permits.txt, admin_withdrawal_deadline.txt, advising_registration.txt, dining_halden_hall_followup.txt

Housing lottery numbers come out the second week of March (admin_housing_lottery.txt).
```

For the out-of-corpus gate criterion, `run_eval.py::check_out_of_scope` refused 5 of 5 questions at cutoff 0.62:

```text
refused (best distance 0.825) What is the capital of Mongolia?
refused (best distance 0.934) How do I change the oil in a diesel engine?
refused (best distance 0.886) Who won the 1994 World Cup?
refused (best distance 0.844) What is the recommended dosage of ibuprofen for a headache?
refused (best distance 0.896) How do I write a for loop in Rust?
```

For the chunk-boundary criterion, `python app.py chunks -n 5` sampled five chunks produced by `chunker.py::split_documents`. All five began at a title or sentence boundary and ended after a complete sentence or paragraph.

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer | MET | For all five questions, the retrieved source list included the document containing the expected fact in every run. |
| 2 | Every answer names a source | MET | All 15 generated answers named at least one source filename, usually in parentheses or a `Source:` line. |
| 3 | The relevance gate stops out-of-corpus questions | MET | The gate refused 5 of 5 out-of-corpus questions, exceeding the 4 of 5 target. This deterministic gate result was copied into all three run columns. |
| 4 | Chunks do not cut off sentences | MET | The five sampled chunks from `app.py chunks -n 5` all started and ended cleanly. |
| 5 | Answers include the expected phrase | MET | All 15 generated answers contained the expected phrase from `questions.py`, ignoring capitalization. |

## Diagnoses

No baseline criterion was missed. The main pattern was that my criteria were safe for this corpus: each question points to a short, single-source post, and the correct document was usually ranked first.

Even though nothing failed, I noticed one weakness in the baseline retrieval output: `TOP_K = 5` gave the model extra distractor chunks. For example, the baseline housing lottery answer retrieved the correct `admin_housing_lottery.txt`, but also included unrelated sources such as `dining_halden_hall_followup.txt`. The generated answer still stayed grounded, so this was not a miss, but the prompt carried more irrelevant context than it needed.

## The Improvement

**What I changed:** I changed `TOP_K` in `config.py` from 5 to 3. I also added `scorer.py`, using the in-class helper shape `judge(question, expects, answer, results) -> bool`, so future eval logs mark expected-phrase checks automatically. The system behavior change was the retrieval setting.

**Why I picked it:** The baseline did not have a failing criterion, so I chose the smallest improvement supported by the evidence: reduce irrelevant context while keeping the correct source in the retrieved set. In the baseline, every correct source was already ranked in the top 1, so lowering top-k from 5 to 3 should preserve correctness while sending fewer distractor chunks to the model.

### Run Log - After

After evidence came from `results/run_2026-09-27_1921_after.md`, produced by `run_eval.py::main` with top-k 3 and cutoff 0.62.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks do not cut off sentences | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Answers include the expected phrase | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Representative after output:

```text
When do housing lottery numbers come out? - run 1
Best distance: 0.3453 (passed the gate)
Sources retrieved: admin_housing_lottery.txt, admin_parking_permits.txt, advising_registration.txt

Housing lottery numbers come out the second week of March (admin_housing_lottery.txt).
```

**Did it help?** It helped with prompt size and did not hurt the five criteria. The baseline used 9,068 total tokens, including 8,646 prompt tokens. The after run used 6,403 total tokens, including 5,979 prompt tokens. That is 2,667 fewer prompt tokens while all five criteria stayed MET. The retrieval source lists also became shorter: for the housing lottery question, the irrelevant `admin_withdrawal_deadline.txt` and `dining_halden_hall_followup.txt` chunks were no longer sent to the model.

## What's Still Broken

No original criterion is still missed after the improvement. What is still weak is the evaluation design: the questions are straightforward, and the criteria do not stress harder cases where the correct source is ranked lower, the answer spans documents, or the gate sees an out-of-scope question with campus-like wording.

The next improvement I would try is a harder evaluation set, not another system tweak. I would add questions that use synonyms, ask for comparison between two documents, or intentionally mention plausible but absent campus topics. I stopped after one improvement because the assignment asks for one measured change, and the top-k change already showed a measurable token reduction without regression.

## What I'd Do Differently

I would make criterion 1 more precise by saying "the top three retrieved chunks contain the answer for at least 4 of 5 questions." The original criterion said "retrieved chunks," but the number of chunks can change with `TOP_K`, so the measurement is easier to compare if the criterion names the retrieval depth.

I would also make criterion 3 harder by including at least one out-of-scope question that sounds like campus life but is absent from the documents. The current out-of-scope questions are very clearly unrelated, so passing them does not prove the gate can handle near misses.

## How I Used AI in Unit 2

I used Codex to inspect the repository, run the baseline and after evaluations, read the generated `results/` files, aggregate question-level evidence into criterion-level run logs, and compare before/after outcomes. Codex also helped trace the baseline retrieval outputs and choose the single top-k improvement. I reviewed the actual run logs instead of inventing results.
