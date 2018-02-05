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
    """
    pass

class IPOLKeyError(Exception):
    """
    """
    pass


class IPOLDecodeInterfaceRequestError(Exception):
    """
    """
    pass


class IPOLReadDDLError(Exception):
    """
    """
    pass

class IPOLFindSuitableDR(Exception):
    """
    """
    pass



class IPOLEnsureCompilationAndDemoExtrasError(Exception):
    """
    """
    def __init__(self, interface_message, email_message=None):
        super(IPOLPrepareFolderError, self).__init__()
        self.interface_message = interface_message
        self.email_message = email_message

class IPOLConversionError(Exception):
    """
    """
    pass

class IPOLPrepareFolderError(Exception):
    """
    """
    def __init__(self, interface_message, email_message=None):
        super(IPOLPrepareFolderError, self).__init__()
        self.interface_message = interface_message
        self.email_message = email_message

class IPOLExecutionError(Exception):
    """
    """
    def __init__(self, interface_message, email_message=None):
        super(IPOLPrepareFolderError, self).__init__()
        self.interface_message = interface_message
        self.email_message = email_message

class IPOLError(Exception):
    """
    """
    pass

class IPOLDemoRunnerResponseError(Exception):
    """
    """
    def __init__(self, message, demo_state, key, error):
        super(IPOLDemoRunnerResponseError, self).__init__()
        self.message = message
        self.demo_state = demo_state
        self.key = key
        self.error = error

        
class IPOLArchiveError(Exception):
    """
    """
    pass
