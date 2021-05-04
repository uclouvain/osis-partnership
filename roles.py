from osis_role import role
from partnership.auth.roles.partnership_manager import PartnershipEntityManager
from partnership.auth.roles.partnership_viewer import PartnershipViewer

role.role_manager.register(PartnershipViewer)
role.role_manager.register(PartnershipEntityManager)
