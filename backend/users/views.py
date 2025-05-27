from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import UserSerializer, UserRegistrationSerializer
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

class RegisterView(CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer
    
class LoginView(APIView):
    """用户登录视图"""
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # 使用SimpleJWT创建令牌
            refresh = RefreshToken.for_user(user)
            
            response = Response()
            response.data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }
            return response
        else:
            return Response(
                {'detail': '用户名或密码错误'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutView(APIView):
    """用户登出视图"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        # 客户端应该删除JWT令牌
        return Response({'detail': '成功登出'}, status=status.HTTP_200_OK)

class VerifyTokenView(APIView):
    """验证令牌是否有效的视图"""
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request):
        # 如果请求能到达这里，说明令牌有效（IsAuthenticated权限已验证）
        return Response({
            'valid': True,
            'user': UserSerializer(request.user).data
        })
