class ResallocIBMCloudException(Exception):
    """Base exception class for Resalloc IBM Cloud errors."""


class PowerVSException(ResallocIBMCloudException):
    """Base exception class for PowerVS errors."""

class PowerVSNotFoundException(PowerVSException):
    """Exception raised when a PowerVS resource is not found."""


class PowerVSInvalidNameException(PowerVSException):
    """Exception raised when a PowerVS resource name is invalid."""
