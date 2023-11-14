from pathlib import Path
from typing import List

from llama_index.readers.file.docs_reader import PDFReader
from llama_index.schema import Document as LLamaIndexDocument

from .models.schema import Document as DocumentSchema
from .constants import DOC_ID_KEY


def fetch_and_read_documents(
    documents: List[DocumentSchema],
) -> List[LLamaIndexDocument]:
    loaded_documents = []
    for doc in documents:
        reader = PDFReader()
        loaded = reader.load_data(Path(doc.url), extra_info={DOC_ID_KEY: str(doc.id)})
        loaded_documents.extend(loaded)
    return loaded_documents


def build_title_for_document(document: DocumentSchema) -> str:
    if document.metadata is not None:
        return f"{document.metadata.document_description}"
    return "没有标题"
