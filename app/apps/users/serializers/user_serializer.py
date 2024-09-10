from rest_framework import serializers
from django.core.exceptions import ValidationError

from apps.users.models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2', 'user_type']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise ValidationError({'password2': 'Passwords must match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
