from rest_framework import serializers
from .models import New, NewCategory

class NewCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NewCategory
        fields = ['id', 'name']

class NewSerializer(serializers.ModelSerializer):
    category = NewCategorySerializer(read_only=True)

    class Meta:
        model = New
        fields = ['id', 'title', 'content', 'category', 'created_at']
