import logging

import colorlog


class XLogs:
    """一个支持彩色输出的自定义日志记录类。

    该类封装了`logging`和`colorlog`模块，提供带有颜色区分的多级别日志输出功能。
    默认配置会将所有DEBUG及以上级别的日志输出到控制台，并自动根据日志级别显示不同颜色。

    Attributes:
        logger (logging.Logger): 内部使用的日志记录器实例
        TAG (str): 日志记录器的名称标识，默认为模块名(__name__)

    Example:
        log = XLogs(TAG="MyApp")
        log.info("System initialized")
        2023-08-10 14:30:00,123 - MyApp - INFO - System initialized
    """

    def __init__(self, TAG=__name__):
        """初始化日志记录器及处理器。

        创建具有指定名称的日志记录器，配置控制台处理器，并设置彩色日志格式。

        Args:
            TAG (str, optional): 日志记录器标识名称，通常使用模块名(__name__)，
                用于区分不同模块的日志。默认为当前模块名。

        Note:
            - 日志级别设置为DEBUG(最低级别)，会捕获所有级别的日志
            - 添加StreamHandler到根日志记录器，确保日志输出到控制台
            - 相同TAG的实例会共享处理器配置(因logging模块的单例特性)
        """
        # 创建指定名称的日志记录器实例
        self.logger = logging.getLogger(TAG)
        # 设置日志记录器的最低处理级别为DEBUG
        self.logger.setLevel(logging.DEBUG)
        # 关键：阻止向上冒泡到 root，避免重复
        self.logger.propagate = False

        # 彩色 formatter
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            reset=True,
            log_colors={
                'DEBUG': 'green',
                'INFO': 'white,bold',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )

        # 仅当未添加过我们自己的控制台 handler 时再添加，防止重复
        if not any(getattr(h, "_xlogs_console", False) for h in self.logger.handlers):
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch._xlogs_console = True  # 防重复标记
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def fatal(self, msg, *args, **kwargs):
        """记录FATAL级别日志(最高级别)。

        该级别表示程序遇到严重错误，可能导致系统崩溃。

        Args:
            msg (str): 日志消息，支持printf格式
            *args: 格式化参数
            **kwargs: 扩展参数，可包含'exc_info'等logging模块支持参数

        Example:
            log.fatal("Critical failure in %s", "core module")
        """
        self.logger.fatal(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """记录ERROR级别日志。

        用于记录程序运行中的错误事件，但系统仍可继续运行。

        Args:
            msg (str): 日志消息，支持printf格式
            *args: 格式化参数
            **kwargs: 扩展参数，如exc_info=True可记录异常堆栈

        Example:
            try:
                 risky_operation()
            except Exception as e:
                 log.error("Operation failed: %s", e, exc_info=True)
        """
        self.logger.error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """记录WARNING级别日志。

        用于记录潜在的问题或非预期情况，但程序仍可正常运行。

        Args:
            msg (str): 日志消息，支持printf格式
            *args: 格式化参数
            **kwargs: 扩展参数

        Example:
            log.warn("Disk space below 10%%!")
        """
        self.logger.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """记录INFO级别日志。

        用于记录常规的系统运行信息，如服务启动、配置加载等。

        Args:
            msg (str): 日志消息，支持printf格式
            *args: 格式化参数
            **kwargs: 扩展参数

        Example:
            log.info("Server started on port %d", 8080)
        """
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """记录DEBUG级别日志。

        用于调试时输出详细运行信息，生产环境通常关闭。

        Args:
            msg (str): 日志消息，支持printf格式
            *args: 格式化参数
            **kwargs: 扩展参数

        Example:
            log.debug("Received request: %s", request.headers)
        """
        self.logger.debug(msg, *args, **kwargs)
