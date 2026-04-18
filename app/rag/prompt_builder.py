from app.rag.hybrid_retriever import RetrievedChunk


SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions \
based on the user's documents. 

Rules:
- Only use information from the provided context to answer
- If the context doesn't contain enough information, say so clearly
- Always be accurate and cite which part of the context you used
- Be concise but complete in your answers"""


def build_prompt(
    query: str,
    chunks: list[RetrievedChunk],
    memory_summary: str | None = None,
    recent_messages: list[dict] | None = None,
) -> tuple[str, str]:
    """
    Builds the final prompt sent to the LLM.
    Returns (system_prompt, user_prompt) tuple.
    """
    # build context block from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("original_name", "document")
        page = chunk.metadata.get("page_number", "")
        page_info = f" (page {page})" if page else ""
        context_parts.append(
            f"[Source {i}: {source}{page_info}]\n{chunk.content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # build memory section
    memory_section = ""
    if memory_summary:
        memory_section = f"\n\nConversation summary so far:\n{memory_summary}"

    # build recent messages section
    history_section = ""
    if recent_messages:
        history_lines = []
        for msg in recent_messages[-6:]:  # last 3 exchanges
            role = "User" if msg["role"] == "user" else "Assistant"
            history_lines.append(f"{role}: {msg['content']}")
        history_section = "\n\nRecent conversation:\n" + "\n".join(history_lines)

    user_prompt = f"""Context from your documents:

{context}
{memory_section}
{history_section}

Question: {query}

Answer based on the context above:"""

    return SYSTEM_PROMPT, user_prompt