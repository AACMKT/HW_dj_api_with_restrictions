from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from advertisements.models import Advertisement


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'draft', 'created_at',)

    def create(self, validated_data):
        """Метод для создания"""

        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""

        if not self.context["request"].user.is_staff:
            if len(Advertisement.objects.filter(creator=self.context["request"].user,
                                                status='OPEN', draft='FALSE')) >= 10 \
                    and not data.get('status') == 'CLOSED':
                raise ValidationError('You have exceeded the limit of 10 actual adverts')
            else:
                return data
        return data
