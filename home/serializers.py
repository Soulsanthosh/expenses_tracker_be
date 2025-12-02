from rest_framework import serializers
from .models import expenses


class ExpenseSerializer(serializers.ModelSerializer):
    
    class Meta:
        
        model = expenses
        fields = "__all__"