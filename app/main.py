import logging
import os
import tempfile

import streamlit as st

from app.log import Utf8DecoderFormatter
from app.models.schema import Document, FundDocumentMetadata
from app.engine import get_chat_engine

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

handler = logging.StreamHandler()
handler.setFormatter(Utf8DecoderFormatter())
logger.handlers = []
logger.addHandler(handler)


def rule_add():
    st.session_state.rule_added = True


def audit_start():
    st.session_state.audit_start = True


def init_page():
    if 'rule_added' not in st.session_state:
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
                _rule = side_bar.text_input(f"规则{i + 1}", key=f"rule{i}", value=st.session_state[f"rule{i}"], on_change=None)
            else:
                _rule = side_bar.text_input(f"规则{i + 1}", key=f"rule{i}", on_change=None)
            print(f"New rule: {_rule}")
    st.warning("上传需审计的文档，格式为PDF")
    st.warning("文档不会持久化，下次进入时需要重新上传文件")


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
    if "engine" not in st.session_state:
        rules = get_rules()
        print(f"===============Rules:")
        print(rules, st.session_state["rule_cnt"])
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
            with st.spinner("构建索引和初始化，请耐心等待..."):
                st.session_state.engine = get_chat_engine(documents, rules)
                st.success("索引构建完毕!")


def main():
    init_page()
    # init_message_history()
    init_engine()

    if 'audit_start' not in st.session_state:
        st.session_state.audit_start = False

    button = st.button("开始", on_click=audit_start)

    if st.session_state.audit_start:
        prompt = "请给出修改意见"
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("请稍等..."):
                engine_response = st.session_state.engine.chat(prompt)
                response = str(engine_response.response)
                st.write(response)
                for source_node in engine_response.source_nodes:
                    node_id = source_node.node.node_id or "None"
                    file_name = source_node.node.metadata["file_name"] or "None"
                    page_label = source_node.node.metadata["page_label"] or "None"

                    shortened_text = f'来源：《{file_name[:25]} ...》"第{page_label}页'
                    with st.expander(shortened_text):
                        st.caption(f"Node id: {node_id}")
                        st.caption(f"File: {file_name}")
                        st.caption(f"Score: {source_node.score}")
                        st.caption(f"Content: {source_node.node.get_content()}")


if __name__ == "__main__":
    main()
