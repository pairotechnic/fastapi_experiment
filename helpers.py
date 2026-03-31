# Standard Library Imports

# Third-Party Library Imports

# Local Application Imports
from config import logger

def trace_exception_hierarchy(exc):
    exception_type = type(exc)
    logger.error(f"{exception_type.__mro__}")

def main():
    import aiohttp
    trace_exception_hierarchy(aiohttp.ServerTimeoutError())

if __name__ == "__main__":
    main()