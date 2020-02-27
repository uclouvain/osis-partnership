from .agreement import *
from .contact import *
from .media import *
from .partnership import *

# Prevent polluting the namespace with module names
for name in ['agreement', 'contact', 'media', 'partnership']:
    del globals()[name]
