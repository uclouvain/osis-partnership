try:
    from .contact import *
    from .enums import *
    from .entity_proxy import *
    from .financing import *
    from .media import *
    from .partner import *
    from .partnership import *
    from .relation import *
    from .ucl_management_entity import *

    # Prevent polluting the namespace with module names
    for name in ['contact', 'financing', 'media', 'partner', 'entity_proxy',
                 'partnership', 'ucl_management_entity', 'relation']:
        del globals()[name]
except RuntimeError as e:  # pragma: no cover
    # There's a weird bug when running tests, the test runner seeing a models
    # package tries to import it directly, failing to do so
    import sys

    if 'test' not in sys.argv:
        raise e
