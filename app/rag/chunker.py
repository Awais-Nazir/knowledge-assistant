import re


def semantic_chunk(
    text: str,
    max_chunk_size: int = 512,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into semantically meaningful chunks.

    Strategy:
    1. Split on paragraph boundaries first (strongest signal)
    2. If a paragraph is too long, split on sentence boundaries
    3. Apply overlap between chunks to preserve context across boundaries
    """
    # normalise whitespace
    text = re.sub(r"\n{3,}", "\n\n", text.strip())

    # split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # if adding this paragraph keeps us under the limit — add it
        if len(current_chunk) + len(paragraph) < max_chunk_size:
            current_chunk += (" " if current_chunk else "") + paragraph
        else:
            # save current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk.strip())

            # if the paragraph itself is too long — split by sentences
            if len(paragraph) > max_chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                sentence_chunk = ""
                for sentence in sentences:
                    if len(sentence_chunk) + len(sentence) < max_chunk_size:
                        sentence_chunk += (" " if sentence_chunk else "") + sentence
                    else:
                        if sentence_chunk:
                            chunks.append(sentence_chunk.strip())
                        sentence_chunk = sentence
                if sentence_chunk:
                    current_chunk = sentence_chunk
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    # apply overlap — prepend tail of previous chunk to next chunk
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap:]
            overlapped.append(tail + " " + chunks[i])
        return overlapped

    return chunks


def extract_text_from_file(content: bytes, mime_type: str) -> str:
    """Extract raw text from uploaded file bytes."""
    if mime_type == "text/plain":
        return content.decode("utf-8", errors="ignore")

    elif mime_type == "application/pdf":
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    elif "wordprocessingml" in mime_type:
        import io

        from docx import Document

        doc = Document(io.BytesIO(content))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return ""
