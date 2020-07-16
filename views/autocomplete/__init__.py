from .faculty import *
from .funding import *
from .offers import *
from .partner import *
from .partnership import *
from .person import *
from .ucl_university import *

# Prevent polluting the namespace with module names
for name in ['faculty', 'funding', 'offers', 'partner', 'partnership', 'person',
             'ucl_university']:
    del globals()[name]
