from rest_framework import status
from rest_framework.exceptions import APIException


class OrganizationAlreadyDeclareAsPartner(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'This organization is already declared as partner'
