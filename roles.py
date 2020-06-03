from osis_role import role
from partnership.auth.roles.partnership_manager import PartnershipEntityManager

role.role_manager.register(PartnershipEntityManager)
