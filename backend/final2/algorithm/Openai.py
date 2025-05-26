# Date:$(DATE)
import requests

# 在 Openai3.py 中添加
def generate_prompt(input_image_uid, x_token):
    url = "http://zs-aigc-test.ur.com.cn/api/ck/prompts/generate"
    try:
        # ======== POST 请求示例 ========
        response = requests.post(
            url,
            json={  # 发送JSON数据（自动设置Content-Type为application/json）
                "accChildType": "",
                "garmentType": "Tops",
                "inputImageUid": input_image_uid,
                "ckType": "MJ_IMAGINE",
                "imageType": "IMAGE_TO_SHAPE_INIT",
            },
            headers={
                "Content-Type": "application/json",
                "Accept-Language": "zh-CN",
                "X-Token": x_token  # 使用传入的X-Token
            },
            timeout=30  # 超时设置（秒）
        )
        # 检查HTTP状态码（非200会抛出HTTPError异常）
        response.raise_for_status()
        # 解析JSON响应（如果是JSON格式）
        data = response.json()
        print("响应状态码:", response.status_code)
        print("响应内容:", data)
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP错误: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"连接错误: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"超时错误: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"请求错误: {err}")
