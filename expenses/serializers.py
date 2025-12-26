from rest_framework import serializers
from .models import expenses

class ExpensesSerializer(serializers.ModelSerializer):

    class Meta:
        model = expenses
        fields = '__all__'