from django.core.wsgi import get_wsgi_application
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'courseparticipation.settings')

application = get_wsgi_application()

from django.conf import settings
if not settings.configured:
    settings.configure()

from api.models import Course, Participation
from rest_framework import generics, status, exceptions

from api.serializers import CourseSerializer, UserSerializer, ParticipationSerializer
from api.generate_db_entries import DbEntriesCreation

# https://www.django-rest-framework.org/tutorial/2-requests-and-responses/
from rest_framework.response import Response

from django.contrib.auth.models import User

from api.permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

class CourseList(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        # Owner can be defined e.g. through serializer.save(owner=self.request.user)
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

# Add classes for the User models defined in django.contrib.auth.models
class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ParticipationCreation(generics.CreateAPIView):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer
    permission_classes = [IsOwnerOrAdmin]

    # Users call this endpoint indicating a participation_course_id and a Participation_course_phase.
    # TODO: ensure that a participation_course_phase is within the available range of phases
    # (needs to unsubscribe there / or indicate new phase if already in Course)
    """
    Check given user_id: does have existing participation?
    ├─ No ► Create new participation with requested user_id, course_id and course_phase
    └─ Yes ► Is requested course_phase same as that of existing participation?
        ├─ No ► Refuse request with error  and inform in response that old participation needs to be deleted first
        └─ Yes ► Is requested course_phase adjoining step to that of existing participation?
            ├─ No ► Refuse request with error  and inform in response that only jumps to adjoining phases allowed
            └─ Yes ► update info in database by saving data from request through serializer
    """
    def get_relevant_user_id(self):
        relevant_user_id = self.request.user.id
        if ('user_id' in self.request.data):
            relevant_user_id=int(self.request.data['user_id'])
        return relevant_user_id

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        existing_participation = Participation.objects.filter(user_id=self.get_relevant_user_id())
        if (existing_participation.count() > 0):
            message = "A Participation for this user_id already exists. Delete unwanted participation first by calling participations/delete/."
            raise exceptions.ValidationError(detail=message)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user_id=self.get_relevant_user_id())


class ParticipationUpdate(generics.UpdateAPIView):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer
    permission_classes = [IsOwnerOrAdmin]

    # Users call this endpoint indicating a participation_course_id and a Participation_course_phase.
    # TODO: ensure that a participation_course_phase is within the available range of phases
    # TODO: ensure that only the participation_course_phase can be updated (not the participation_course_id).
    # For switching participation_course_id, old participation needs to be deleted and a new one created.


class ParticipationDeletion(generics.DestroyAPIView):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self, request):
        """
        Returns the object the view is displaying.
        """
        # Ensure that returned object belongs to requesting user
        queryset = Participation.objects.filter(user_id=request.user.id)

        filter_kwargs = {}
        obj = generics.get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    """
    Destroy a model instance. (Overridden from rest_framework/mixins.py)
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object(self.request)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ParticipationList(generics.ListAPIView):
    queryset = Participation.objects.all()
    serializer_class = ParticipationSerializer
    permission_classes = [IsOwnerOrAdmin]

    # TODO: ensure that list only shows participations relevant to authenticated user
    # TODO: write separate endpoint to provide primary key of participation

    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        requesting_user_id = list(User.objects.filter(username=request.user).values())[0]['id']
        if(not request.user.is_superuser or not request.user.is_staff):
            queryset = queryset.filter(user_id=requesting_user_id)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
