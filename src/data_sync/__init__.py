# Make the main class available at the package level
from .core import DataSync
from .exceptions import DataSyncError

__all__ = ['DataSync', 'DataSyncError']
