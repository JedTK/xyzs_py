import calendar
import math
import re
import time
from datetime import datetime, timedelta as td
from decimal import Decimal, ROUND_HALF_UP


class TimeUtil:
    """

    时间操作辅助类
    """

    @staticmethod
    def time():
        """
        返回当前时间戳（毫秒）。
        """
        return int(time.time() * 1000)

    @staticmethod
    def get_timedelta(days=0, hours=0, minutes=0, seconds=0, milliseconds=0, weeks=0):
        """
        返回调整后的时间戳（毫秒）。
        :param days: 与当前日期相差的天数。默认值为 0，表示当前时间。
        :param hours: 与当前日期相差的小时数。默认值为 0。
        :param minutes: 与当前日期相差的分钟数。默认值为 0。
        :param seconds: 与当前日期相差的秒数。默认值为 0。
        :param milliseconds: 与当前日期相差的毫秒数。默认值为 0。
        :param weeks: 与当前日期相差的周数。默认值为 0。
        :return: 时间戳（毫秒）。
        """
        # 将所有参数传递给timedelta进行时间差的计算
        delta = td(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        target_time = datetime.now() + delta
        return int(target_time.timestamp() * 1000)

    @staticmethod
    def to_time(time_str, time_format="%Y-%m-%d %H:%M:%S"):
        """
        将给定的时间字符串转换为毫秒级时间戳。

        :param time_str: 需要转换的时间字符串。
        :param time_format: 时间字符串的格式，默认为 "%Y-%m-%d %H:%M:%S"。
        :return: 转换得到的毫秒级时间戳，如果转换失败则返回 None。
        """
        try:
            # 将时间字符串按照指定格式转换为 datetime 对象
            dt = datetime.strptime(time_str, time_format)
            # 将 datetime 对象转换为时间戳，并转换为毫秒级（乘以1000并取整）
            timestamp_ms = int(dt.timestamp() * 1000)
            return timestamp_ms
        except ValueError:
            # 如果时间字符串不符合格式，返回 None
            return None

    @staticmethod
    def time_str(timestamp=None, time_format="%Y-%m-%d %H:%M:%S"):
        """
        返回指定时间戳的格式化字符串，如果没有指定时间戳则返回当前时间的格式化字符串。

        :param timestamp: 时间戳，毫秒级
        :param time_format: 时间格式
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒
        time_tuple = time.localtime(timestamp)  # 从时间戳转换到时间元组
        formatted_time = time.strftime(time_format, time_tuple)
        return formatted_time

    # region 计算 定时间戳或当前时间 的年、季度、月、日、时的开始时间

    @staticmethod
    def year_begin(timestamp=None, year_delta=0):
        """
        返回指定时间戳或当前时间的前/后几年的开始时间戳（该年的第一天凌晨0点）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        :param year_delta: 要添加或减去的年数
        """
        if timestamp is None:
            current_time = time.time()
        else:
            current_time = timestamp / 1000

        local_time = time.localtime(current_time)
        year = local_time.tm_year + year_delta

        first_day_time = time.mktime((year, 1, 1, 0, 0, 0, 0, 0, -1))
        return int(first_day_time * 1000)

    @staticmethod
    def year_end(timestamp=None, year_delta=0):
        """
        返回指定时间戳或当前时间的前/后几年的结束时间戳（该年的最后一天午夜24点前一秒）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        :param year_delta: 要添加或减去的年数
        """
        if timestamp is None:
            current_time = time.time()
        else:
            current_time = timestamp / 1000

        local_time = time.localtime(current_time)
        year = local_time.tm_year + year_delta

        last_day_time = time.mktime((year, 12, 31, 23, 59, 59, 0, 0, -1))
        return int(last_day_time * 1000)

    @staticmethod
    def quarter_begin(timestamp=None):
        """
        返回指定时间戳或当前时间所在季度的开始时间戳（该季度第一天凌晨0点）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(timestamp)
        month = local_time.tm_mon
        quarter_start_month = (month - 1) // 3 * 3 + 1  # 计算该季度的第一个月

        quarter_start_time = time.mktime((local_time.tm_year, quarter_start_month, 1, 0, 0, 0, 0, 0, -1))
        return int(quarter_start_time * 1000)

    @staticmethod
    def quarter_end(timestamp=None):
        """
        返回指定时间戳或当前时间所在季度的结束时间戳（该季度最后一天午夜24点前一秒）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(timestamp)
        month = local_time.tm_mon
        quarter_end_month = (month - 1) // 3 * 3 + 3  # 计算该季度的最后一个月

        last_day = calendar.monthrange(local_time.tm_year, quarter_end_month)[1]  # 获取季度最后一个月的最后一天
        quarter_end_time = time.mktime((local_time.tm_year, quarter_end_month, last_day, 23, 59, 59, 0, 0, -1))
        return int(quarter_end_time * 1000)

    @staticmethod
    def month_begin(timestamp=None, month_delta=0):
        """
        返回指定时间戳或当前时间的前/后几个月的开始时间戳（该月的第一天凌晨0点）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        :param month_delta: 要添加或减去的月数
        """
        if timestamp is None:
            current_time = time.time()  # 获取当前时间戳（秒级）
        else:
            current_time = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(current_time)
        year, month = local_time.tm_year, local_time.tm_mon + month_delta
        year += month // 12  # 计算年的偏移
        month = month % 12 or 12  # 处理月份溢出和12月的特殊情况

        first_day_time = time.mktime((year, month, 1, 0, 0, 0, 0, 0, -1))
        return int(first_day_time * 1000)

    @staticmethod
    def month_end(timestamp=None, month_delta=0):
        """
        返回指定时间戳或当前时间的前/后几个月的结束时间戳（该月的最后一天午夜24点前一秒）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        :param month_delta: 要添加或减去的月数
        """
        if timestamp is None:
            current_time = time.time()  # 获取当前时间戳（秒级）
        else:
            current_time = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(current_time)
        year, month = local_time.tm_year, local_time.tm_mon + month_delta
        year += month // 12  # 计算年的偏移
        month = month % 12 or 12  # 处理月份溢出和12月的特殊情况

        last_day = calendar.monthrange(year, month)[1]
        last_day_time = time.mktime((year, month, last_day, 23, 59, 59, 0, 0, -1))
        return int(last_day_time * 1000)

    @staticmethod
    def day_begin(timestamp=None, day=0):
        """
        返回指定时间戳或当前时间的前/后几天的开始时间戳（凌晨0点）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        :param day: 要添加或减去的天数
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(timestamp)
        start_of_day = time.mktime((local_time.tm_year, local_time.tm_mon, local_time.tm_mday + day, 0, 0, 0, 0, 0, -1))
        return int(start_of_day * 1000)

    @staticmethod
    def day_end(timestamp=None, day=0):
        """
        返回指定时间戳或当前时间的前/后几天的结束时间戳（午夜24点前一秒）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        :param day: 要添加或减去的天数
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(timestamp)
        end_of_day = time.mktime(
            (local_time.tm_year, local_time.tm_mon, local_time.tm_mday + day, 23, 59, 59, 0, 0, -1))
        return int(end_of_day * 1000)

    @staticmethod
    def hour_begin(timestamp=None):
        """
        返回指定时间戳或当前时间所在小时的开始时间戳（整点小时）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(timestamp)
        hour_start = time.mktime(
            (local_time.tm_year, local_time.tm_mon, local_time.tm_mday, local_time.tm_hour, 0, 0, 0, 0, -1))
        return int(hour_start * 1000)

    @staticmethod
    def hour_end(timestamp=None):
        """
        返回指定时间戳或当前时间所在小时的结束时间戳（整点小时前一秒）。

        :param timestamp: 时间戳，毫秒级，如果为 None 则使用当前时间
        """
        if timestamp is None:
            timestamp = time.time()  # 获取当前时间戳（秒级）
        else:
            timestamp = timestamp / 1000  # 转换毫秒到秒

        local_time = time.localtime(timestamp)
        hour_end = time.mktime(
            (local_time.tm_year, local_time.tm_mon, local_time.tm_mday, local_time.tm_hour, 59, 59, 0, 0, -1))
        return int(hour_end * 1000)

    # endregion

    # region 时间换算

    @staticmethod
    def to_full_hours(seconds):
        """
        将秒转换成整数小时，向上取整。

        :param seconds: 时间长度，单位秒
        :return: 整数小时
        """
        hours = seconds / 3600
        return math.ceil(hours)

    @staticmethod
    def to_decimal_hours(seconds):
        """
        将秒转换成小时，保留两位小数。

        :param seconds: 时间长度，单位秒
        :return: 小时数，Decimal 类型
        """
        seconds_decimal = Decimal(seconds)
        hours_in_seconds = Decimal(3600)
        return seconds_decimal / hours_in_seconds.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def divide_time(seconds, interval):
        """
        将时间划分成几个等份（向上取整），例如：将1小时按照指定分钟进行计算可以划分多少份。

        :param seconds: 时间长度，单位秒
        :param interval: 划分等份的时间长度，单位秒
        :return: 划分的份数
        """
        portions = seconds / interval
        return math.ceil(portions)

    @staticmethod
    def format_seconds(seconds: int, time_format: str = "{h}时{m}分{s}秒", strip_empty_units: bool = True) -> str:
        """
        将秒转换成指定格式的时间字符串。

        :param seconds: 时间长度，单位秒
        :param time_format: 输出格式字符串，默认为"{h}时{m}分{s}秒"
        :param strip_empty_units: 是否去除数值为零的时间单位，默认为True
        :return: 格式化后的时间字符串。
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        formatted_time = time_format.format(h=hours, m=minutes, s=seconds)

        if strip_empty_units:
            # 使用正则表达式去除零单位
            formatted_time = re.sub(r'0[时分](?![^{]*})', '', formatted_time)
            if not re.search(r'[1-9]', formatted_time):  # 如果没有任何非零数字
                formatted_time = formatted_time.replace("0秒", "0秒")  # 确保至少显示“0秒”

        return formatted_time.strip()

    # endregion
