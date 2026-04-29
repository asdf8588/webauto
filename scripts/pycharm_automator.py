"""
PyCharm 自动化工具 - 自动安装依赖并控制 PyCharm
"""
import subprocess
import os
import sys


class PyCharmAutomator:
    """PyCharm 自动化控制器"""

    def __init__(self, pycharm_path=None):
        # 自动检测 PyCharm 路径
        self.pycharm_path = pycharm_path or self._detect_pycharm_path()
        self.python_executable = sys.executable

    def _detect_pycharm_path(self):
        """自动检测 PyCharm 安装路径"""
        common_paths = [
            r"C:\Program Files\JetBrains\PyCharm Community Edition 2024.1.3\bin\pycharm64.exe",
            r"C:\Program Files\JetBrains\PyCharm Professional 2024.1.3\bin\pycharm64.exe",
            r"C:\Program Files (x86)\JetBrains\PyCharm Community Edition 2024.1.3\bin\pycharm64.exe",
            r"C:\Users\%USERNAME%\AppData\Local\JetBrains\Toolbox\apps\PyCharm-C\ch-0\241.15989.155\bin\pycharm64.exe",
        ]
        
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
        
        print("警告：未自动检测到 PyCharm 路径，请手动指定")
        return None

    def install_package(self, package_name):
        """通过当前解释器安装 Python 包"""
        print(f"正在安装 {package_name}...")
        
        result = subprocess.run(
            [self.python_executable, "-m", "pip", "install", package_name, "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print(f"✅ {package_name} 安装成功")
            return True
        else:
            print(f"❌ {package_name} 安装失败")
            print(f"错误信息: {result.stderr}")
            return False

    def install_langchain(self):
        """安装 LangChain 及相关依赖"""
        packages = [
            "langchain",
            "langchain-openai", 
            "langchain-community",
            "python-dotenv"
        ]
        
        print("===== 开始安装 LangChain 依赖 =====")
        success_count = 0
        
        for package in packages:
            if self.install_package(package):
                success_count += 1
        
        print(f"\n===== 安装完成：{success_count}/{len(packages)} =====")
        return success_count == len(packages)

    def open_file(self, file_path, line_number=None):
        """在 PyCharm 中打开文件"""
        if not self.pycharm_path:
            print("错误：未指定 PyCharm 路径")
            return False
        
        if not os.path.exists(file_path):
            print(f"错误：文件不存在: {file_path}")
            return False
        
        args = [self.pycharm_path, file_path]
        
        if line_number:
            args.insert(1, f"--line")
            args.insert(2, str(line_number))
        
        print(f"正在打开文件: {file_path}")
        subprocess.Popen(args, shell=True)
        return True

    def open_project(self, project_path):
        """在 PyCharm 中打开项目"""
        if not self.pycharm_path:
            print("错误：未指定 PyCharm 路径")
            return False
        
        if not os.path.exists(project_path):
            print(f"错误：项目路径不存在: {project_path}")
            return False
        
        print(f"正在打开项目: {project_path}")
        subprocess.Popen([self.pycharm_path, project_path], shell=True)
        return True

    def install_and_open(self, package_name, file_path=None):
        """安装包并打开文件"""
        if self.install_package(package_name):
            if file_path:
                self.open_file(file_path)
            return True
        return False


if __name__ == "__main__":
    automator = PyCharmAutomator()
    
    print(f"当前 Python 解释器: {automator.python_executable}")
    print(f"检测到的 PyCharm 路径: {automator.pycharm_path}")
    
    print("\n===== 自动化任务 =====")
    
    # 安装 LangChain
    if automator.install_langchain():
        print("\n✅ LangChain 安装成功！")
        
        # 打开相关文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        langchain_helper = os.path.join(project_root, "utils", "langchain_helper.py")
        
        if os.path.exists(langchain_helper):
            automator.open_file(langchain_helper, line_number=1)
            print(f"已在 PyCharm 中打开: {langchain_helper}")
    else:
        print("\n❌ LangChain 安装失败，请检查错误信息")