"""
图像处理系统配置文件
统一管理所有算法的配置参数
"""

# 默认算法配置参数
DEFAULT_CONFIG = {
    'distance_threshold': 0,  # 图像哈希算法中的相似度阈值

    'color_score_threshold_high': 50,  # 颜色评分的高阈值
    'color_score_threshold_low': 20,  # 颜色评分的低阈值
    'sharpness_score_threshold_high': 100,  # 清晰度评分的高阈值
    'sharpness_score_threshold_low': 30,  # 清晰度评分的低阈值
    'comprehensiveness_score_threshold_high': 0.6,  # 综合质量评分的高阈值
    'comprehensiveness_score_threshold_low': 0.4,  # 综合质量评分的低阈值
    'noise_score_threshold_low': 30,  # 噪声评分的低阈值
    'noise_score_threshold_high': 50,  # 噪声评分的高阈值

    'texture_threshold_high': 0.6,  # 纹理评分的高阈值
    'texture_threshold_low': 0.4,  # 纹理评分的低阈值
    'completeness_threshold_high': 0.6,  # 完整性评分的高阈值
    'completeness_threshold_low': 0.4,  # 完整性评分的低阈值
    'quality_score_threshold_high': 0.6,  # 图像质量评分的高阈值
    'quality_score_threshold_low': 0.4,  # 图像质量评分的低阈值
    'overall_score_threshold_high': 0.6,  # 综合评分的高阈值
    'overall_score_threshold_low': 0.4,  # 综合评分的低阈值

    'brenner_threshold_high': 2500,  # Brenner梯度阈值，用于清晰度检测
    'brenner_threshold_low': 1000,  # Brenner梯度阈值，用于清晰度检测

    'ssim_threshold_high': 80,  # 结构相似性指数（SSIM）的阈值
    'ssim_threshold_low': 50,  # 结构相似性指数（SSIM）的阈值
}

# 默认路径配置
DEFAULT_PATHS = {
    'anomaly_output_dir': "anomaly_images",  # 生成图片的目录
    'input_image_uid': "20250409ckt0000016.jpeg",
    'x_token': ("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJ3ZWIiLCJpc3MiOiJt"
                "YXJzLXBlcm1pc3Npb24tY2VudGVyLXRlc3QiLCJleHAiOjE3NDQ3MDY0MTksImlh"
                "dCI6MTc0NDYyMDAxOSwianRpIjoiZjM5YmIyZTE1MWExNGUwOTg2M2IzNGZkOTli"
                "Yjg2NjciLCJ1c2VybmFtZSI6IjgwMDE1MDExNiJ9.Ye1zf3pjdBE7KPBTOSzwLXhp"
                "bFCL-1JCGs-tc02sS14"),
    'template_image_dir': "data/template",  # 模板图片目录
    'comparison_image_dir': "data/comparision",  # 测试图片目录
    'report_dir': 'report'
}

def get_config():
    """获取默认配置"""
    return DEFAULT_CONFIG.copy()

def get_paths():
    """获取默认路径配置"""
    return DEFAULT_PATHS.copy()

def update_config(custom_config):
    """更新配置参数"""
    config = get_config()
    config.update(custom_config)
    return config

def update_paths(custom_paths):
    """更新路径配置"""
    paths = get_paths()
    paths.update(custom_paths)
    return paths 