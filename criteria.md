# Acceptance criteria - The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
before any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. "Retrieval works" is an opinion. "For at least
4 of my 5 test questions, the top results include a chunk containing the
answer" is a criterion.

Under each one, I wrote why I chose that target and not a stricter or looser
one.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
I chose 4 out of 5 because retrieval does not have to be perfect every time,
but I still expect the system to find the correct information for most of my
test questions.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
I chose all 5 because every answer should show where its information came
from. Since the purpose of this project is to give grounded answers from the
documents, an answer without a source would be hard to verify.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that"
in at least 4 of 5 tries.

**Why this target:**
I chose 4 out of 5 because the relevance gate should reject most clearly
unrelated questions, while allowing for one possible mistake because semantic
similarity is not always perfect.

---

## 4. Chunks do not cut off sentences

All 5 of 5 sampled chunks begin and end cleanly, with no sentence cut in half
at either edge.

**Why this target:**
I chose 5 out of 5 because cutting a sentence in half can remove important
context and make a chunk harder to understand on its own. I want every sampled
chunk to contain complete sentences.

---

## 5. Answers include the expected phrase

For at least 4 of my 5 test questions, the generated answer contains the
question's `expects` phrase from `questions.py`, ignoring capitalization.

**Why this target:**
I chose 4 out of 5 because I expect most correct answers to include the key
fact I identified in the `expects` field, but the model may occasionally
express the same idea using slightly different wording.

---

## Unit 2 note

If a criterion turns out to be broken rather than merely unmet, I can revise it
in unit 2 by adding the revision underneath the original criterion and leaving
the original visible. Lowering a target just because I missed it is not a valid
revision; the missed target should be diagnosed and improved against.
