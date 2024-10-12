


class ParseError(Exception):
    def __init__(self, msg):
        self.msg = msg


class FileAlignException(Exception):
    # the entire file is skipped
    def __init__(self, msg = ''):
        self.msg = msg


class VarAlignException(Exception):
    # only skip the variable
    def __init__(self, msg = ''):
        self.msg = msg
