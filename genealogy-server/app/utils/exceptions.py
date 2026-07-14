class AppException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class BadRequestException(AppException):
    def __init__(self, message: str = "请求参数错误"):
        super().__init__(400, message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "未授权"):
        super().__init__(401, message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "无权限访问"):
        super().__init__(403, message)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(404, message)


class ConflictException(AppException):
    def __init__(self, message: str = "资源冲突"):
        super().__init__(409, message)
