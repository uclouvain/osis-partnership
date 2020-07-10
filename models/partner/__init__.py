try:
    from .entity import *
    from .partner import *

    # Prevent polluting the namespace with module names
    for name in ['entity', 'partner']:
        del globals()[name]
except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
