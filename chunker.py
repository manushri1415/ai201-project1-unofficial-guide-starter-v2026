"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents into chunks. ⚠️ REPLACE THE BODY OF THIS IN MILESTONE 3.

    The selected campus_life corpus is made of short student posts. Each file
    is already one coherent answer, and useful facts usually live in one
    sentence or paragraph inside that post.

    Short posts stay whole. Longer documents are packed by paragraph, with a
    sentence-aware fallback for unusually long paragraphs.
    """
    chunk_size = config.CHUNK_SIZE
    produced_by = "chunker.py::split_documents"

    chunks: list[Chunk] = []
    for doc in documents:
        index = 0
        for text in _post_or_paragraph_chunks(doc.text, chunk_size):
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by=produced_by,
                )
            )
            index += 1

    return chunks


def _post_or_paragraph_chunks(text: str, chunk_size: int) -> list[str]:
    """Keep short posts whole; pack longer posts by paragraph."""
    if len(text) <= chunk_size:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        extra = len(paragraph) + (2 if current else 0)
        if current and current_len + extra > chunk_size:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0

        if len(paragraph) > chunk_size:
            chunks.extend(_sentence_chunks(paragraph, chunk_size))
            continue

        current.append(paragraph)
        current_len += extra

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _sentence_chunks(text: str, chunk_size: int) -> list[str]:
    """Fallback for an unusually long paragraph without cutting sentences."""
    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text)
        if s.strip()
    ]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        extra = len(sentence) + (1 if current else 0)
        if current and current_len + extra > chunk_size:
            chunks.append(" ".join(current))
            current = []
            current_len = 0

        if len(sentence) > chunk_size:
            chunks.extend(_hard_wrap(sentence, chunk_size))
            continue

        current.append(sentence)
        current_len += extra

    if current:
        chunks.append(" ".join(current))

    return chunks


def _hard_wrap(text: str, chunk_size: int) -> list[str]:
    """Last-resort wrapping for text with no usable natural breaks."""
    return [
        text[start : start + chunk_size].strip()
        for start in range(0, len(text), chunk_size)
        if text[start : start + chunk_size].strip()
    ]


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
