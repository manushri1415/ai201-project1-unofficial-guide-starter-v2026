#!/usr/bin/env python3
"""
Run your test questions repeatedly and write the results down.

    python run_eval.py                 three runs, the default
    python run_eval.py --runs 5        more runs
    python run_eval.py --label after   name this run, e.g. before/after a fix

This does the mechanical half of unit 2 for you: it asks each of your questions
the same way three separate times, with caching turned off so you get three
real answers, and writes everything into results/ as a table with one row per
question.

It also puts every question in `OUT_OF_SCOPE` through retrieval and the gate
and records what happened, so criterion 3 — the one about out-of-corpus
questions — has evidence in the same file as the other four. That part costs
nothing: a question the gate refuses never reaches the model.

That table is the raw material for your run log, not the run log itself. The
submission template wants one row per *criterion* — aggregating your questions
up into your criteria is your work, not the script's.

⚠️ What it does NOT do is decide whether an answer was right.

That judgment is yours, and you'll build it in class in unit 2 as `scorer.py`.
Until that file exists, the Run columns carry the raw answers and you read them
yourself. Once it exists — a file called `scorer.py`, with a function
`judge(question, expects, answer, results) -> bool` — this script finds it
automatically and the Run columns carry verdicts instead.

Deciding what counts as correct is the actual lesson. It would be easy to hand
you a scorer; you'd learn nothing from it.
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import config
import questions as qs


def load_scorer():
    """Use scorer.py if the student has built it. Otherwise run unscored."""
    try:
        import scorer  # noqa: PLC0415
    except ImportError:
        return None
    judge = getattr(scorer, "judge", None)
    return judge if callable(judge) else None


def run_once(question: str, top_k, threshold, corpus, variant):
    """One question, one run. Returns the answer and what retrieval gave us."""
    from store import search
    import gate
    from generate import answer_from_chunks

    results = search(question, top_k=top_k, corpus=corpus, variant=variant)
    decision = gate.check(results, threshold=threshold)

    if not decision.passed:
        return gate.REFUSAL, results, decision

    # cache=False on purpose. Three runs have to be three real answers.
    answer = answer_from_chunks(question, results, cache=False)
    return answer, results, decision


def check_retrieved_contains_answer(expects: str, results) -> bool:
    """Criterion 1: at least one retrieved chunk contains the expected fact."""
    if not expects:
        return False
    needle = expects.strip().lower()
    return any(needle in (r.text or "").lower() for r in results)


def check_answer_names_source(answer: str, results) -> bool:
    """Criterion 2: the answer names one of the retrieved source files."""
    answer = answer or ""
    return any(r.source in answer for r in results)


def clean_chunk_boundary(text: str) -> bool:
    """Heuristic for criterion 4: chunks should look sentence/heading aligned."""
    text = (text or "").strip()
    if not text:
        return False

    first = text[0]
    starts_cleanly = (
        first.isupper()
        or first.isdigit()
        or first in "#`\"'"
    )
    ends_cleanly = bool(re.search(r'[.!?")\]`]\s*$', text))
    return starts_cleanly and ends_cleanly


def check_chunk_boundaries(corpus: str) -> dict:
    """Run criterion 4 over every chunk instead of sampling by eye."""
    from chunker import split_documents
    from ingest import load_documents

    documents = load_documents(corpus)
    chunks = split_documents(documents)
    checked = [
        {
            "label": chunk.label,
            "passed": clean_chunk_boundary(chunk.text),
            "start": chunk.text.strip()[:40],
            "end": chunk.text.strip()[-40:],
        }
        for chunk in chunks
    ]
    passed = sum(item["passed"] for item in checked)
    return {
        "passed": passed,
        "total": len(checked),
        "failures": [item for item in checked if not item["passed"]],
    }


def summarize_runs(rows, gate_rows, chunk_check) -> list[dict]:
    """Aggregate question-level measurements into the five criteria."""
    run_count = len(rows[0]["runs"]) if rows else 0

    retrieved_counts = []
    source_counts = []
    expected_counts = []
    for index in range(run_count):
        retrieved_counts.append(sum(row["retrieved_runs"][index] is True for row in rows))
        source_counts.append(sum(row["source_runs"][index] is True for row in rows))
        expected_counts.append(sum(row["runs"][index] is True for row in rows))

    gate_count = sum(row["refused"] for row in gate_rows)
    chunk_count = chunk_check["passed"]
    chunk_total = chunk_check["total"]

    return [
        {
            "criterion": "1. Retrieved chunk contains the answer",
            "target": "4 of 5",
            "runs": [f"{count}/{len(rows)}" for count in retrieved_counts],
            "met": all(count >= 4 for count in retrieved_counts),
        },
        {
            "criterion": "2. Every answer names a source",
            "target": "5 of 5",
            "runs": [f"{count}/{len(rows)}" for count in source_counts],
            "met": all(count == len(rows) for count in source_counts),
        },
        {
            "criterion": "3. Gate stops out-of-corpus questions",
            "target": "4 of 5",
            "runs": [f"{gate_count}/{len(gate_rows)}"] * run_count,
            "met": gate_count >= 4,
        },
        {
            "criterion": "4. Chunks do not cut off sentences",
            "target": "all chunks",
            "runs": [f"{chunk_count}/{chunk_total}"] * run_count,
            "met": chunk_count == chunk_total,
        },
        {
            "criterion": "5. Answers include the expected phrase",
            "target": "4 of 5",
            "runs": [f"{count}/{len(rows)}" for count in expected_counts],
            "met": all(count >= 4 for count in expected_counts),
        },
    ]


def main():
    parser = argparse.ArgumentParser(description="Run the test questions and log the results.")
    parser.add_argument("--runs", type=int, default=3, help="runs per question (default 3)")
    parser.add_argument("--label", default="", help="a name for this run, e.g. 'before'")
    parser.add_argument("--corpus", default=None)
    parser.add_argument("--variant", default="default")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    corpus = args.corpus or config.CORPUS
    top_k = args.top_k or config.TOP_K
    threshold = config.THRESHOLD if args.threshold is None else args.threshold

    items = qs.answered()
    if not items:
        print(
            "questions.py has no questions in it yet.\n"
            "Milestone 2 asks you to write five. Fill them in and run this again.",
            file=sys.stderr,
        )
        sys.exit(1)

    judge = load_scorer()
    if judge is None:
        print("No scorer.py found — running unscored. Verdict column will be blank.")
        print("You'll build scorer.py in class in unit 2.\n")

    if args.runs < 3:
        print(f"⚠️  {args.runs} run(s). The submission asks for three.\n")

    transcript = []
    rows = []

    for item in items:
        question = item["question"]
        expects = item.get("expects", "")
        print(f"\n{question}")

        run_results = []
        for run in range(1, args.runs + 1):
            answer, results, decision = run_once(
                question, top_k, threshold, corpus, args.variant
            )
            passed = judge(question, expects, answer, results) if judge else None
            retrieved_has_answer = check_retrieved_contains_answer(expects, results)
            answer_names_source = check_answer_names_source(answer, results)
            run_results.append(passed)

            mark = {True: "pass", False: "fail", None: "—"}[passed]
            print(f"  run {run}: {mark}  (best distance {decision.best_distance:.3f})")

            transcript.append(
                {
                    "question": question,
                    "run": run,
                    "answer": answer,
                    "sources": sorted({r.source for r in results}),
                    "best_distance": decision.best_distance,
                    "gate_passed": decision.passed,
                    "retrieved_has_answer": retrieved_has_answer,
                    "answer_names_source": answer_names_source,
                }
            )

        rows.append(
            {
                "question": question,
                "expects": expects,
                "runs": run_results,
                "retrieved_runs": [
                    entry["retrieved_has_answer"]
                    for entry in transcript[-args.runs:]
                ],
                "source_runs": [
                    entry["answer_names_source"]
                    for entry in transcript[-args.runs:]
                ],
            }
        )

    gate_rows = check_out_of_scope(top_k, threshold, corpus, args.variant)
    chunk_check = check_chunk_boundaries(corpus)

    write_report(
        rows, transcript, gate_rows, chunk_check, args, corpus, top_k, threshold,
        scored=judge is not None,
    )


def check_out_of_scope(top_k, threshold, corpus, variant):
    """Put every OUT_OF_SCOPE question through retrieval and the gate.

    Criterion 3 in criteria.md is about questions the corpus doesn't cover, and
    it needs evidence in the run log like the other four. This costs nothing:
    a question the gate refuses never reaches the model, so there is no API
    call and no reason to run it three times — retrieval is deterministic and
    the gate is a comparison against a fixed number.
    """
    from store import search
    import gate

    questions = getattr(qs, "OUT_OF_SCOPE", [])
    if not questions:
        return []

    print("\nOut-of-scope questions (the gate should refuse these):")
    rows = []
    for question in questions:
        results = search(question, top_k=top_k, corpus=corpus, variant=variant)
        decision = gate.check(results, threshold=threshold)
        refused = not decision.passed
        print(f"  {'refused' if refused else 'LET THROUGH'}  "
              f"(best distance {decision.best_distance:.3f})  {question}")
        rows.append(
            {
                "question": question,
                "refused": refused,
                "best_distance": decision.best_distance,
            }
        )

    kept = sum(r["refused"] for r in rows)
    print(f"  -> gate refused {kept} of {len(rows)}")
    return rows


def write_report(
    rows,
    transcript,
    gate_rows,
    chunk_check,
    args,
    corpus,
    top_k,
    threshold,
    scored,
):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = len(rows[0]["runs"]) if rows else 0
    run_headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    run_divider = "|".join(["---"] * n)

    criteria_rows = summarize_runs(rows, gate_rows, chunk_check)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        f"- Produced by: `run_eval.py::main`",
        f"- Retrieval: `store.py::search`, chunks from `chunker.py::split_documents`",
        f"- Corpus: `{corpus}` (index variant `{args.variant}`)",
        f"- top-k: {top_k} · relevance cutoff: {threshold}",
        f"- Runs per question: {n}, caching off",
        f"- When: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Criteria Summary",
        "",
        f"| Criterion | Target | {run_headers} | Verdict |",
        f"|---|---|{run_divider}|---|",
    ]

    for row in criteria_rows:
        verdict = "MET" if row["met"] else "MISSED"
        lines.append(
            f"| {row['criterion']} | {row['target']} | "
            f"{' | '.join(row['runs'])} | {verdict} |"
        )

    lines += [
        "",
        "## Question-Level Scorer Output",
        "",
        "These columns use `scorer.py::judge`, which checks whether each answer",
        "contains the expected phrase for the question.",
        "",
        f"| Question | {run_headers} |",
        f"|---|{run_divider}|",
    ]

    for row in rows:
        cells = []
        for passed in row["runs"]:
            cells.append({True: "pass", False: "fail", None: " "}[passed])
        question = row["question"].replace("|", "\\|")
        lines.append(f"| {question} | {' | '.join(cells)} |")

    if not scored:
        lines += [
            "",
            "> The Run columns are blank because `scorer.py` doesn't exist yet.",
            "> Judge each question yourself by reading the output below, or build",
            "> the scorer first and re-run.",
        ]

    if gate_rows:
        refused = sum(r["refused"] for r in gate_rows)
        lines += [
            "",
            "---",
            "",
            "## The relevance gate on out-of-corpus questions",
            "",
            f"Produced by `run_eval.py::check_out_of_scope`, cutoff {threshold}. "
            f"Refused {refused} of {len(gate_rows)}.",
            "",
            "Retrieval is deterministic and the gate is a comparison against a",
            "fixed number, so these do not vary between runs — one pass over the",
            "list is the whole measurement.",
            "",
            "| Out-of-scope question | Best distance | Gate |",
            "|---|---|---|",
        ]
        for row in gate_rows:
            question = row["question"].replace("|", "\\|")
            verdict = "refused" if row["refused"] else "**let through**"
            lines.append(f"| {question} | {row['best_distance']:.3f} | {verdict} |")

    lines += [
        "",
        "---",
        "",
        "## Chunk boundary check",
        "",
        "Produced by `run_eval.py::check_chunk_boundaries` over every chunk from "
        "`chunker.py::split_documents`.",
        "",
        f"Passed {chunk_check['passed']} of {chunk_check['total']} chunks.",
    ]

    if chunk_check["failures"]:
        lines += ["", "| Chunk | Start | End |", "|---|---|---|"]
        for failure in chunk_check["failures"][:10]:
            label = failure["label"].replace("|", "\\|")
            start = failure["start"].replace("|", "\\|")
            end = failure["end"].replace("|", "\\|")
            lines.append(f"| {label} | {start} | {end} |")
        if len(chunk_check["failures"]) > 10:
            lines.append(
                f"| ... | {len(chunk_check['failures']) - 10} more failures | ... |"
            )

    lines += ["", "---", "", "## Real output", "",
              "This is what the system actually produced. Paste the relevant parts",
              "into your README underneath the table — the rubric asks for real",
              "output as text, not a description of it.", ""]

    for entry in transcript:
        lines += [
            f"### {entry['question']} — run {entry['run']}",
            "",
            f"- Best distance: {entry['best_distance']:.4f} "
            f"({'passed' if entry['gate_passed'] else 'refused by'} the gate)",
            f"- Sources retrieved: {', '.join(entry['sources']) or 'none'}",
            "",
            "```",
            entry["answer"],
            "```",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")

    import generate as gen

    print(f"\nWrote {path.relative_to(config.ROOT)}")
    print(gen.usage())
    print("\nCommit this file. It's the evidence the run actually happened.")


if __name__ == "__main__":
    main()
