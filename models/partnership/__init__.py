try:
    from .agreement import *
    from .configuration import *
    from .entity_manager import *
    from .partnership import *
    from .year import *

    # Prevent polluting the namespace with module names
    for name in ['agreement', 'configuration', 'entity_manager', 'partnership', 'year']:
        del globals()[name]
except RuntimeError as e:
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
