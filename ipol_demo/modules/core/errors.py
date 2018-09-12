"""
Custom error exception types
"""

class IPOLDemoExtrasError(Exception):
    """
    IPOLDemoExtrasError
    """
    pass


class IPOLInputUploadError(Exception):
    """
    IPOLInputUploadError
    """
    pass

class IPOLUploadedInputRejectedError(Exception):
    """
    IPOLUploadedInputRejectedError
    """
    pass

class IPOLCopyBlobsError(Exception):
    """
    IPOLCopyBlobsError
    """
    pass


class IPOLProcessInputsError(Exception):
    """
    IPOLProcessInputsError
    """
    pass


class IPOLExtractError(Exception):
    """
    IPOLExtractError
    """
    pass


class IPOLInputUploadTooLargeError(Exception):
    """
    IPOLInputUploadTooLargeError
    """
    def __init__(self, index, max_weight):
        super(IPOLInputUploadTooLargeError, self).__init__()
        self.index = index
        self.max_weight = int(max_weight)


class IPOLMissingRequiredInputError(Exception):
    """
    IPOLMissingRequiredInputError
    """
    def __init__(self, index):
        super(IPOLMissingRequiredInputError, self).__init__()
        self.index = index


class IPOLWorkDirError(Exception):
    """
    IPOLWorkDirError
    """
    pass

class IPOLKeyError(Exception):
    """
    IPOLKeyError
    """
    pass


class IPOLDecodeInterfaceRequestError(Exception):
    """
    IPOLDecodeInterfaceRequestError
    """
    pass


class IPOLReadDDLError(Exception):
    """
    IPOLReadDDLError
    """
    pass

class IPOLCheckDDLError(Exception):
    """
    IPOLCheckDDLError
    """
    pass

class IPOLFindSuitableDR(Exception):
    """
    IPOLFindSuitableDR
    """
    pass

class IPOLEnsureCompilationError(Exception):
    """
    IPOLEnsureCompilationError
    """
    pass

class IPOLConversionError(Exception):
    """
    IPOLConversionError
    """
    pass

class IPOLPrepareFolderError(Exception):
    """
    IPOLPrepareFolderError
    """
    def __init__(self, interface_message, email_message=None):
        super(IPOLPrepareFolderError, self).__init__()
        self.interface_message = interface_message
        self.email_message = email_message

class IPOLExecutionError(Exception):
    """
    IPOLExecutionError
    """
    def __init__(self, interface_message, email_message=None):
        super(IPOLExecutionError, self).__init__()
        self.interface_message = interface_message
        self.email_message = email_message

class IPOLDemoRunnerResponseError(Exception):
    """
    IPOLDemoRunnerResponseError
    """
    def __init__(self, message, demo_state, key, error):
        super(IPOLDemoRunnerResponseError, self).__init__()
        self.message = message
        self.demo_state = demo_state
        self.key = key
        self.error = error
