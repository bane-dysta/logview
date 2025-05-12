from setuptools import setup, find_packages

# 读取README.md作为长描述
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="logview",
    version="0.1.0",
    author="LogView开发团队",
    author_email="logview@example.com",
    description="基于VIM风格的通用日志查看器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/logview",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "windows-curses;platform_system=='Windows'",
    ],
    entry_points={
        "console_scripts": [
            "logview=logview.cli:main",
        ],
    },
) 