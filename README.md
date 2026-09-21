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

These sections are for the later unit 2 evaluation work. I have not filled them in yet because the project still needs my own acceptance-criteria decisions in `criteria.md` before the unit 2 run log should be finalized.

## Run Log - Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

## The Improvement

**What I changed:**

**Why I picked it:**

### Run Log - After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

## What's Still Broken

## What I'd Do Differently
