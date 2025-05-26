from rest_framework import serializers
from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    """图像序列化器"""
    class Meta:
        model = Image
        fields = [
            'id', 'title', 'file', 'image_hash', 
            'uploaded_by', 'uploaded_at'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at'] 