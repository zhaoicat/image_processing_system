import os
import glob
import logging

# 简化的导入方式 - 直接使用相对导入
from .ImageHash import is_similar
from .Opencv1 import calculate_image_quality
from .Opencv2 import evaluate_fashion_image
from .Opencv3 import calculate_composite_score

# 创建logger
logger = logging.getLogger(__name__)


def test_imagehash_algorithm(paths, config):
    all_results = []
    passed_count = 0
    failed_count = 0
    
    # 安全获取模板图片
    jpg_templates = glob.glob(os.path.join(
        paths['template_image_dir'], '*.jpg'))
    png_templates = glob.glob(os.path.join(
        paths['template_image_dir'], '*.png'))
    
    # 尝试获取模板图片路径
    template_image_path = None
    if jpg_templates:
        template_image_path = jpg_templates[0]
    elif png_templates:
        template_image_path = png_templates[0]
    
    # 如果没有找到模板图片，尝试从比较目录获取
    if template_image_path is None:
        jpg_comparisons = glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg'))
        png_comparisons = glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.png'))
        
        if jpg_comparisons:
            template_image_path = jpg_comparisons[0]
            logger.warning(
                "模板目录中没有图片，使用比较目录中的第一张JPG图片作为模板: %s",
                template_image_path
            )
        elif png_comparisons:
            template_image_path = png_comparisons[0]
            logger.warning(
                "模板目录中没有图片，使用比较目录中的第一张PNG图片作为模板: %s",
                template_image_path
            )
    
    # 如果仍然没有找到模板图片，返回默认结果
    if template_image_path is None:
        logger.error("无法找到任何模板图片，无法执行ImageHash算法测试")
        return 0, 0, 0

    for image_path in (glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg')) + 
                      glob.glob(os.path.join(
                          paths['comparison_image_dir'], '*.png'))):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        image_hash = is_similar(template_image_path, image_path)
        if image_hash['distance'] > config['distance_threshold']:
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count


def test_opencv1_algorithm(paths, config):
    all_results = []
    passed_count = 0
    failed_count = 0
    
    # OpenCV1算法不需要模板图片，可以直接处理

    for image_path in (glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg')) + 
                      glob.glob(os.path.join(
                          paths['comparison_image_dir'], '*.png'))):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        result_quality = calculate_image_quality(image_path)
        
        # 简化条件判断
        color_ok = (result_quality['color_score'] > 
                    config['color_score_threshold_high'])
        sharpness_ok = (result_quality['sharpness_score'] > 
                        config['sharpness_score_threshold_high'])
        quality_ok = (result_quality['quality_score'] > 
                      config['quality_score_threshold_high'])
        noise_ok = (result_quality['noise_score'] > 
                    config['noise_score_threshold_high'])
        
        conditions = [color_ok, sharpness_ok, quality_ok, noise_ok]
        
        if all(conditions):
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count


def test_opencv2_algorithm(paths, config):
    all_results = []
    passed_count = 0
    failed_count = 0
    
    # 安全获取模板图片
    jpg_templates = glob.glob(os.path.join(
        paths['template_image_dir'], '*.jpg'))
    png_templates = glob.glob(os.path.join(
        paths['template_image_dir'], '*.png'))
    
    # 尝试获取模板图片路径
    template_image_path = None
    if jpg_templates:
        template_image_path = jpg_templates[0]
    elif png_templates:
        template_image_path = png_templates[0]
    
    # 如果没有找到模板图片，尝试从比较目录获取
    if template_image_path is None:
        jpg_comparisons = glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg'))
        png_comparisons = glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.png'))
        
        if jpg_comparisons:
            template_image_path = jpg_comparisons[0]
            logger.warning(
                "模板目录中没有图片，使用比较目录中的第一张JPG图片作为模板: %s",
                template_image_path
            )
        elif png_comparisons:
            template_image_path = png_comparisons[0]
            logger.warning(
                "模板目录中没有图片，使用比较目录中的第一张PNG图片作为模板: %s",
                template_image_path
            )
    
    # 如果仍然没有找到模板图片，返回默认结果
    if template_image_path is None:
        logger.error("无法找到任何模板图片，无法执行纹理质量评估算法测试")
        return 0, 0, 0

    for image_path in (glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg')) + 
                      glob.glob(os.path.join(
                          paths['comparison_image_dir'], '*.png'))):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        result_texture = evaluate_fashion_image(
            template_image_path, image_path)
        
        # 简化条件判断
        texture_ok = (result_texture['texture'] >
                      config['texture_threshold_high'])
        completeness_ok = (result_texture['completeness'] >
                           config['completeness_threshold_high'])
        quality_ok = (result_texture['quality'] >
                      config['quality_score_threshold_high'])
        overall_ok = (result_texture['overall'] >
                      config['quality_score_threshold_high'])
        
        conditions = [texture_ok, completeness_ok, quality_ok, overall_ok]
        
        if all(conditions):
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count


def test_opencv3_algorithm(paths, config):
    all_results = []
    passed_count = 0
    failed_count = 0
    
    # OpenCV3算法不需要模板图片，可以直接处理

    for image_path in (glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg')) + 
                      glob.glob(os.path.join(
                          paths['comparison_image_dir'], '*.png'))):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        clarity_result = calculate_composite_score(image_path)
        
        # 简化条件判断
        brenner_ok = (clarity_result['raw_scores']['brenner'] >
                      config['brenner_threshold_high'])
        ssim_ok = (clarity_result['raw_scores']['ssim'] >
                   config['ssim_threshold_high'])
        
        conditions = [brenner_ok, ssim_ok]
        
        if all(conditions):
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count


def test_overall_results(paths, config):
    total_images = 0
    total_passed = 0
    total_failed = 0

    # 安全获取模板图片
    jpg_templates = glob.glob(os.path.join(
        paths['template_image_dir'], '*.jpg'))
    png_templates = glob.glob(os.path.join(
        paths['template_image_dir'], '*.png'))
    
    # 尝试获取模板图片路径
    template_image_path = None
    if jpg_templates:
        template_image_path = jpg_templates[0]
    elif png_templates:
        template_image_path = png_templates[0]
    
    # 如果没有找到模板图片，尝试从比较目录获取
    if template_image_path is None:
        jpg_comparisons = glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg'))
        png_comparisons = glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.png'))
        
        if jpg_comparisons:
            template_image_path = jpg_comparisons[0]
            logger.warning(
                "模板目录中没有图片，使用比较目录中的第一张JPG图片作为模板: %s",
                template_image_path
            )
        elif png_comparisons:
            template_image_path = png_comparisons[0]
            logger.warning(
                "模板目录中没有图片，使用比较目录中的第一张PNG图片作为模板: %s",
                template_image_path
            )
    
    # 如果仍然没有找到模板图片，返回默认结果
    if template_image_path is None:
        logger.error("无法找到任何模板图片，无法执行整体测试")
        return 0, 0, 0

    for image_path in (glob.glob(os.path.join(
            paths['comparison_image_dir'], '*.jpg')) + 
                      glob.glob(os.path.join(
                          paths['comparison_image_dir'], '*.png'))):
        # Test ImageHash algorithm
        image_hash = is_similar(template_image_path, image_path)
        if image_hash['distance'] > 0:
            total_passed += 1
        else:
            total_failed += 1

        # Test OpenCV1 algorithm
        result_quality = calculate_image_quality(image_path)
        color_ok = (result_quality['color_score'] > 
                    config['color_score_threshold_high'])
        sharpness_ok = (result_quality['sharpness_score'] > 
                        config['sharpness_score_threshold_high'])
        quality_ok = (result_quality['quality_score'] > 
                      config['quality_score_threshold_high'])
        noise_ok = (result_quality['noise_score'] > 
                    config['noise_score_threshold_high'])
        
        quality_conditions = [color_ok, sharpness_ok, quality_ok, noise_ok]
        
        if all(quality_conditions):
            total_passed += 1
        else:
            total_failed += 1

        # Test OpenCV2 algorithm
        result_texture = evaluate_fashion_image(
            template_image_path, image_path)
        texture_ok = (result_texture['texture'] >
                      config['texture_threshold_high'])
        completeness_ok = (result_texture['completeness'] >
                           config['completeness_threshold_high'])
        tex_quality_ok = (result_texture['quality'] >
                          config['quality_score_threshold_high'])
        overall_ok = (result_texture['overall'] >
                      config['quality_score_threshold_high'])
        grade_ok = result_texture['quality_grade'] == 'A'
        
        texture_conditions = [
            texture_ok, completeness_ok, tex_quality_ok, overall_ok, grade_ok
        ]
        
        if all(texture_conditions):
            total_passed += 1
        else:
            total_failed += 1

        # Test OpenCV3 algorithm
        clarity_result = calculate_composite_score(image_path)
        brenner_ok = (clarity_result['raw_scores']['brenner'] >
                      config['brenner_threshold_high'])
        ssim_ok = (clarity_result['raw_scores']['ssim'] >
                   config['ssim_threshold_high'])
        
        clarity_conditions = [brenner_ok, ssim_ok]
        
        if all(clarity_conditions):
            total_passed += 1
        else:
            total_failed += 1

        # Increment by 4 for each image since there are four tests per image
        total_images += 4
    
    return total_images, total_passed, total_failed

