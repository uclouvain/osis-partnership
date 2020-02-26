from .partner import *
from .partnership import *

# Prevent polluting the namespace with module names
for name in ['partner', 'partnership']:
    del globals()[name]
