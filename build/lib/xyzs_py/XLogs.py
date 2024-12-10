import logging

import colorlog


class XLogs:
    def __init__(self, TAG=__name__):
        # 创建一个日志记录器
        self.logger = logging.getLogger(TAG)
        self.logger.setLevel(logging.DEBUG)

        # 创建一个控制台处理器并设置日志级别为DEBUG
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 创建一个颜色格式化器并将其添加到处理器中
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'green',
                'INFO': 'white,bold',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        ch.setFormatter(formatter)

        # 将处理器添加到日志记录器中
        self.logger.addHandler(ch)

    def fatal(self, msg, *args, **kwargs):
        self.logger.fatal(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
