# Standard Library Imports

# Third-Party Library Imports

# Local Application Imports
from config import logger

def trace_exception_hierarchy(exc):
    exception_type = type(exc)
    hierarchy = []
    for cls in exception_type.__mro__:
        hierarchy.append(cls.__name__)
    logger.error(f"Exception hierarchy: {' -> '.join(hierarchy)}")