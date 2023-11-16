from typing import List

from llama_index import PromptTemplate
from llama_index.indices.service_context import ServiceContext
from llama_index.prompts.prompt_type import PromptType
from llama_index.prompts.prompts import QuestionAnswerPrompt, RefinePrompt
from llama_index.response_synthesizers import BaseSynthesizer
from llama_index.response_synthesizers.factory import get_response_synthesizer

from .utils import build_title_for_document
from .models.schema import Document as DocumentSchema


def get_context_prompt_template(documents: List[DocumentSchema]):
    doc_titles = "\n".join("- " + build_title_for_document(doc) for doc in documents)
    return PromptTemplate(
        "用户选择了一组文档，并询问了有关这些文件的问题。这些文件的标题如下: \n"
        f"{doc_titles}"
        "以下是上下文信息。\n"
        "---------------------\n"
        "{context_str}"
        "\n---------------------\n"
    )


def get_sys_prompt(msgs: List[str]):
    content = ""
    for i, msg in enumerate(msgs):
        content += f"{i+1}. {msg}\n"
    print(content)
    return f"""
你现在是一个审查员，根据以下规则对文本提出修改意见：
{content}
以下是一些你必须遵循的准则:

- 你只扮演审查员的角色，不要模拟其他问题。
- 你给出的修改意见必须与上述规则相关。
- 你最多只能给出5条修改意见。
- 如果修改后的文本与原文本相同，则不要给出该修改意见。
- 你必须总是用中文给出修改意见。

"""
