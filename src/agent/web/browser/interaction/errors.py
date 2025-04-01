class BrowserError(Exception):
    """Base class for browser interaction errors."""
    pass

class NavigationError(BrowserError):
    """Raised when navigation fails."""
    pass

class ElementNotFoundError(BrowserError):
    """Raised when an element cannot be found."""
    pass

class InteractionError(BrowserError):
    """Raised when interaction with an element fails."""
    pass

class AuthenticationError(BrowserError):
    """Raised when login/authentication fails."""
    pass

class TimeoutError(BrowserError):
    """Raised when an operation times out."""
    pass 