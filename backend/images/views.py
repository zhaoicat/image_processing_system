from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import hashlib
import os
import logging
from .models import Image
from .serializers import ImageSerializer

logger = logging.getLogger(__name__)


class ImageViewSet(viewsets.ModelViewSet):
    """处理图像的视图集"""
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """创建时自动设置当前用户为上传者"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def upload_multiple(self, request):
        """批量上传图片"""
        logger.info(f"收到批量上传请求，用户: {request.user}")
        logger.info(f"请求文件数量: {len(request.FILES)}")
        logger.info(f"请求数据: {request.data}")
        
        files = request.FILES.getlist('files')
        logger.info(f"获取到的文件列表: {[f.name for f in files]}")
        
        if not files:
            logger.warning("没有找到上传的文件")
            return Response(
                {'error': '请选择要上传的文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_images = []
        errors = []
        
        for file in files:
            try:
                logger.info(f"处理文件: {file.name}, 大小: {file.size}")
                
                # 计算文件哈希值
                file_content = file.read()
                file_hash = hashlib.md5(file_content).hexdigest()
                file.seek(0)  # 重置文件指针
                
                logger.info(f"文件 {file.name} 的哈希值: {file_hash}")
                
                # 检查是否已存在相同哈希的图片
                existing_image = Image.objects.filter(
                    image_hash=file_hash
                ).first()
                if existing_image:
                    error_msg = f'图片 {file.name} 已存在'
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue
                
                # 直接创建图片实例
                title = os.path.splitext(file.name)[0]
                logger.info(f"创建图片记录，标题: {title}")
                
                # 创建Image实例
                image = Image.objects.create(
                    title=title,
                    file=file,
                    image_hash=file_hash,
                    uploaded_by=request.user
                )
                
                # 序列化返回数据
                serializer = self.get_serializer(image)
                uploaded_images.append(serializer.data)
                logger.info(f"图片 {file.name} 保存成功，ID: {image.id}")
                    
            except Exception as e:
                error_msg = f'处理图片 {file.name} 时出错: {str(e)}'
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        response_data = {
            'uploaded_count': len(uploaded_images),
            'uploaded_images': uploaded_images,
            'errors': errors
        }
        
        logger.info(f"上传完成: 成功 {len(uploaded_images)} 个，错误 {len(errors)} 个")
        
        if uploaded_images:
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            logger.warning(f"没有成功上传任何文件，错误: {errors}")
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST) 