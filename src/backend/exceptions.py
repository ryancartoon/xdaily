class AppException(Exception):
    """Base exception for the application"""
    pass

class APIError(AppException):
    """Exception raised for API-related errors"""
    pass

class AnalysisError(AppException):
    """Exception raised for analysis-related errors"""
    pass

class RetrievalError(AppException):
    """Exception raised for retrieval-related errors"""
    pass 