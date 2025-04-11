class ExcelUtil:
    """
    Excel辅助函数
    """

    @staticmethod
    def column_index_by_name(column):
        """
        根据列名（如"A", "B", "C"等）获取列的索引（0-based）。

        参数:
            column (str): Excel 列名
        返回:
            int: 列的索引（0-based）
        异常:
            ValueError: 如果列名包含非大写字母字符
        """
        # 将列名转为大写以确保一致性
        column = column.upper()
        column_number = 0

        # 遍历列名中的每个字符
        for ch in column:
            # 检查字符是否为大写字母
            if not 'A' <= ch <= 'Z':
                raise ValueError("Invalid column name")
            # 计算方法：每次将前一次结果乘以26，再加上当前字符代表的数值
            # 'A'对应1，'B'对应2，...，'Z'对应26
            column_number = column_number * 26 + (ord(ch) - ord('A') + 1)

        # 返回 0-based 索引
        return column_number - 1

    @staticmethod
    def column_name_by_index(index):
        """
        根据列的索引（0-based）获取对应的Excel列名。

        参数:
            index (int): 列索引（0-based）
        返回:
            str: 对应的Excel列名
        异常:
            ValueError: 如果索引为负数
        """
        # 检查索引是否为负数
        if index < 0:
            raise ValueError("Index must be non-negative")

        column_name = []
        n = index + 1  # 转换为 1-based 以符合 Excel 列名计算

        # 当 n > 0 时，循环计算每个字符
        while n > 0:
            n -= 1  # 调整为计算时的 0-based
            remainder = n % 26  # 计算余数，对应当前位的字母
            column_name.append(chr(remainder + ord('A')))  # 添加对应的字母
            n //= 26  # 更新 n 为下一位

        # 将字符列表反转并连接成字符串
        column_name.reverse()
        return ''.join(column_name)
