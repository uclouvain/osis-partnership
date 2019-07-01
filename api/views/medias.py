import os

from django.http.response import FileResponse
from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from partnership.api.serializers import MediaWithMetadataSerializer
from partnership.models import Media


class MediaMetadataRetrieveView(generics.RetrieveAPIView):
    serializer_class = MediaWithMetadataSerializer
    permission_classes = (AllowAny,)
    queryset = Media.objects.all()
    lookup_field = 'uuid'


class MediaPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.visibility == Media.VISIBILITY_PUBLIC:
            return True
        person = request.user.person
        if person is None:
            return False
        # Employee can access all files
        if person.employee:
            return True
        # Else we check if the medi can be accessed by student
        # and if the user is a student
        if obj.visibility == Media.VISIBILITY_STAFF_STUDENT:
            if person.student_set.exists():
                return True
        return False


class MediaDownloadView(generics.GenericAPIView):
    serializer_class = MediaWithMetadataSerializer
    permission_classes = (MediaPermission,)
    queryset = Media.objects.all()
    lookup_field = 'uuid'

    def get(self, *args, **kwargs):
        media = self.get_object()
        if media.url is not None:
            return Response(data={'url': media.url})
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response
