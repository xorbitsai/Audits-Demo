import logging
import os
import tempfile

import streamlit as st
from llama_index.llms import ChatMessage

from app.log import Utf8DecoderFormatter
from app.models.schema import Document, FundDocumentMetadata
from app.engine import get_chat_engine
from app.prompts import get_sys_prompt
from app.utils import get_doc_contents

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

handler = logging.StreamHandler()
handler.setFormatter(Utf8DecoderFormatter())
logger.handlers = []
logger.addHandler(handler)


def rule_add():
    st.session_state.rule_added = True


def text_start():
    st.session_state.text_start = True


def file_start():
    st.session_state.file_start = True


def init_page():
    if "rule_added" not in st.session_state:
        st.session_state.rule_added = False
    if "rule_cnt" not in st.session_state:
        st.session_state["rule_cnt"] = 0
    st.set_page_config(page_title="审计助手", page_icon="🤗")
    st.header("审计助手")
    side_bar = st.sidebar
    button = side_bar.button("新增一条规则", on_click=rule_add)
    if button:
        st.session_state["rule_cnt"] += 1
    if st.session_state.rule_added:
        cnt = st.session_state["rule_cnt"]
        for i in range(cnt):
            if f"rule{i}" in st.session_state:
                _rule = side_bar.text_input(
                    f"规则{i + 1}",
                    key=f"rule{i}",
                    value=st.session_state[f"rule{i}"],
                    on_change=None,
                )
            else:
                _rule = side_bar.text_input(
                    f"规则{i + 1}", key=f"rule{i}", on_change=None
                )


def handle_uploaded_file():
    placeholder = st.empty()
    uploaded_files = placeholder.file_uploader(
        "提供相关的文档（可以是多个PDF文档）", type=["pdf"], accept_multiple_files=True
    )
    if len(uploaded_files) > 0:
        placeholder.empty()
        st.success("文件上传成功!")
        return uploaded_files
    else:
        st.stop()


def get_rules():
    rules_cnt = st.session_state["rule_cnt"]
    res = []
    for i in range(rules_cnt):
        res.append(st.session_state.get(f"rule{i}", ""))
    return res


def init_engine():
    if "text_start" not in st.session_state:
        st.session_state.text_start = False
    if "file_start" not in st.session_state:
        st.session_state.file_start = False
    if "engine" not in st.session_state:
        st.session_state.engine = get_chat_engine()
    text, file = st.tabs(["文本输入", "文件上传"])
    with text:
        st.text_area(label="待审计的文本", key="text")
        st.button("开始", key='text_button', on_click=text_start)

        if st.session_state.text_start:
            rules = get_rules()
            messages = [
                ChatMessage(role="system", content=f"{get_sys_prompt(rules)}"),
                ChatMessage(
                    role="user",
                    content=f"请针对以下文本给出修改意见: \n{st.session_state.text}",
                ),
            ]
            with st.chat_message("assistant"):
                with st.spinner("请稍等..."):
                    engine_response = st.session_state.engine.chat(messages)
                    st.write(engine_response)

    with file:
        st.warning("上传需审计的文档，格式为PDF")
        st.warning("文档不会持久化，下次进入时需要重新上传文件")
        if uploaded_files := handle_uploaded_file():
            documents = []
            for uploaded_file in uploaded_files:
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                documents.append(
                    Document(
                        url=file_path,
                        metadata=FundDocumentMetadata(
                            document_description=uploaded_file.name
                        ),
                    )
                )

                logger.info(
                    f"File {uploaded_file.name} has been written to {file_path}"
                )
            with st.spinner("读取文档，请耐心等待..."):
                st.session_state.documents = documents
                st.success("文档读取完毕!")
            st.button("开始", key='file_button', on_click=file_start)

            if st.session_state.file_start:
                rules = get_rules()
                messages = [
                    ChatMessage(role="system", content=f"{get_sys_prompt(rules)}"),
                    ChatMessage(
                        role="user",
                        content=f"请针对以下文本给出修改意见: \n{get_doc_contents(st.session_state.documents)}",
                    ),
                ]
                with st.chat_message("assistant"):
                    with st.spinner("请稍等..."):
                        engine_response = st.session_state.engine.chat(messages)
                        st.write(engine_response)


def main():
    init_page()
    init_engine()


if __name__ == "__main__":
    main()
