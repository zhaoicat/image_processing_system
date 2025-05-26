#!/usr/bin/env python
"""
测试图片批量上传API
"""
import requests
import json

# 登录获取token
def get_auth_token():
    login_url = "http://localhost:8888/api/auth/login/"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        return response.json().get('token')
    else:
        print(f"登录失败: {response.status_code}, {response.text}")
        return None

# 测试上传
def test_upload():
    token = get_auth_token()
    if not token:
        return
    
    print(f"获取到token: {token[:20]}...")
    
    # 创建一个小的测试图片文件
    import io
    from PIL import Image
    
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    upload_url = "http://localhost:8888/api/images/upload_multiple/"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    files = {
        'files': ('test_image.png', img_bytes, 'image/png')
    }
    
    print("发送上传请求...")
    response = requests.post(upload_url, headers=headers, files=files)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 201:
        print("✅ 上传成功!")
    else:
        print("❌ 上传失败!")

if __name__ == "__main__":
    test_upload() 