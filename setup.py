from setuptools import setup, find_packages

setup(
    name="xyzs_py",  # 包名，建议与项目文件夹名称一致
    version="1.0.8",  # 版本号，遵循语义化版本控制
    author="Jed",  # 作者
    author_email="jiede2011@hotmail.com",  # 作者邮箱
    description="封装Mysql、Redis、时间操作类、yaml配置操作、Http操作、日志操作等等快速使用的代码",  # 包的简要描述
    long_description=open("README.md").read(),  # 长描述，一般从 README.md 文件中读取
    long_description_content_type="text/markdown",  # 长描述的格式，通常为 Markdown
    url="https://github.com/JedTK/xyzs_py",  # 项目的主页或 Git 仓库 URL
    packages=find_packages(),  # 自动查找项目中的所有包
    # 在这里列出依赖包及其版本
    install_requires=[
        "requests~=2.32.3",
        "colorlog~=6.8.2",
        "aiohttp~=3.10.11",
        "setuptools>=70.1.1",
        "PyYAML~=6.0.1",
        "redis~=5.0.8",
        "APScheduler~=3.10.4",
        "SQLAlchemy~=2.0.36",
        "DateTime~=5.5",
    ],
    classifiers=[  # 分类信息
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # 替换为实际许可证
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # 兼容的 Python 版本
    include_package_data=True,  # 包含包中的静态文件（如文件夹中的 *.txt 或 *.json）
    entry_points={  # 可选，定义可执行的脚本命令
        "console_scripts": [

        ]
    },
)
