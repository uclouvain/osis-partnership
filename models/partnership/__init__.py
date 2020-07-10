try:
    from .agreement import *
    from .configuration import *
    from .partnership import *
    from .partnership_year import *
    from .partnership_year_education import *

    # Prevent polluting the namespace with module names
    for name in ['agreement', 'configuration', 'partnership',
                 'partnership_year', 'partnership_year_education']:
        del globals()[name]
except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
