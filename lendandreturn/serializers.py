from rest_framework import serializers
from .models import LendReturn


class LendReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = LendReturn
        fields = "__all__"
