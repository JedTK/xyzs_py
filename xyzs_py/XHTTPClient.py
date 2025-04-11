import aiohttp

from xyzs_py.XLogs import XLogs

# 初始化日志系统，用于记录程序的运行状态
logger = XLogs(__name__)


class RequestMethod:
    """
    定义HTTP请求方法类型的枚举类。
    """
    POST = 'POST'
    GET = 'GET'


class ContentType:
    """
    定义HTTP请求中Content-Type的常见类型的枚举类。
    """
    FORM_URLENCODED = 'application/x-www-form-urlencoded'
    MULTIPART_FORM_DATA = 'multipart/form-config'
    JSON = 'application/json'


class XHTTPClient:
    """
    提供HTTP请求的静态方法集合，封装了aiohttp库的使用，简化HTTP请求过程。
    方法均为静态方法，可以直接通过类名调用。
    """

    @staticmethod
    async def request(url, params=None, content_type=ContentType.FORM_URLENCODED, method=RequestMethod.GET,
                      headers=None):
        """
        发送HTTP请求的通用方法。

        参数:
        url (str): 请求的URL。
        params (dict, optional): 请求的参数。
        content_type (str): 请求的内容类型，来自ContentType枚举类。
        method (str): 请求方法，来自RequestMethod枚举类。
        headers (dict, optional): 请求头。

        返回:
        str: 服务器的响应文本，如果响应状态码不是200，则返回None。
        """
        if headers is None: headers = {}
        headers['Content-Type'] = content_type
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url,
                                           data=params if content_type != ContentType.JSON else None,
                                           json=params if content_type == ContentType.JSON else None,
                                           headers=headers) as response:
                    if response.status != 200:
                        logger.warn(f"服务器响应异常：{response.status}")
                        return None
                    return await response.text()
        except Exception as e:
            logger.error(f"Exception {str(e)} on {url}")
            return None

    @staticmethod
    async def fetch_json(url, params=None, content_type=ContentType.FORM_URLENCODED, method=RequestMethod.GET,
                         headers=None):
        """
        发送HTTP请求并获取JSON响应的方法。

        参数:
        url (str): 请求的URL。
        params (dict, optional): 请求的参数。
        content_type (str): 请求的内容类型，来自ContentType枚举类。
        method (str): 请求方法，来自RequestMethod枚举类。
        headers (dict, optional): 请求头。

        返回:
        dict: 服务器的响应数据，解析为JSON格式，如果响应状态码不是200，则返回None。
        """
        if headers is None: headers = {}
        headers['Content-Type'] = content_type
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url,
                                           data=params if content_type != ContentType.JSON else None,
                                           json=params if content_type == ContentType.JSON else None,
                                           headers=headers) as response:
                    if response.status != 200:
                        logger.warn(f"服务器响应异常：{response.status}")
                        return None
                    return await response.json()
        except Exception as e:
            logger.error(f"Exception {str(e)} on {url}")
            return None

    @staticmethod
    async def get(url, params=None, content_type=ContentType.FORM_URLENCODED, headers=None):
        """
        封装的GET请求方法，简化调用。

        参数和返回同 request 方法。
        """
        return await XHTTPClient.request(url,
                                         params=params,
                                         content_type=content_type,
                                         method=RequestMethod.GET,
                                         headers=headers)

    @staticmethod
    async def post(url, params=None, content_type=ContentType.FORM_URLENCODED, headers=None):
        """
        封装的POST请求方法，简化调用。

        参数和返回同 request 方法。
        """
        return await XHTTPClient.request(url,
                                         params=params,
                                         content_type=content_type,
                                         method=RequestMethod.POST,
                                         headers=headers)

    @staticmethod
    async def fetch_get_json(url, params=None, content_type=ContentType.FORM_URLENCODED, headers=None):
        """
        封装的GET请求方法，用于获取JSON响应，简化调用。

        参数和返回同 fetch_json 方法。
        """
        return await XHTTPClient.fetch_json(url,
                                            params=params,
                                            content_type=content_type,
                                            method=RequestMethod.GET,
                                            headers=headers)

    @staticmethod
    async def fetch_post_json(url, params=None, content_type=ContentType.FORM_URLENCODED, headers=None):
        """
        封装的POST请求方法，用于获取JSON响应，简化调用。

        参数和返回同 fetch_json 方法。
        """
        return await XHTTPClient.fetch_json(url,
                                            params=params,
                                            content_type=content_type,
                                            method=RequestMethod.POST,
                                            headers=headers)

    @staticmethod
    async def upload(url, file_data, headers=None):
        """
        文件上传的特殊方法，构造multipart/form-data类型的请求。

        参数:
        url (str): 请求的URL。
        file_data (io.BytesIO): 要上传的文件数据。
        headers (dict, optional): 请求头。

        返回:
        str: 服务器的响应文本，如果响应状态码不是200，则返回None。
        """
        form = aiohttp.FormData()
        form.add_field('file', file_data)
        return await XHTTPClient.request(url,
                                         params=form,
                                         content_type=ContentType.MULTIPART_FORM_DATA,
                                         method=RequestMethod.POST,
                                         headers=headers)
