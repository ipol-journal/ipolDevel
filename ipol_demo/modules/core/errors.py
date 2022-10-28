"""
Custom error exception types
"""

class IPOLDemoExtrasError(Exception):
    """
    IPOLDemoExtrasError
    """

class IPOLInputUploadError(Exception):
    """
    IPOLInputUploadError
    """

class IPOLUploadedInputRejectedError(Exception):
    """
    IPOLUploadedInputRejectedError
    """

class IPOLCopyBlobsError(Exception):
    """
    IPOLCopyBlobsError
    """

class IPOLProcessInputsError(Exception):
    """
    IPOLProcessInputsError
    """

class IPOLExtractError(Exception):
    """
    IPOLExtractError
    """

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

class IPOLKeyError(Exception):
    """
    IPOLKeyError
    """

class IPOLDecodeInterfaceRequestError(Exception):
    """
    IPOLDecodeInterfaceRequestError
    """

class IPOLReadDDLError(Exception):
    """
    IPOLReadDDLError
    """

    def __init__(self, error_message, error_code=None):
        super(IPOLReadDDLError, self).__init__()
        self.error_message = error_message
        self.error_code = error_code

class IPOLCheckDDLError(Exception):
    """
    IPOLCheckDDLError
    """

class IPOLFindSuitableDR(Exception):
    """
    IPOLFindSuitableDR
    """

class IPOLEnsureCompilationError(Exception):
    """
    IPOLEnsureCompilationError
    """

class IPOLConversionError(Exception):
    """
    IPOLConversionError
    """

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

class IPOLDeleteDemoError(Exception):
    """
    IPOLDeleteDemoError
    """
