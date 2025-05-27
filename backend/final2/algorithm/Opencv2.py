import cv2
import numpy as np


def calculate_texture_complexity(image):
    """计算图像纹理复杂度（基于灰度共生矩阵）"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist /= hist.sum()

    contrast = np.sum((hist * np.arange(256)) ** 2)
    entropy = -np.sum(hist[hist > 0] * np.log2(hist[hist > 0] + 1e-6))

    texture_score = (contrast + entropy) / (256 ** 2 + 256)
    return min(texture_score, 1.0)


def check_element_completeness(image, template_path=None):
    """检查服装元素完整性（使用模板匹配）"""
    if template_path:
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            return 0.0
        
        # 转换图像为灰度
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 检查尺寸，确保模板不大于图像
        img_h, img_w = gray_image.shape
        temp_h, temp_w = template.shape
        
        # 如果模板比图像大，调整模板尺寸
        if temp_h > img_h or temp_w > img_w:
            # 计算缩放比例，保持宽高比
            scale_h = img_h / temp_h if temp_h > img_h else 1.0
            scale_w = img_w / temp_w if temp_w > img_w else 1.0
            scale = min(scale_h, scale_w, 0.8)  # 最大缩放到80%
            
            new_w = int(temp_w * scale)
            new_h = int(temp_h * scale)
            template = cv2.resize(template, (new_w, new_h))
        
        # 如果调整后的模板仍然太大或太小，返回默认值
        temp_h, temp_w = template.shape
        if temp_h > img_h or temp_w > img_w or temp_h < 10 or temp_w < 10:
            return 0.5  # 返回中等完整性分数
        
        try:
            res = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
            return float(res.max())
        except cv2.error as e:
            print(f"模板匹配错误: {e}")
            return 0.5  # 返回中等完整性分数
    return 1.0

def calculate_quality_metrics(image):
    """计算图像质量指标（清晰度、噪声）优化版"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 清晰度计算（调整基准值）
    laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
    clarity_base = laplacian / 150  # 基准值从150调整为50

    # 噪声水平计算（逻辑反转）
    noise_level = gray.std()
    noise_factor = min(noise_level / 30, 1.0)  # 噪声越大得分越高

    # 质量得分改进（防止乘积归零）
    quality_score = (clarity_base + noise_factor) / 2  # 改用平均值

    return min(max(quality_score, 0), 1)

#旧代码，暂保留
#def calculate_quality_metrics(image):
    #"""计算图像质量指标（清晰度、噪声）"""
    #gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    #laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
    #noise = gray.std()

    #clarity_base = min(laplacian / 150, 1.0)
    #noise_factor = max(1 - (noise / 30), 0)
    #quality_score = clarity_base * noise_factor

    #return min(max(quality_score, 0), 1)


def evaluate_fashion_image(template_path,image_path):
    """综合评估函数（四级质量等级）"""
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), -1)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    # 初始化评分字典
    scores = {
        'texture': 0.0,
        'completeness': 0.0,
        'quality': 0.0
    }

    # 计算各维度得分
    scores['texture'] = calculate_texture_complexity(img)
    scores['completeness'] = check_element_completeness(img, template_path)
    scores['quality'] = calculate_quality_metrics(img)

    # 加权综合评分
    weights = {'texture': 0.3, 'completeness': 0.3, 'quality': 0.4}
    overall = sum(scores[k] * weights[k] for k in weights)

    # 四级质量等级判断
    grade_thresholds = {
        'A': 0.9,  # 优秀（接近完美）
        'B': 0.7,  # 良好（可接受）
        'C': 0.5,  # 合格（需改进）
        'D': 0.0  # 不可用（严重缺陷）
    }

    # 动态确定等级
    quality_grade = 'D'
    for grade, threshold in grade_thresholds.items():
        if overall >= threshold:
            quality_grade = grade
            break

    # 人工审核逻辑
    needs_review = quality_grade in ('C', 'D')  # C/D级需要人工介入

    # 打印质量评估报告
    '''
    print("=" * 50)
    print(f"图像质量评估报告 ({image_path})")
    print("-" * 50)
    print(f"纹理复杂度: {scores['texture']:.3f}")
    print(f"元素完整性: {scores['completeness']:.3f}")
    print(f"画面质量: {scores['quality']:.3f}")
    print("-" * 50)
    print(f"综合评分: {overall:.3f}")
    print(f"质量等级: {quality_grade} {'' if overall == 1.0 else '⚠️'}")
    print(f"是否需人工: {'是' if needs_review else '否'}")
    
    # 状态指示器
    status_map = {
        'A': '✅ 优秀（无需处理）',
        'B': '🟢 良好（建议优化）',
        'C': '🟡 合格（需改进）',
        'D': '🔴 不可用（必须处理）'
    }

    print("\n" + "=" * 50)
    print(f"质量状态: {status_map[quality_grade]}")
    print("-" * 50)
    print("处理建议:")
    if needs_review:
        print("- ✅ 优先检查元素完整性")
        print("- 🟡 优化纹理复杂度")
        print("- 🔴 重点提升画面质量")
    else:
        print("- 🟢 无需人工干预，可直接使用")
    '''





    return {
        'texture': scores['texture'],
        'completeness': scores['completeness'],
        'quality': scores['quality'],
        'overall': overall,
        'quality_grade': quality_grade,
        'needs_human_review': needs_review
    }


