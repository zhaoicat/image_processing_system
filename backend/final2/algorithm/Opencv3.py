import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

# 特征权重（总和=1）
WEIGHTS = {
    'brenner': 0.75,
    'ssim': 0.25
}

def load_image_gray(image_path):
    """读取图像并转换为灰度"""
    #img = cv2.imread(image_path)
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
    if img is None:
        raise FileNotFoundError(f"无法找到图像文件: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray.astype(np.float32)

def brenner_gradient(gray_img):
    """Brenner梯度法计算图像清晰度"""
    step = 3
    h, w = gray_img.shape
    brenner = 0.0
    for i in range(0, h - step, step):
        for j in range(0, w, step):
            diff = gray_img[i, j] - gray_img[i + step, j]
            brenner += diff ** 2
    return (brenner / (h * w)) * 100

def ssim_contrast(gray_img):
    """使用SSIM计算图像对比度"""
    window = 7
    blurred = cv2.GaussianBlur(gray_img, (window, window), 0)
    data_range = np.max(gray_img) - np.min(gray_img)
    if data_range == 0:
        return 0.0
    contrast = ssim(gray_img, blurred, data_range=data_range, win_size=window)
    return contrast * 100

def calculate_composite_score(image_path):
    """计算图像清晰度综合得分"""
    try:
        gray = load_image_gray(image_path)
        scores = {
            'brenner': brenner_gradient(gray),
            'ssim': ssim_contrast(gray)
        }
        composite = sum(scores[k] * WEIGHTS[k] for k in scores)
        return {
            'raw_scores': scores,
            'composite': np.clip(composite, 0, 100),
            'initial_brenner': scores['brenner'],
            'initial_ssim': scores['ssim']
        }
    except Exception as e:
        print(f"分析失败: {str(e)}")
        return None

if __name__ == "__main__":
    test_image = r"C:\Users\Administrator\Desktop\parttime\data\data\20250408skt0000069.png"
    result = calculate_composite_score(test_image)

    if result:
        print("===== 清晰度分析报告 =====")
        print(f"Brenner梯度: {result['raw_scores']['brenner']:.1f}")
        print(f"SSIM对比度: {result['raw_scores']['ssim']:.1f}")
        # print(f"综合得分: {result['composite']:.1f}/100")

        # if result['composite'] >= 85:
        #     print("质量等级: 优秀")
        # elif result['composite'] >= 70:
        #     print("质量等级: 良好")
        # else:
        #     print("质量等级: 需改进")
