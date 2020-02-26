from .contact import *
from .fields import *
from .financing import *
from .media import *
from .partner import *
from .partnership import *
from .ucl_management_entity import *
from .widgets import *

# Prevent polluting the namespace with module names
for name in ['contact', 'fields', 'financing', 'media', 'partner',
             'partnership', 'ucl_management_entity', 'widgets']:
    del globals()[name]
