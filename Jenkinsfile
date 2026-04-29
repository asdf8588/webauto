pipeline {
    agent any
    
    environment {
        // Python 环境
        PYTHON_VERSION = '3.11'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '>>> 拉取代码'
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                echo '>>> 设置 Python 环境'
                bat '''
                    python --version
                    pip --version
                '''
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo '>>> 安装依赖'
                bat '''
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Install Playwright Browsers') {
            steps {
                echo '>>> 安装 Playwright 浏览器'
                bat '''
                    playwright install chromium
                '''
            }
        }
        
        stage('Run API Tests') {
            steps {
                echo '>>> 运行 API 测试'
                bat '''
                    pytest tests/api/ -v --tb=short -o addopts=
                '''
            }
        }
        
        stage('Run UI Tests') {
            steps {
                echo '>>> 运行 UI 测试'
                bat '''
                    pytest tests/ui/ -v --tb=short -o addopts= -m "not requires_browser"
                '''
            }
        }
        
        stage('Generate Report') {
            steps {
                echo '>>> 生成测试报告'
                bat '''
                    if exist allure-results (
                        echo Allure results found
                    ) else (
                        echo No allure results
                    )
                '''
            }
        }
    }
    
    post {
        always {
            echo '>>> 清理工作空间'
            // 保留测试结果
            archiveArtifacts artifacts: 'allure-results/**/*', allowEmptyArchive: true
            junit 'allure-results/*.xml', allowEmptyResults: true
        }
        success {
            echo '>>> 测试全部通过！'
        }
        failure {
            echo '>>> 测试失败，请检查日志'
        }
    }
}
