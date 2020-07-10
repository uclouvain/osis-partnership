try:
    from .address import *
    from .contact import *
    from .enums import *
    from .financing import *
    from .media import *
    from .partner import *
    from .partnership import *
    from .ucl_management_entity import *

    # Prevent polluting the namespace with module names
    for name in ['address', 'contact', 'financing', 'media', 'partner',
                 'partnership', 'ucl_management_entity']:
        del globals()[name]
except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
