XYZS_PY 库引用与卸载教程


一、在其他项目中引用方式：

1. 固定分支引用（适合开发阶段）

命令如下：
	pip install git+https://github.com/JedTK/xyzs_py.git@main

说明：
每次你修改并 git push 后，只需在其他项目中运行以下命令即可更新为最新版本：

	pip install --upgrade --force-reinstall git+https://github.com/JedTK/xyzs_py.git@main

适合正在频繁开发优化中的阶段。


2. 指定 tag 安装（适合稳定发布）

首先在本地打 tag 并推送：
	git tag v1.0.1  
	git push origin v1.0.1

然后在其他项目中使用以下命令安装指定版本：
pip install git+https://github.com/JedTK/xyzs_py.git@v1.0.1

二、requirements.txt 中的配置示例：

1. 固定分支引用方式：

	git+https://github.com/JedTK/xyzs_py.git@main#egg=xyzs_py

2. 指定 tag 的引用方式：

	git+https://github.com/JedTK/xyzs_py.git@v1.0.1#egg=xyzs_py

然后运行：
	pip install -r requirements.txt

三、卸载 XYZS_PY 库的方法：
	pip uninstall xyzs_py

