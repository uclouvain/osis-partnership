from .create import *
from .delete import *
from .update import *

# Prevent polluting the namespace with module names
for name in ['create', 'delete', 'update']:
    del globals()[name]
