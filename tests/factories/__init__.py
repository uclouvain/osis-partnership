from .agreement import *
from .contact import *
from .entity_manager import *
from .financing import *
from .media import *
from .partner import *
from .partnership import *
from .partnership_year import *
from .partnership_year_education import *
from .ucl_management_entity import *


# Prevent polluting the namespace with module names
for name in ['agreement', 'contact', 'entity_manager', 'financing',
             'media', 'partner', 'partnership', 'partnership_year',
             'partnership_year_education', 'ucl_management_entity']:
    del globals()[name]
