"""
LangChain 集成助手 - 用于 AI 辅助测试
依赖：pip install langchain langchain-openai langchain-community

用法：
1. 设置环境变量：$env:OPENAI_API_KEY="sk-xxx"
2. from utils.langchain_helper import AITestAssistant
"""
import os
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


class AITestAssistant:
    """AI 测试助手 - 使用 LangChain 辅助测试生成和分析"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        初始化 AI 测试助手
        
        Args:
            api_key: OpenAI API Key（默认从环境变量读取）
            model: 使用的模型（默认 gpt-4o-mini，便宜又快）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("需要设置 OPENAI_API_KEY 环境变量")
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=self.api_key,
            temperature=0.7
        )

    def generate_test_cases(self, feature_description: str, field_definitions: Dict[str, str]) -> List[Dict]:
        """
        根据功能描述和字段定义生成测试用例

        Args:
            feature_description: 功能描述，如"用户注册接口"
            field_definitions: 字段定义，如 {"username": "必填，2-20字符", "email": "必填，邮箱格式"}
        
        Returns:
            List[Dict]: 生成的测试用例列表
        
        Example:
            >>> assistant = AITestAssistant()
            >>> cases = assistant.generate_test_cases(
            ...     "用户登录接口",
            ...     {"email": "必填，邮箱格式", "password": "必填，6位以上"}
            ... )
            >>> print(cases)
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的 QA 工程师，负责生成测试用例。
请根据提供的信息生成全面的测试用例，包括：
1. 正向场景（全部有效数据）
2. 边界值测试
3. 异常场景（必填字段、空值、格式错误等）
4. 安全测试（SQL注入、XSS等）

输出格式为 JSON 数组，每个用例包含：name, description, priority, request_data, expected_status"""),
            ("human", "功能：{feature}\n\n字段定义：\n{fields}")
        ])

        fields_str = "\n".join([f"- {k}: {v}" for k, v in field_definitions.items()])

        chain = prompt | self.llm | JsonOutputParser()

        result = chain.invoke({
            "feature": feature_description,
            "fields": fields_str
        })

        return result

    def analyze_test_results(self, test_log: str) -> Dict[str, Any]:
        """
        分析测试日志，生成问题诊断和改进建议

        Args:
            test_log: 测试日志内容
        
        Returns:
            Dict: 分析结果，包含 failures, performance_issues, risks, suggestions
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个测试专家，负责分析测试结果并提供诊断。
请分析提供的测试日志，识别：
1. 失败的测试用例及原因
2. 性能问题
3. 潜在的风险点
4. 改进建议

输出 JSON 格式，包含：failures, performance_issues, risks, suggestions"""),
            ("human", "测试日志：\n{log}")
        ])

        chain = prompt | self.llm | JsonOutputParser()
        return chain.invoke({"log": test_log})

    def generate_page_locator(self, page_description: str, elements: List[str]) -> Dict[str, str]:
        """
        根据页面描述生成 Playwright 无障碍树定位器建议

        Args:
            page_description: 页面功能描述
            elements: 需要定位的元素列表
        
        Returns:
            Dict[str, str]: 元素名 -> 推荐定位器
        
        Example:
            >>> locators = assistant.generate_page_locator(
            ...     "登录页面，包含用户名、密码输入框和登录按钮",
            ...     ["用户名输入框", "密码输入框", "登录按钮"]
            ... )
            >>> print(locators)
            {'用户名输入框': 'page.get_by_label("用户名")', ...}
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个 Playwright 自动化测试专家。
根据页面描述，为每个元素推荐最佳的无障碍树定位方式。
优先级：get_by_role > get_by_label > get_by_placeholder > 其他

输出 JSON 格式：{element_name: locator_suggestion}"""),
            ("human", "页面：{page}\n\n需要定位的元素：\n{elements}")
        ])

        chain = prompt | self.llm | JsonOutputParser()

        return chain.invoke({
            "page": page_description,
            "elements": "\n".join([f"- {e}" for e in elements])
        })

    def generate_assertions(self, api_response_sample: str, context: str) -> str:
        """
        根据 API 响应示例生成断言建议

        Args:
            api_response_sample: API 响应示例（JSON 格式）
            context: API 的业务背景
        
        Returns:
            str: pytest 断言代码建议
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个 QA 专家，负责生成测试断言。"),
            ("human", "请为以下 API 响应生成 pytest 断言：\n\n业务背景：{context}\n\n响应示例：\n{sample}")
        ])

        chain = prompt | self.llm
        result = chain.invoke({"context": context, "sample": api_response_sample})

        return result.content


def demo():
    """演示用法 - 需要设置 OPENAI_API_KEY"""
    if not os.getenv("OPENAI_API_KEY"):
        print("请先设置环境变量：")
        print('  $env:OPENAI_API_KEY = "sk-xxx"')
        return
    
    assistant = AITestAssistant()
    
    print("\n=== 示例1：生成测试用例 ===")
    test_cases = assistant.generate_test_cases(
        feature_description="用户注册接口",
        field_definitions={
            "username": "必填，2-20字符",
            "email": "必填，邮箱格式",
            "password": "必填，6-20字符"
        }
    )
    print("生成的测试用例：", test_cases)

    print("\n=== 示例2：生成定位器 ===")
    locators = assistant.generate_page_locator(
        page_description="用户登录页面，包含用户名输入框、密码输入框和登录按钮",
        elements=["用户名输入框", "密码输入框", "登录按钮"]
    )
    print("推荐的定位器：", locators)


if __name__ == "__main__":
    demo()
