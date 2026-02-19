"""
document_parser.py
Extracts plain text from various source types.
Supported: PDF, DOCX, plain text, URL (web scrape), YouTube transcript
"""
import io
from typing import Optional

import requests
from bs4 import BeautifulSoup


def parse_pdf(file_bytes: bytes) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)


def parse_docx(file_bytes: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_url(url: str, timeout: int = 15) -> str:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "NotebookLM-Clone/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove script/style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def parse_youtube(url: str) -> str:
    from youtube_transcript_api import YouTubeTranscriptApi
    # Extract video ID from URL
    import re
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if not match:
        raise ValueError(f"Cannot extract YouTube video ID from: {url}")
    video_id = match.group(1)
    entries = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join(e["text"] for e in entries)


def parse_document(source_type: str, file_bytes: Optional[bytes] = None,
                   url: Optional[str] = None) -> str:
    """
    Dispatch to the correct parser based on source_type.

    Args:
        source_type: One of "pdf", "docx", "text", "url", "youtube"
        file_bytes:  Raw file bytes (for pdf/docx/text)
        url:         URL string (for url/youtube)

    Returns:
        Extracted plain text string.
    """
    if source_type == "pdf":
        return parse_pdf(file_bytes)
    elif source_type == "docx":
        return parse_docx(file_bytes)
    elif source_type == "text":
        return file_bytes.decode("utf-8", errors="replace")
    elif source_type == "url":
        return parse_url(url)
    elif source_type == "youtube":
        return parse_youtube(url)
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")
