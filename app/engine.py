import logging
import os
from typing import List

import tiktoken
from langchain.embeddings import XinferenceEmbeddings
from langchain.llms import Xinference
from llama_index.chat_engine import CondenseQuestionChatEngine
from llama_index.llms import OpenAI
from llama_index import ServiceContext, VectorStoreIndex
from llama_index.callbacks import LlamaDebugHandler
from llama_index.callbacks.base import CallbackManager
from llama_index.chat_engine.types import BaseChatEngine, ChatMode
from llama_index.embeddings import LangchainEmbedding
from llama_index.embeddings.openai import (
    OpenAIEmbedding,
    OpenAIEmbeddingMode,
    OpenAIEmbeddingModelType,
)
from llama_index.memory import ChatMemoryBuffer
from llama_index.node_parser import SimpleNodeParser
from llama_index.text_splitter import SentenceSplitter

from .models.schema import Document as DocumentSchema
from .utils import fetch_and_read_documents
from .constants import NODE_PARSER_CHUNK_SIZE, NODE_PARSER_CHUNK_OVERLAP
from .prompts import get_context_prompt_template, get_sys_prompt


logger = logging.getLogger(__name__)


def get_llm():
    llm = OpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo-0613",
        streaming=False,
        api_key="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",
    )

    return llm


def get_embedding_model():
    embedding = OpenAIEmbedding(
        mode=OpenAIEmbeddingMode.SIMILARITY_MODE,
        model_type=OpenAIEmbeddingModelType.TEXT_EMBED_ADA_002,
        api_key="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",
    )

    return embedding


def get_service_context(callback_handlers):
    callback_manager = CallbackManager(callback_handlers)

    embedding_model = get_embedding_model()
    llm = get_llm()

    text_splitter = SentenceSplitter(
        separator=" ",
        chunk_size=NODE_PARSER_CHUNK_SIZE,
        chunk_overlap=NODE_PARSER_CHUNK_OVERLAP,
        paragraph_separator="\n\n\n",
        secondary_chunking_regex="[^,.;。]+[,.;。]?",
        tokenizer=tiktoken.encoding_for_model("gpt-3.5-turbo").encode,
    )

    node_parser = SimpleNodeParser.from_defaults(
        text_splitter=text_splitter,
        callback_manager=callback_manager,
    )

    return ServiceContext.from_defaults(
        callback_manager=callback_manager,
        llm=llm,
        embed_model=embedding_model,
        node_parser=node_parser,
    )


def get_chat_engine(documents: List[DocumentSchema], rules: List[str]) -> BaseChatEngine:
    """Custom a query engine for qa, retrieve all documents in one index."""
    llama_debug = LlamaDebugHandler(print_trace_on_end=True)

    service_context = get_service_context([llama_debug])

    llama_index_docs = fetch_and_read_documents(documents)
    logger.debug(llama_index_docs)
    index = VectorStoreIndex.from_documents(
        llama_index_docs,
        service_context=service_context,
    )

    # memory = ChatMemoryBuffer.from_defaults(
    #     token_limit=get_llm_max_tokens() * get_history_count()
    # )

    # CondenseQuestionChatEngine.from_defaults(
    #     query_engine=index.as_query_engine()
    # )

    chat_engine = index.as_chat_engine(
        chat_mode=ChatMode.CONTEXT,
        # memory=memory,
        context_template=get_context_prompt_template(documents),
        system_prompt=get_sys_prompt(rules),
    )
    return chat_engine
