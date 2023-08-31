from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Exists, OuterRef
from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, Favorite
from advertisements.permissions import IsOwnerOrReadOnly
from advertisements.serializers import AdvertisementSerializer


class ManageFavorite:
    @action(
      detail=True,
      methods=['get'],
      url_path='favorite',
      permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        instance = self.get_object()
        content_type = ContentType.objects.get_for_model(instance)
        if request.user.is_anonymous:
            raise ValidationError('You must be registered to add adverts to favorites')
        elif request.user.id != instance.creator.id:
            favorite_obj, created = Favorite.objects.get_or_create(
                user=request.user, content_type=content_type, object_id=instance.id
            )
        else:
            raise ValidationError('You can\'t add your own advert to favorites!')
        if created:
            return Response(
                {'message': 'Content is added to favorites'},
                status=status.HTTP_201_CREATED
            )
        else:
            favorite_obj.delete()
            return Response(
                {'message': 'Content is deleted from favorites'},
                status=status.HTTP_200_OK
            )

    @action(
        detail=False,
        methods=['get'],
        url_path='favorites',
        permission_classes=[IsAuthenticated, ]
    )
    def favorites(self, request):
        queryset = self.get_queryset().filter(is_favorite=True)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def annotate_qs_is_favorite_field(self, queryset):
        if self.request.user.is_authenticated:
            is_favorite_subquery = Favorite.objects.filter(
                object_id=OuterRef('pk'),
                user=self.request.user,
                content_type=ContentType.objects.get_for_model(queryset.model)
            )
            queryset = queryset.annotate(is_favorite=Exists(is_favorite_subquery))
        return queryset


class AdvertisementViewSet(ModelViewSet, ManageFavorite):
    """ViewSet для объявлений."""
    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = AdvertisementFilter

    def get_permissions(self):

        """Получение прав для действий."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            if self.request.user.is_superuser or self.request.user.is_staff:
                return []
            else:
                return [IsAuthenticated(), IsOwnerOrReadOnly()]

        return []

    def get_queryset(self):

        if self.request.user.is_anonymous:
            queryset = Advertisement.objects.filter(draft='FALSE')
        else:
            queryset = Advertisement.objects.filter(creator=self.request.user) ^\
                       Advertisement.objects.filter(draft='FALSE')\
                       & Advertisement.objects.exclude(creator=self.request.user)
        queryset = self.annotate_qs_is_favorite_field(queryset)

        return queryset
