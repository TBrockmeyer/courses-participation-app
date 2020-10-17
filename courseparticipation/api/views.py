from django.core.wsgi import get_wsgi_application
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courseparticipation.settings')

application = get_wsgi_application()

from django.conf import settings
if not settings.configured:
    settings.configure()

from api.models import Course
from rest_framework import generics, status

from api.serializers import CourseSerializer
from api.generate_db_entries import DbEntriesCreation

# https://www.django-rest-framework.org/tutorial/2-requests-and-responses/
from rest_framework.response import Response

import os
import inspect

class CourseList(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        # user_creation = DbEntriesCreation.create_user('admin', 'admin', True, True)
        # Owner can be defined e.g. through serializer.save(owner=self.request.user)
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    # TODO: create test in TestApi.py