import cv2
import numpy as np
import os


def calculate_image_quality(image_path, target_color=(255, 255, 255)):
    """
    综合质量评分（0~1范围，越大越好）
    包含三个维度：
    - 颜色匹配度 (40%权重)
    - 清晰度 (30%权重)
    - 噪声水平 (30%权重)
    """
    try:
        # 读取图像基础检查
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"文件不存在: {image_path}")
        img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
        # img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")

        # 转换为RGB格式
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # ---------------------
        # 1. 颜色匹配度计算
        # ---------------------
        target_array = np.full_like(img_rgb, target_color)
        color_diff = cv2.absdiff(img_rgb, target_array)
        avg_color_diff = np.mean(color_diff)  # 值越小越好 颜色匹配度初始值

        # 归一化到0-1（目标差异越小得分越高）
        color_score = 1 - (avg_color_diff / 255)  # 最大差异255

        # ---------------------
        # 2. 清晰度计算（拉普拉斯方差）
        # ---------------------
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # 归一化到0-1（值越大清晰度越高）
        sharpness_score = min(laplacian_var / 150, 1.0)  # 150为基准阈值  清晰度初始值

        # ---------------------
        # 3. 噪声水平计算（灰度标准差）
        # ---------------------
        noise_level = gray.std()

        # 归一化到0-1（值越大噪声越强，得分越高）
        # 基准阈值设为30，超过30的噪声按满分计算（可根据实际数据调整）
        noise_score = min(noise_level / 30, 1.0)  # 30为基准阈值  噪音初始值

        # 归一化到0-1（值越小越好）---旧
        # noise_score = 1 - (noise_level / 30)  # 30为基准阈值

        # ---------------------
        # 综合评分（加权平均）
        # ---------------------
        quality_score = color_score * 0.4 + sharpness_score * 0.3 + noise_score * 0.3

        result = {
            "color_score": color_score,  # 颜色匹配度
            "sharpness_score": sharpness_score,  # 清晰度
            "noise_score": noise_score,  # 噪声水平
            "quality_score": quality_score,  # 综合质量
            "initial_color_diff": avg_color_diff,  # 颜色匹配度初始值
            "initial_laplacian_var": laplacian_var,  # 清晰度初始值
            "initial_noise_level": noise_level,  # 噪音初始值
        }

        # 打印质量评估报告
        # print("===== 质量评估报告 =====")
        # print(f"颜色匹配度: {'高' if result['color_score'] >= 0.6 else '中' if result['color_score'] >= 0.4 else '低'}")
        # print(f"清晰度: {'清晰' if result['sharpness_score'] >= 0.6 else '一般' if result['sharpness_score'] >= 0.4 else '模糊'}")
        # print(f"噪声水平: {'低' if result['noise_score'] < 0.4 else '中' if result['noise_score'] < 0.6 else '高'}")
        # print(f"综合质量: {'优良' if result['quality_score'] >= 0.6 else '可用' if result['quality_score'] >= 0.4 else '差'}")

        # 质量等级判断
        # if result['quality_score'] >= 0.6:
        #   print("质量评级: 优良 🔵")
        # elif result['quality_score'] >= 0.4:
        #   print("质量评级: 可用 ⚪")
        # else:
        #   print("质量评级: 差 ❌")

        return result

    except Exception as e:
        print(f"错误: {str(e)}")
        return None


# 测试示例
# image_path = r"C:\Users\Administrator\Desktop\test\1.jpg"
# calculate_image_quality(image_path)
