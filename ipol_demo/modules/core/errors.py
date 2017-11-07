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
        self.index = index
        self.max_weight = int(max_weight)


class IPOLMissingRequiredInputError(Exception):
    """
    IPOLMissingRequiredInputError
    """
    def __init__(self, index):
        self.index = index
