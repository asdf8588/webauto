import sys
print(f"Python: {sys.version}")

packages = ['langchain', 'langchain_openai', 'langchain_community', 'openai', 'dotenv']

for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f"✅ {pkg} - 已安装")
    except ImportError:
        print(f"❌ {pkg} - 未安装")