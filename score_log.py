#!/usr/bin/env python3
"""Score an existing run_eval.py markdown log without making model calls."""

import argparse
import re
from pathlib import Path

import config
import questions as qs
from ingest import load_documents
from run_eval import check_chunk_boundaries


RUN_HEADING = re.compile(r"^### (?P<question>.*?)\s+(?:—|â€”|-)\s+run (?P<run>\d+)\s*$")


def parse_log(path: Path) -> tuple[list[dict], list[dict]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: list[dict] = []
    gate_rows: list[dict] = []

    index = 0
    while index < len(lines):
        line = lines[index]

        if line.startswith("| What ") or line.startswith("| How ") or line.startswith("| Who "):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 3 and cells[1].replace(".", "", 1).isdigit():
                gate_rows.append(
                    {
                        "question": cells[0],
                        "best_distance": float(cells[1]),
                        "refused": cells[2].lower() == "refused",
                    }
                )

        match = RUN_HEADING.match(line)
        if not match:
            index += 1
            continue

        question = match.group("question")
        run = int(match.group("run"))
        sources: list[str] = []
        answer_lines: list[str] = []
        in_answer = False
        index += 1

        while index < len(lines) and not lines[index].startswith("### "):
            current = lines[index]
            if current.startswith("- Sources retrieved:"):
                raw_sources = current.split(":", 1)[1].strip()
                sources = [
                    source.strip()
                    for source in raw_sources.split(",")
                    if source.strip() and source.strip() != "none"
                ]
            elif current.strip() == "```":
                in_answer = not in_answer
            elif in_answer:
                answer_lines.append(current)
            index += 1

        entries.append(
            {
                "question": question,
                "run": run,
                "sources": sources,
                "answer": "\n".join(answer_lines).strip(),
            }
        )

    return entries, gate_rows


def score_entries(entries: list[dict], gate_rows: list[dict], corpus: str) -> list[dict]:
    expects_by_question = {
        item["question"]: item.get("expects", "")
        for item in qs.answered()
    }
    docs_by_source = {
        document.source: document.text
        for document in load_documents(corpus)
    }
    run_numbers = sorted({entry["run"] for entry in entries})
    chunk_check = check_chunk_boundaries(corpus)

    rows = []
    for criterion in ("retrieved", "source", "expected"):
        counts = []
        for run in run_numbers:
            passed = 0
            total = 0
            for entry in entries:
                if entry["run"] != run:
                    continue
                total += 1
                expects = expects_by_question.get(entry["question"], "").lower()
                answer = entry["answer"].lower()
                retrieved_text = "\n".join(
                    docs_by_source.get(source, "")
                    for source in entry["sources"]
                ).lower()

                if criterion == "retrieved" and expects and expects in retrieved_text:
                    passed += 1
                elif criterion == "source" and any(
                    source in entry["answer"] for source in entry["sources"]
                ):
                    passed += 1
                elif criterion == "expected" and expects and expects in answer:
                    passed += 1
            counts.append((passed, total))
        rows.append(counts)

    gate_passed = sum(row["refused"] for row in gate_rows)
    gate_total = len(gate_rows)

    return [
        {
            "criterion": "1. Retrieved chunk contains the answer",
            "target": "4 of 5",
            "runs": [f"{passed}/{total}" for passed, total in rows[0]],
            "met": all(passed >= 4 for passed, _ in rows[0]),
        },
        {
            "criterion": "2. Every answer names a source",
            "target": "5 of 5",
            "runs": [f"{passed}/{total}" for passed, total in rows[1]],
            "met": all(passed == total for passed, total in rows[1]),
        },
        {
            "criterion": "3. Gate stops out-of-corpus questions",
            "target": "4 of 5",
            "runs": [f"{gate_passed}/{gate_total}"] * len(run_numbers),
            "met": gate_passed >= 4,
        },
        {
            "criterion": "4. Chunks do not cut off sentences",
            "target": "all chunks",
            "runs": [f"{chunk_check['passed']}/{chunk_check['total']}"] * len(run_numbers),
            "met": chunk_check["passed"] == chunk_check["total"],
        },
        {
            "criterion": "5. Answers include the expected phrase",
            "target": "4 of 5",
            "runs": [f"{passed}/{total}" for passed, total in rows[2]],
            "met": all(passed >= 4 for passed, _ in rows[2]),
        },
    ]


def markdown_table(summary: list[dict]) -> str:
    run_count = len(summary[0]["runs"]) if summary else 0
    run_headers = " | ".join(f"Run {index}" for index in range(1, run_count + 1))
    run_divider = "|".join(["---"] * run_count)
    lines = [
        f"| Criterion | Target | {run_headers} | Verdict |",
        f"|---|---|{run_divider}|---|",
    ]
    for row in summary:
        verdict = "MET" if row["met"] else "MISSED"
        lines.append(
            f"| {row['criterion']} | {row['target']} | "
            f"{' | '.join(row['runs'])} | {verdict} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="path to a results/run_*.md file")
    parser.add_argument("--corpus", default=config.CORPUS)
    args = parser.parse_args()

    entries, gate_rows = parse_log(args.log)
    summary = score_entries(entries, gate_rows, args.corpus)
    print(markdown_table(summary))


if __name__ == "__main__":
    main()
