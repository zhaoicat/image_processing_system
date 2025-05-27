import glob
import os
from .AnomalyData import generate_anomaly_images
from .ImageHash import is_similar
from .Openai import generate_prompt
from .Opencv1 import calculate_image_quality #2-1
from .Opencv2 import evaluate_fashion_image #2-2
from .Opencv3 import calculate_composite_score
import os
import glob
import datetime

def test_imagehash_algorithm(paths, config):
    all_results = []
    passed_count = 0
    failed_count = 0
    template_image_path = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))[0] if glob.glob(os.path.join(paths['template_image_dir'], '*.jpg')) else glob.glob(os.path.join(paths['template_image_dir'], '*.png'))[0]

    for image_path in glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + glob.glob(os.path.join(paths['comparison_image_dir'], '*.png')):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        image_hash = is_similar(template_image_path, image_path)
        if image_hash['distance'] > config['distance_threshold']:
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count

def test_opencv1_algorithm(paths,config):
    all_results = []
    passed_count = 0
    failed_count = 0
    template_image_path = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))[0] if glob.glob(os.path.join(paths['template_image_dir'], '*.jpg')) else glob.glob(os.path.join(paths['template_image_dir'], '*.png'))[0]

    for image_path in glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + glob.glob(os.path.join(paths['comparison_image_dir'], '*.png')):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        result_quality = calculate_image_quality(image_path)
        if result_quality['color_score'] > config['color_score_threshold_high'] and result_quality['sharpness_score'] > config['sharpness_score_threshold_high'] and result_quality['quality_score'] > config['quality_score_threshold_high'] and result_quality['noise_score'] > config['noise_score_threshold_high']:
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count

def test_opencv2_algorithm(paths,config):
    all_results = []
    passed_count = 0
    failed_count = 0
    template_image_path = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))[0] if glob.glob(os.path.join(paths['template_image_dir'], '*.jpg')) else glob.glob(os.path.join(paths['template_image_dir'], '*.png'))[0]

    for image_path in glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + glob.glob(os.path.join(paths['comparison_image_dir'], '*.png')):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        result_texture = evaluate_fashion_image(template_image_path, image_path)
        if result_texture['texture'] > config['texture_threshold_high'] and result_texture['completeness']>config['completeness_threshold_high'] and result_texture['quality'] > config['quality_score_threshold_high'] and result_texture['overall'] > config['quality_score_threshold_high'] and result_texture['quality_grade'] == 'A':
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count

def test_opencv3_algorithm(paths,config):
    all_results = []
    passed_count = 0
    failed_count = 0
    template_image_path = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))[0] if glob.glob(os.path.join(paths['template_image_dir'], '*.jpg')) else glob.glob(os.path.join(paths['template_image_dir'], '*.png'))[0]

    for image_path in glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + glob.glob(os.path.join(paths['comparison_image_dir'], '*.png')):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
        clarity_result = calculate_composite_score(image_path)
        if clarity_result['raw_scores']['brenner'] > config['brenner_threshold_high'] and clarity_result['raw_scores']['ssim'] > config['ssim_threshold_high']:
            passed_count += 1
        else:
            failed_count += 1
    total_images = len(all_results)
    return total_images, passed_count, failed_count

def test_overall_results(paths,config):
    total_images = 0
    total_passed = 0
    total_failed = 0

    # Accumulate results from each algorithm
    template_image_path = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))[0] if glob.glob(os.path.join(paths['template_image_dir'], '*.jpg')) else glob.glob(os.path.join(paths['template_image_dir'], '*.png'))[0]

    for image_path in glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + glob.glob(os.path.join(paths['comparison_image_dir'], '*.png')):
        image_name = os.path.basename(image_path)
        # Test ImageHash algorithm
        image_hash = is_similar(template_image_path, image_path)
        if image_hash['distance'] > 0:
            total_passed += 1
        else:
            total_failed += 1

        # Test OpenCV1 algorithm
        result_quality = calculate_image_quality(image_path)
        if result_quality['color_score'] > config['color_score_threshold_high'] and result_quality['sharpness_score'] > config['sharpness_score_threshold_high'] and result_quality['quality_score'] > config['quality_score_threshold_high'] and result_quality['noise_score'] > config['noise_score_threshold_high']:
            total_passed += 1
        else:
            total_failed += 1

        # Test OpenCV2 algorithm
        result_texture = evaluate_fashion_image(template_image_path, image_path)
        if result_texture['texture'] > config['texture_threshold_high'] and result_texture['completeness'] > config['completeness_threshold_high'] and result_texture['quality'] > config['quality_score_threshold_high'] and result_texture['overall'] > config['quality_score_threshold_high'] and result_texture['quality_grade'] == 'A':
            total_passed += 1
        else:
            total_failed += 1

        # Test OpenCV3 algorithm
        clarity_result = calculate_composite_score(image_path)
        if clarity_result['raw_scores']['brenner'] > config['brenner_threshold_high'] and clarity_result['raw_scores']['ssim'] > config['ssim_threshold_high']:
            total_passed += 1
        else:
            total_failed += 1

        total_images += 4  # Increment by 4 for each image since there are four tests per image
