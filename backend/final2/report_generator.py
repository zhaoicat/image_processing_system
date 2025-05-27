"""
报告生成器模块
包装原有的HTML报告生成功能，与算法包装器集成
"""

import sys
import os
import glob
import datetime
from tqdm import tqdm

# 添加当前目录到Python路径，支持直接运行
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 简单的绝对导入
from algorithm_wrappers import (
    imagehash_algorithm,
    opencv1_algorithm,
    opencv2_algorithm,
    opencv3_algorithm,
    comprehensive_algorithm
)


def generate_html_report(paths, config, input_choice):
    """
    生成HTML格式的检测报告
    
    Args:
        paths (dict): 路径配置字典
        config (dict): 算法配置参数
        input_choice (str): 功能选择字符串
        
    Returns:
        str: 生成的报告文件路径
    """
    if not paths or not config or not input_choice:
        raise ValueError("路径配置、算法配置和功能选择都不能为空")
    
    # 确保报告目录存在
    os.makedirs(paths['report_dir'], exist_ok=True)
    
    # 查找模板图片
    template_image_path = find_template_image(paths['template_image_dir'])
    print(f"使用模板图片: {template_image_path}")
    
    # 收集所有测试图片
    all_results = collect_test_images(paths['comparison_image_dir'])
    
    # 运行算法并收集结果
    if input_choice == '5':
        input_choice = '1234'  # 综合检测
    
    process_images_with_algorithms(all_results, template_image_path, 
                                 paths['comparison_image_dir'], 
                                 config, input_choice)
    
    # 生成HTML报告
    report_path = generate_combined_report(all_results, config, input_choice, paths)
    
    return report_path


def find_template_image(template_dir):
    """查找模板图片"""
    if not template_dir:
        raise ValueError("模板图片目录不能为空")
    
    # 查找JPG文件
    jpg_files = glob.glob(os.path.join(template_dir, '*.jpg'))
    if jpg_files:
        return jpg_files[0]
    
    # 查找PNG文件
    png_files = glob.glob(os.path.join(template_dir, '*.png'))
    if png_files:
        return png_files[0]
    
    # 查找JPEG文件
    jpeg_files = glob.glob(os.path.join(template_dir, '*.jpeg'))
    if jpeg_files:
        return jpeg_files[0]
    
    raise FileNotFoundError(f"在模板目录 '{template_dir}' 中没有找到任何图片文件")


def collect_test_images(comparison_dir):
    """收集所有测试图片"""
    if not comparison_dir:
        raise ValueError("比较图片目录不能为空")
    
    all_results = []
    image_files = (glob.glob(os.path.join(comparison_dir, '*.jpg')) + 
                  glob.glob(os.path.join(comparison_dir, '*.png')) +
                  glob.glob(os.path.join(comparison_dir, '*.jpeg')))
    
    for image_path in image_files:
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
    
    return all_results


def process_images_with_algorithms(all_results, template_path, comparison_dir, config, input_choice):
    """使用算法处理图片"""
    for i, (image_name, result_group) in tqdm(enumerate(all_results), 
                                            desc='Processing images', 
                                            total=len(all_results)):
        image_path = os.path.join(comparison_dir, image_name)
        
        if '1' in input_choice:
            # ImageHash算法
            hamming_result = imagehash_algorithm(template_path, image_path, config['distance_threshold'])
            result_group.append((1, hamming_result))
        
        if '2' in input_choice:
            # OpenCV1算法
            quality_result = opencv1_algorithm(image_path, (255, 255, 255))
            result_group.append((2, quality_result))
        
        if '3' in input_choice:
            # OpenCV2算法
            fashion_result = opencv2_algorithm(template_path, image_path)
            result_group.append((3, fashion_result))
        
        if '4' in input_choice:
            # OpenCV3算法
            clarity_result = opencv3_algorithm(image_path)
            result_group.append((4, clarity_result))


def generate_combined_report(all_results, config, input_choice, paths):
    """生成综合HTML报告"""
    algorithm_report = generate_algorithm_summary_report(all_results, input_choice, config)
    overall_report = generate_overall_quality_report(all_results, config, input_choice)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 确定报告名称
    report_names = {
        '1': '图像准确度',
        '2': '图像质量',
        '3': '图像纹理',
        '4': '图像清晰度',
        '1234': '综合质量AI检测',
        '5': '综合质量AI检测'
    }
    
    sorted_choice = ''.join(sorted(set(input_choice)))
    
    if sorted_choice in report_names:
        report_name = report_names[sorted_choice]
    else:
        report_name = '+'.join(report_names[char] for char in sorted_choice if char in report_names)
    
    filename = os.path.join(paths['report_dir'], f"{report_name}_{timestamp}.html")
    
    html_content = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
        th {{ background-color: #f2f2f2; }}
        td {{ text-align: center; }}
    </style>
    </head>
    <body>
    <h1 style="text-align: center;">图像质量检测报告</h1>
    {algorithm_report}
    {overall_report}
    </body>
    </html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML报告已生成: {filename}")
    return filename


def generate_algorithm_summary_report(all_results, input_choice, config):
    """生成算法汇总报告"""
    algorithm_summary = {
        'ImageHash': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV1': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV2': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV3': {'total': 0, 'passed': 0, 'failed': 0}
    }
    
    selected_algorithms = []
    
    # 统计各算法结果
    for image_name, result_group in all_results:
        for func_id, result in result_group:
            if func_id == 1 and '1' in input_choice:
                if 'ImageHash' not in selected_algorithms:
                    selected_algorithms.append('ImageHash')
                algorithm_summary['ImageHash']['total'] += 1
                if result['distance'] <= config['distance_threshold']:
                    algorithm_summary['ImageHash']['passed'] += 1
                else:
                    algorithm_summary['ImageHash']['failed'] += 1
            
            elif func_id == 2 and '2' in input_choice:
                if 'OpenCV1' not in selected_algorithms:
                    selected_algorithms.append('OpenCV1')
                algorithm_summary['OpenCV1']['total'] += 1
                if result['quality_score'] >= config['quality_score_threshold_high']:
                    algorithm_summary['OpenCV1']['passed'] += 1
                else:
                    algorithm_summary['OpenCV1']['failed'] += 1
            
            elif func_id == 3 and '3' in input_choice:
                if 'OpenCV2' not in selected_algorithms:
                    selected_algorithms.append('OpenCV2')
                algorithm_summary['OpenCV2']['total'] += 1
                if result['overall'] >= config['quality_score_threshold_high']:
                    algorithm_summary['OpenCV2']['passed'] += 1
                else:
                    algorithm_summary['OpenCV2']['failed'] += 1
            
            elif func_id == 4 and '4' in input_choice:
                if 'OpenCV3' not in selected_algorithms:
                    selected_algorithms.append('OpenCV3')
                algorithm_summary['OpenCV3']['total'] += 1
                if (result['raw_scores']['brenner'] > config['brenner_threshold_high'] and 
                    result['raw_scores']['ssim'] > config['ssim_threshold_high']):
                    algorithm_summary['OpenCV3']['passed'] += 1
                else:
                    algorithm_summary['OpenCV3']['failed'] += 1
    
    # 生成HTML表格
    total_images = sum(algorithm_summary[alg]['total'] for alg in selected_algorithms)
    total_passed = sum(algorithm_summary[alg]['passed'] for alg in selected_algorithms)
    total_failed = sum(algorithm_summary[alg]['failed'] for alg in selected_algorithms)
    
    report_content = """
    <h2 style="text-align: center;">算法测试结果汇总</h2>
    <table>
    <tr>
        <th>算法名称</th>
        <th>检测图片总数</th>
        <th>通过总数</th>
        <th>未通过总数</th>
    </tr>
    """
    
    for algorithm in selected_algorithms:
        summary = algorithm_summary[algorithm]
        report_content += f"""
        <tr>
            <td>{algorithm}</td>
            <td>{summary['total']}</td>
            <td>{summary['passed']}</td>
            <td>{summary['failed']}</td>
        </tr>
        """
    
    report_content += f"""
    <tr style="font-weight: bold;">
        <td>合计</td>
        <td>{total_images}</td>
        <td>{total_passed}</td>
        <td>{total_failed}</td>
    </tr>
    """
    report_content += "</table>\n"
    return report_content


def generate_overall_quality_report(all_results, config, input_choice):
    """生成详细质量报告"""
    report_content = """
    <h2 style="text-align: center;">详细质量检测报告</h2>
    <table>
    <tr>
        <th>图片名称</th>
        <th>检测算法</th>
        <th>评估维度</th>
        <th>评估分数</th>
        <th>评估结果</th>
        <th>是否通过</th>
    </tr>
    """
    
    for image_name, result_group in all_results:
        for func_id, result in result_group:
            if func_id == 1 and '1' in input_choice:
                # ImageHash算法结果
                passed = "是" if result['distance'] <= config['distance_threshold'] else "否"
                report_content += f"""
                <tr>
                    <td>{image_name}</td>
                    <td>ImageHash算法</td>
                    <td>汉明距离</td>
                    <td>{result['distance']}</td>
                    <td>{'相似' if result['similar'] else '不相似'}</td>
                    <td>{passed}</td>
                </tr>
                """
            
            elif func_id == 2 and '2' in input_choice:
                # OpenCV1算法结果
                passed = "是" if result['quality_score'] >= config['quality_score_threshold_high'] else "否"
                report_content += f"""
                <tr>
                    <td rowspan="4">{image_name}</td>
                    <td rowspan="4">OpenCV1算法</td>
                    <td>颜色匹配度</td>
                    <td>{result['color_score']:.3f}</td>
                    <td>{'优' if result['color_score'] >= 0.8 else '良' if result['color_score'] >= 0.6 else '中' if result['color_score'] >= 0.4 else '差'}</td>
                    <td rowspan="4">{passed}</td>
                </tr>
                <tr>
                    <td>清晰度</td>
                    <td>{result['sharpness_score']:.3f}</td>
                    <td>{'优' if result['sharpness_score'] >= 0.8 else '良' if result['sharpness_score'] >= 0.6 else '中' if result['sharpness_score'] >= 0.4 else '差'}</td>
                </tr>
                <tr>
                    <td>噪声水平</td>
                    <td>{result['noise_score']:.3f}</td>
                    <td>{'高' if result['noise_score'] >= 0.8 else '中' if result['noise_score'] >= 0.4 else '低'}</td>
                </tr>
                <tr>
                    <td>综合质量</td>
                    <td>{result['quality_score']:.3f}</td>
                    <td>{'优' if result['quality_score'] >= 0.8 else '良' if result['quality_score'] >= 0.6 else '中' if result['quality_score'] >= 0.4 else '差'}</td>
                </tr>
                """
            
            elif func_id == 3 and '3' in input_choice:
                # OpenCV2算法结果
                passed = "是" if result['overall'] >= config['quality_score_threshold_high'] else "否"
                report_content += f"""
                <tr>
                    <td rowspan="4">{image_name}</td>
                    <td rowspan="4">OpenCV2算法</td>
                    <td>纹理复杂度</td>
                    <td>{result['texture']:.3f}</td>
                    <td>{'高' if result['texture'] >= 0.8 else '中' if result['texture'] >= 0.4 else '低'}</td>
                    <td rowspan="4">{passed}</td>
                </tr>
                <tr>
                    <td>元素完整性</td>
                    <td>{result['completeness']:.3f}</td>
                    <td>{'完整' if result['completeness'] >= 0.8 else '较完整' if result['completeness'] >= 0.6 else '一般' if result['completeness'] >= 0.4 else '不完整'}</td>
                </tr>
                <tr>
                    <td>画面质量</td>
                    <td>{result['quality']:.3f}</td>
                    <td>{'优' if result['quality'] >= 0.8 else '良' if result['quality'] >= 0.6 else '中' if result['quality'] >= 0.4 else '差'}</td>
                </tr>
                <tr>
                    <td>质量等级</td>
                    <td>{result['quality_grade']}</td>
                    <td>{result['quality_grade']}级</td>
                </tr>
                """
            
            elif func_id == 4 and '4' in input_choice:
                # OpenCV3算法结果
                brenner_passed = result['raw_scores']['brenner'] > config['brenner_threshold_high']
                ssim_passed = result['raw_scores']['ssim'] > config['ssim_threshold_high']
                passed = "是" if brenner_passed and ssim_passed else "否"
                
                report_content += f"""
                <tr>
                    <td rowspan="2">{image_name}</td>
                    <td rowspan="2">OpenCV3算法</td>
                    <td>Brenner梯度</td>
                    <td>{result['raw_scores']['brenner']:.2f}</td>
                    <td>{'优' if result['raw_scores']['brenner'] > config['brenner_threshold_high'] else '中' if result['raw_scores']['brenner'] >= config['brenner_threshold_low'] else '差'}</td>
                    <td rowspan="2">{passed}</td>
                </tr>
                <tr>
                    <td>SSIM对比度</td>
                    <td>{result['raw_scores']['ssim']:.2f}</td>
                    <td>{'优' if result['raw_scores']['ssim'] > config['ssim_threshold_high'] else '中' if result['raw_scores']['ssim'] >= config['ssim_threshold_low'] else '差'}</td>
                </tr>
                """
    
    report_content += "</table>\n"
    return report_content


def quick_report_generation(template_dir, comparison_dir, report_dir, algorithms="1234"):
    """
    快速生成报告的便捷函数
    
    Args:
        template_dir (str): 模板图片目录
        comparison_dir (str): 比较图片目录  
        report_dir (str): 报告输出目录
        algorithms (str): 要运行的算法，默认"1234"表示全部
        
    Returns:
        str: 生成的报告文件路径
    """
    paths = {
        'template_image_dir': template_dir,
        'comparison_image_dir': comparison_dir,
        'report_dir': report_dir
    }
    
    # 使用统一的配置
    from .config import get_config
    config = get_config()
    
    return generate_html_report(paths, config, algorithms) 