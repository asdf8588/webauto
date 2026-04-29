"""
LangChain Agent 示例 - 智能测试执行助手
依赖：pip install langchain langchain-openai langchain-community

用法示例：
1. 设置环境变量：$env:OPENAI_API_KEY="sk-xxx"
2. 运行：python tests/test_langchain_agent.py
"""
import pytest
import os
from typing import Dict, Any

# LangChain 核心
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain.agents import AgentExecutor, create_tool_calling_agent


def get_llm():
    """获取 LLM 实例"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请先设置 OPENAI_API_KEY 环境变量")
    
    return ChatOpenAI(
        model="gpt-4o-mini",  # 用便宜的模型
        api_key=api_key,
        temperature=0
    )


class PlaywrightTestRunner:
    """Playwright 测试执行器"""

    @staticmethod
    def run_ui_test(test_name: str) -> Dict[str, Any]:
        """执行 UI 测试"""
        import subprocess
        result = subprocess.run(
            ["pytest", f"tests/ui/{test_name}.py", "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    @staticmethod
    def run_api_test(endpoint: str) -> Dict[str, Any]:
        """执行 API 测试"""
        import subprocess
        result = subprocess.run(
            ["pytest", f"tests/api/test_{endpoint}.py", "-v"],
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout
        }


# 定义工具
def run_login_test() -> str:
    """执行登录页面 UI 测试
    
    Returns:
        str: 测试执行结果
    """
    runner = PlaywrightTestRunner()
    result = runner.run_ui_test("test_login")
    return f"登录测试{'成功' if result['success'] else '失败'}"


def run_api_test_endpoint(endpoint: str) -> str:
    """执行指定端点的 API 测试

    Args:
        endpoint: API 端点名称，如 'user', 'auth' 等
    
    Returns:
        str: 测试执行结果
    """
    runner = PlaywrightTestRunner()
    result = runner.run_api_test(endpoint)
    return f"API 测试{'成功' if result['success'] else '失败'}"


def get_test_report() -> str:
    """获取最新的测试报告摘要
    
    Returns:
        str: 测试报告内容
    """
    try:
        with open("allure-report/widgets/summary.json", "r") as f:
            import json
            data = json.load(f)
            return f"测试统计：{data}"
    except FileNotFoundError:
        return "报告文件不存在，请先运行测试"


def create_test_agent():
    """创建测试助手 Agent"""
    llm = get_llm()
    
    # 工具列表
    tools = [run_login_test, run_api_test_endpoint, get_test_report]
    
    # 构建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个测试助手，可以执行以下操作：
1. 运行登录页面的 UI 测试（使用 run_login_test）
2. 运行指定 API 端点的测试（使用 run_api_test_endpoint）
3. 获取测试报告（使用 get_test_report）

根据用户需求，选择合适的工具执行。当用户说"测一下登录"就用 run_login_test，
说"测 API"就用 run_api_test_endpoint。"""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 创建 Agent（LangChain 0.3.x 语法）
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor


class TestLangChainAgent:
    """LangChain Agent 测试示例"""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="需要设置 OPENAI_API_KEY 环境变量"
    )
    def test_agent_execute_login(self):
        """测试 Agent 执行登录测试"""
        agent = create_test_agent()
        
        result = agent.invoke({
            "input": "请执行登录页面的 UI 测试"
        })
        
        print(f"Agent 执行结果：{result}")

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="需要设置 OPENAI_API_KEY"
    )
    def test_agent_query_report(self):
        """测试 Agent 查询报告"""
        agent = create_test_agent()
        
        result = agent.invoke({
            "input": "获取最新的测试报告"
        })
        
        print(f"报告结果：{result}")


if __name__ == "__main__":
    print("=" * 60)
    print("LangChain Agent 测试助手")
    print("=" * 60)
    print()
    
    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("请先设置环境变量：")
        print('  Windows: $env:OPENAI_API_KEY="sk-xxx"')
        print('  Linux/Mac: export OPENAI_API_KEY="sk-xxx"')
        print()
        print("或者直接在代码中设置：")
        print('  import os')
        print('  os.environ["OPENAI_API_KEY"] = "sk-xxx"')
    else:
        print("API Key 已设置，开始测试...")
        print()
        
        agent = create_test_agent()
        
        # 简单对话测试
        user_input = input("请输入你要执行的测试（输入 q 退出）: ")
        if user_input.lower() != 'q':
            result = agent.invoke({"input": user_input})
            print("\n执行结果:")
            print(result.get("output", "无输出"))
