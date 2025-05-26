"""
utils.py - 图像处理工具函数

提供评估和报告生成等辅助功能
"""

import logging
import os
import glob
import datetime
from tqdm import tqdm

# 简化的导入方式 - 直接使用相对导入
from .algorithm.AnomalyData import generate_anomaly_images
from .algorithm.ImageHash import is_similar
from .algorithm.Openai import generate_prompt
from .algorithm.Opencv1 import calculate_image_quality
from .algorithm.Opencv2 import evaluate_fashion_image
from .algorithm.Opencv3 import calculate_composite_score
from .algorithm.evaluation import (
    test_imagehash_algorithm,
    test_opencv1_algorithm,
    test_opencv2_algorithm,
    test_opencv3_algorithm
)

# 创建logger
logger = logging.getLogger(__name__)


def generate_overall_quality_report(all_results, config, input_choice, paths):
    report_content = """
    <h1 style=\"text-align: center;\">综合质量检测报告</h1>
    <table>
    <tr>
        <th>图片名称</th>
        <th>质量检测名称</th>
        <th>评估维度</th>
        <th>评估分数</th>
        <th>评估结果</th>
        <th>预期分数</th>
        <th>是否人工干预</th>
        <th>检测初始值</th>
        <th>质量预测区间建议</th>
    </tr>
    """

    rowspan_map = {1: 1, 2: 3, 3: 3, 4: 2}

    for image_name, result_group in all_results:
        total_rowspan = sum(rowspan_map[func_id] for func_id, _ in result_group if str(func_id) in input_choice)
        first_func_id = True
        for i, (func_id, result) in enumerate(result_group):
            if str(func_id) in input_choice:
                if first_func_id:
                    image_name_cell = f"<td rowspan='{total_rowspan}'>{image_name}</td>"
                    first_func_id = False
                else:
                    image_name_cell = "<td style='display: none;'></td>"

                if func_id == 1:
                    if isinstance(result, dict) and 'distance' in result:
                        result_text = f"""
                                        <tr>
                                            {image_name_cell}
                                            <td rowspan='1'>图像准确度AI检测【ImageHash算法】</td>
                                            <td>汉明距离</td>
                                            <td>{result['distance']}</td>
                                            <td>{'图像差异显著' if result['distance'] > config['distance_threshold'] else '图像高度相似或重复'}</td>
                                            <td>>0</td>
                                            <td>{'否' if result['distance'] > config['distance_threshold'] else '是'}</td>
                                            <td></td>
                                            <td></td>
                                        </tr>
                                        """
                        report_content += result_text
                elif func_id == 2:

                    if isinstance(result, dict) and 'color_score' in result:

                        result_text = f"""
                                        <tr>
                                            {image_name_cell}
                                            <td rowspan='3'>图像质量AI检测【opencv算法1】</td>
                                            <td>颜色匹配度（目标白色差异）</td>
                                            <td>{result['initial_color_diff']}</td>
                                            <td>{'差' if result['initial_color_diff'] >= config['color_score_threshold_high'] else '高' if result['initial_color_diff'] <= config['color_score_threshold_low'] else '一般'}</td>
                                            <td><20</td>
                                            <td>{'否' if result['initial_color_diff'] >= config['color_score_threshold_high'] else '是'}</td>
                                            <td>{result['initial_color_diff']}</td>
                                            <td>颜色匹配度（目标白色差异）：<20为高,20<=欧氏距离<=50一般,>50差</td>
                                        </tr>
                                        <tr>
                                            <td>清晰度（拉普拉斯方差）</td>
                                            <td>{result['initial_laplacian_var']}</td>
                                            <td>{'清晰' if result['initial_laplacian_var'] >= config['sharpness_score_threshold_high'] else '模糊' if result['initial_laplacian_var'] <= config['sharpness_score_threshold_low'] else '一般'}</td>
                                            <td>>100</td>
                                            <td>{'否' if result['initial_laplacian_var'] >= config['sharpness_score_threshold_high'] else '是'}</td>
                                            <td>{result['initial_laplacian_var']}</td>
                                            <td>清晰度（拉普拉斯方差）：方差>100(越高越清晰),30<方差<=100中等,<=30差</td>
                                        </tr>
                                        <tr>
                                            <td>噪声水平（灰度标准差）</td>
                                            <td>{result['initial_noise_level']}</td>
                                            <td>{'优秀' if result['initial_noise_level'] < config['noise_score_threshold_low'] else '差' if result['initial_noise_level'] > config['noise_score_threshold_high'] else '中'}</td>
                                            <td><30</td>
                                            <td>{'否' if result['initial_noise_level'] >= config['noise_score_threshold_high'] else '是'}</td>
                                            <td>{result['initial_noise_level']}</td>
                                            <td>噪声水平（灰度标准差）：<30为好,30>=Z>=50为中,>50差</td>
                                        </tr>
                                        <!--
                                        <tr>
                                            <td>综合质量</td>
                                            <td>{result['quality_score']}</td>
                                            <td>{'优秀' if result['quality_score'] >= config['quality_score_threshold_high'] else '可用' if result['quality_score'] <= config['quality_score_threshold_high'] else '差'}</td>
                                            <td>>0.6</td>
                                            <td>{'否' if result['quality_score'] >= config['quality_score_threshold_high'] else '是'}</td>
                                            <td></td>
                                            <td></td>
                                        </tr>
                                        -->
                                        """
                        report_content += result_text
                elif func_id == 3:

                    if isinstance(result, dict) and 'texture' in result:
     
                        result_text = f"""
                                        <tr>
                                            {image_name_cell}
                                            <td rowspan='3'>图像纹理质量AI检测【opencv算法2】</td>
                                            <td>纹理复杂度</td>
                                            <td>{result['texture']}</td>
                                            <td>{'优秀' if result['texture'] >= config['texture_threshold_high'] else '中' if result['texture'] <= config['texture_threshold_low'] else '差'}</td>
                                            <td>>0.6</td>
                                            <td>{'否' if result['texture'] >= config['texture_threshold_high'] else '是'}</td>
                                            <td></td>
                                            <td></td>
                                        </tr>
                                        <tr>
                                            <td>元素完整性</td>
                                            <td>{result['completeness']}</td>
                                            <td>{'完整' if result['completeness'] >= config['completeness_threshold_high'] else '一般' if result['completeness'] <= config['completeness_threshold_low'] else '不完整'}</td>
                                            <td>>0.6</td>
                                            <td>{'否' if result['completeness'] >= config['completeness_threshold_high'] else '是'}</td>
                                            <td></td>
                                            <td></td>
                                        </tr>
                                        <tr>
                                            <td>画面质量</td>
                                            <td>{result['quality']}</td>
                                            <td>{'优秀' if result['quality'] >= config['quality_score_threshold_high'] else '可用' if result['quality'] <= config['quality_score_threshold_low'] else '差'}</td>
                                            <td>>0.6</td>
                                            <td>{'否' if result['quality'] >= config['quality_score_threshold_high'] else '是'}</td>
                                            <td></td>
                                            <td></td>
                                        </tr>
                                        <!--
                                        <tr>
                                            <td>综合评分</td>
                                            <td>{result['overall']}</td>
                                            <td>{'优秀' if result['overall'] >= config['overall_score_threshold_high'] else '一般' if result['overall'] <= config['overall_score_threshold_low'] else '差'}</td>
                                            <td>>0.6</td>
                                            <td>{'否' if result['overall'] >= config['overall_score_threshold_high'] else '是'}</td>
                                            <td></td>
                                            <td></td>
                                        </tr>
                                        -->
                                        
                                        """
                        report_content += result_text
                elif func_id == 4:

                    if isinstance(result, dict) and 'composite' in result:
    
                        # Map Brenner score to weighted value using linear interpolation
                        if result['raw_scores']['brenner'] < 1000:
                            brenner_weighted = result['raw_scores']['brenner'] / 2500 * 0.4
                        elif result['raw_scores']['brenner'] <= 2500:
                            brenner_weighted = 0.4 + (result['raw_scores']['brenner'] - 1000) / 1500 * 0.2
                        else:
                            brenner_weighted = 0.6 + (result['raw_scores']['brenner'] - 2500) / 500 * 0.4

                        # Map SSIM score to weighted value using linear interpolation
                        if result['raw_scores']['ssim'] < 50:
                            ssim_weighted = result['raw_scores']['ssim'] / 80 * 0.4
                        elif result['raw_scores']['ssim'] <= 80:
                            ssim_weighted = 0.4 + (result['raw_scores']['ssim'] - 50) / 30 * 0.2
                        else:
                            ssim_weighted = 0.6 + (result['raw_scores']['ssim'] - 80) / 20 * 0.4

                        result_text = f"""
                            <tr>
                                {image_name_cell}
                                <td rowspan='2'>图像清晰度AI检测【opencv算法3+ScikitImage算法】</td>
                                <td rowspan='1'>Brenner算法</td>
                                <td>{result['raw_scores']['brenner']} </td>
                                <td>{'优秀' if result['raw_scores']['brenner'] > config['brenner_threshold_high'] else '一般' if result['raw_scores']['brenner'] >= config['brenner_threshold_low'] else '差'}</td>
                                <td>>2500</td>
                                <td>{'否' if result['raw_scores']['brenner'] > config['brenner_threshold_high'] else '是'}</td>
                                
                                <td>{result['initial_brenner']}</td>
                                <td>>2500为优，2500>=B>=1000为一般，<1000为差</td>
                            </tr>
                            <tr>    
                                <td rowspan='1'>SSIM对比度</td>
                                <td>{result['raw_scores']['ssim']}</td>
                                <td>{'优秀' if result['raw_scores']['ssim'] > config['ssim_threshold_high'] else '差' if result['raw_scores']['ssim'] < config['ssim_threshold_low'] else '一般'}</td>
                                <td>>80</td>
                                <td>{'否' if result['raw_scores']['ssim'] > config['ssim_threshold_high'] else '是'}</td>
                                
                                <td>{result['initial_ssim']}</td>
                                <td>>80为优，50<=S<=80为一般，<50为差</td>
                            </tr>
                            """
                        report_content += result_text

    report_content += "</table>\n"
    return report_content


def generate_algorithm_summary_report(paths, input_choice,config):
    algorithm_summary = {
        'ImageHash': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV1': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV2': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV3': {'total': 0, 'passed': 0, 'failed': 0}
    }
    selected_algorithms = []
    
    # 检查报告目录是否是task_xxx/img_x格式的子目录结构
    is_parent_task = False
    task_dir = os.path.basename(paths['report_dir'])
    if task_dir.startswith('task_') and not 'img_' in task_dir:
        logger.info("检测到主任务目录: %s，开始扫描子目录报告...", task_dir)
        is_parent_task = True
        
    if is_parent_task:
        # 统计方法1: 统计所有子任务目录的结果总和
        img_dirs = glob.glob(os.path.join(paths['report_dir'], 'img_*'))
        logger.info("找到 %s 个子目录", len(img_dirs))
        
        if img_dirs:
            # 有子目录，需要递归统计所有子目录中的图片数量
            sub_results = {'ImageHash': {'total': 0, 'passed': 0, 'failed': 0},
                          'OpenCV1': {'total': 0, 'passed': 0, 'failed': 0},
                          'OpenCV2': {'total': 0, 'passed': 0, 'failed': 0},
                          'OpenCV3': {'total': 0, 'passed': 0, 'failed': 0}}
            
            for img_dir in img_dirs:
                # 创建子任务的paths
                sub_paths = paths.copy()
                sub_task_dir = os.path.join(img_dir, os.path.basename(task_dir) + '_' + os.path.basename(img_dir))
                
                if os.path.exists(sub_task_dir):
                    sub_paths['report_dir'] = sub_task_dir
                    img_name = os.path.basename(img_dir)
                    logger.info("处理子目录 %s 中的报告...", img_name)
                    
                    # 获取此子目录的统计数据
                    if '1' in input_choice:
                        sub_total, sub_passed, sub_failed = test_imagehash_algorithm(sub_paths, config)
                        sub_results['ImageHash']['total'] += sub_total
                        sub_results['ImageHash']['passed'] += sub_passed
                        sub_results['ImageHash']['failed'] += sub_failed
                        if 'ImageHash' not in selected_algorithms:
                            selected_algorithms.append('ImageHash')
                    
                    if '2' in input_choice:
                        sub_total, sub_passed, sub_failed = test_opencv1_algorithm(sub_paths, config)
                        sub_results['OpenCV1']['total'] += sub_total
                        sub_results['OpenCV1']['passed'] += sub_passed
                        sub_results['OpenCV1']['failed'] += sub_failed
                        if 'OpenCV1' not in selected_algorithms:
                            selected_algorithms.append('OpenCV1')
                    
                    if '3' in input_choice:
                        sub_total, sub_passed, sub_failed = test_opencv2_algorithm(sub_paths, config)
                        sub_results['OpenCV2']['total'] += sub_total
                        sub_results['OpenCV2']['passed'] += sub_passed
                        sub_results['OpenCV2']['failed'] += sub_failed
                        if 'OpenCV2' not in selected_algorithms:
                            selected_algorithms.append('OpenCV2')
                    
                    if '4' in input_choice:
                        sub_total, sub_passed, sub_failed = test_opencv3_algorithm(sub_paths, config)
                        sub_results['OpenCV3']['total'] += sub_total
                        sub_results['OpenCV3']['passed'] += sub_passed
                        sub_results['OpenCV3']['failed'] += sub_failed
                        if 'OpenCV3' not in selected_algorithms:
                            selected_algorithms.append('OpenCV3')
            
            # 使用子目录汇总的结果
            algorithm_summary = sub_results
        else:
            # 没有子目录，使用标准处理方法
            if '1' in input_choice:
                algorithm_summary['ImageHash']['total'], algorithm_summary['ImageHash']['passed'], algorithm_summary['ImageHash']['failed'] = test_imagehash_algorithm(paths,config)
                selected_algorithms.append('ImageHash')
            if '2' in input_choice:
                algorithm_summary['OpenCV1']['total'], algorithm_summary['OpenCV1']['passed'], algorithm_summary['OpenCV1']['failed'] = test_opencv1_algorithm(paths,config)
                selected_algorithms.append('OpenCV1')
            if '3' in input_choice:
                algorithm_summary['OpenCV2']['total'], algorithm_summary['OpenCV2']['passed'], algorithm_summary['OpenCV2']['failed'] = test_opencv2_algorithm(paths,config)
                selected_algorithms.append('OpenCV2')
            if '4' in input_choice:
                algorithm_summary['OpenCV3']['total'], algorithm_summary['OpenCV3']['passed'], algorithm_summary['OpenCV3']['failed'] = test_opencv3_algorithm(paths,config)
                selected_algorithms.append('OpenCV3')
    else:
        # 标准处理方法（单一子目录）
        if '1' in input_choice:
            algorithm_summary['ImageHash']['total'], algorithm_summary['ImageHash']['passed'], algorithm_summary['ImageHash']['failed'] = test_imagehash_algorithm(paths,config)
            selected_algorithms.append('ImageHash')
        if '2' in input_choice:
            algorithm_summary['OpenCV1']['total'], algorithm_summary['OpenCV1']['passed'], algorithm_summary['OpenCV1']['failed'] = test_opencv1_algorithm(paths,config)
            selected_algorithms.append('OpenCV1')
        if '3' in input_choice:
            algorithm_summary['OpenCV2']['total'], algorithm_summary['OpenCV2']['passed'], algorithm_summary['OpenCV2']['failed'] = test_opencv2_algorithm(paths,config)
            selected_algorithms.append('OpenCV2')
        if '4' in input_choice:
            algorithm_summary['OpenCV3']['total'], algorithm_summary['OpenCV3']['passed'], algorithm_summary['OpenCV3']['failed'] = test_opencv3_algorithm(paths,config)
            selected_algorithms.append('OpenCV3')
    
    # 计算实际的唯一图片数量（使用一个算法的图片数量，而不是所有算法的总和）
    # 假设每个算法都处理了相同的图片集
    if selected_algorithms:
        # 获取第一个算法的图片数量作为实际图片数量
        total_images = algorithm_summary[selected_algorithms[0]]['total']
    else:
        total_images = 0
    total_passed = sum(algorithm_summary[alg]['passed'] for alg in selected_algorithms)
    total_failed = sum(algorithm_summary[alg]['failed'] for alg in selected_algorithms)
    
    report_content = """
    <h1 style=\"text-align: center;\">算法测试结果报告</h1>
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
    <tr>
        <td>合计</td>
        <td>{total_images}</td>
        <td>{total_passed}</td>
        <td>{total_failed}</td>
    </tr>
    """
    report_content += "</table>\n"
    return report_content

def generate_combined_report(all_results, config, input_choice, paths):
    algorithm_report = generate_algorithm_summary_report(paths, input_choice, config)
    overall_report = generate_overall_quality_report(all_results, config, input_choice, paths)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Determine the filename based on input_choice
    report_names = {
        '1': '图像准确度',
        '2': '图像质量',
        '3': '图像纹理',
        '4': '图像清晰度',
        '1234': '综合质量AI检测',
        '5': '综合质量AI检测'
    }
    
    # Create a sorted list of unique characters in input_choice
    sorted_choice = ''.join(sorted(set(input_choice)))
    
    # Generate the filename based on the sorted choice
    if sorted_choice in report_names:
        report_name = report_names[sorted_choice]
    else:
        report_name = '+'.join(report_names[char] for char in sorted_choice if char in report_names)
    
    filename = os.path.join(paths['report_dir'], f"{report_name}_{timestamp}.html")
    
    html_content = f"""
    <html>
    <head>
    <meta charset=\"UTF-8\">
    <style>
        body {{ font-family: Arial, sans-serif; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
        th {{ background-color: #f2f2f2; }}
        td {{ text-align: center; }}
    </style>
    </head>
    <body>
    <h1 style=\"text-align: center;\"></h1>
    {algorithm_report}
    {overall_report}
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info("Combined report generated: %s", filename)



def evaluation(paths, config, input_choice):
    all_results = []
    
    # 安全获取模板图片，检查是否存在
    jpg_templates = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))
    png_templates = glob.glob(os.path.join(paths['template_image_dir'], '*.png'))
    
    template_image_path = None
    
    # 尝试从模板目录获取图片
    if jpg_templates:
        template_image_path = jpg_templates[0]
        logger.info("使用模板目录中的JPG图片: %s", template_image_path)
    elif png_templates:
        template_image_path = png_templates[0]
        logger.info("使用模板目录中的PNG图片: %s", template_image_path)
    
    # 如果模板目录没有图片，尝试使用比较目录中的第一张图片作为模板
    if template_image_path is None:
        jpg_comparisons = glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg'))
        png_comparisons = glob.glob(os.path.join(paths['comparison_image_dir'], '*.png'))
        
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
        else:
            # 如果比较目录也没有图片，则显示错误并根据情况跳过需要模板的算法
            logger.error(
                "无法找到任何模板图片。模板目录和比较目录都没有JPG或PNG图片。"
            )
            if '1' in input_choice or '3' in input_choice:
                logger.warning(
                    "算法选择中包含需要模板图片的算法(1,3)，但找不到模板图片。这些算法将被跳过。"
                )
    
    # 获取所有比较图片 - 优先使用paths['all_image_paths']
    if 'all_image_paths' in paths and paths['all_image_paths']:
        comparison_images = paths['all_image_paths']
        logger.info("使用指定的图片列表，共有 %s 张图片", len(comparison_images))
    else:
        # 回退到传统方式：从目录获取图片
        comparison_images = (
            glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + 
            glob.glob(os.path.join(paths['comparison_image_dir'], '*.png'))
        )
    
    # 确保有图片需要处理
    if not comparison_images:
        logger.error("没有图片可以处理。")
        return  # 如果没有图片，直接返回
    
    # 为每个图片创建结果存储
    for image_path in tqdm(comparison_images, desc='Processing images'):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
    
    # 记录每个算法是否执行成功
    algorithm_success = {'1': False, '2': False, '3': False, '4': False}
    
    # 如果是综合模式，执行所有可能的算法
    if input_choice == '5':
        actual_input_choice = '1234'
    else:
        actual_input_choice = input_choice
    
    # 单独执行每个算法，捕获每个算法可能的异常
    for algorithm in actual_input_choice:
        if algorithm not in '1234':
            continue
            
        logger.info("开始执行算法 %s", algorithm)
        
        try:
            # 算法1和3需要模板图片
            if (algorithm in '13') and not template_image_path:
                logger.info("跳过算法 %s，因为没有找到有效的模板图片", algorithm)
                continue
                
            for i, (image_name, result_group) in tqdm(
                enumerate(all_results), 
                desc=f'执行算法 {algorithm}', 
                total=len(all_results)
            ):
                # 获取完整图片路径
                image_path = os.path.join(paths['comparison_image_dir'], image_name)
                # 如果图片路径是完整路径，直接使用
                if os.path.exists(image_name):
                    image_path = image_name
                elif not os.path.exists(image_path):
                    # 尝试查找完整路径
                    for full_path in comparison_images:
                        if os.path.basename(full_path) == image_name:
                            image_path = full_path
                            break
                
                # 根据算法选择执行相应的处理函数
                if algorithm == '1' and template_image_path:
                    hamming = is_similar(template_image_path, image_path)
                    result_group.append((1, hamming))
                elif algorithm == '2':
                    result_quality = calculate_image_quality(image_path)
                    result_group.append((2, result_quality))
                elif algorithm == '3' and template_image_path:
                    result_fashion = evaluate_fashion_image(template_image_path, image_path)
                    result_group.append((3, result_fashion))
                elif algorithm == '4':
                    clarity_result = calculate_composite_score(image_path)
                    result_group.append((4, clarity_result))
            
            # 标记算法执行成功
            algorithm_success[algorithm] = True
            logger.info("算法 %s 执行成功", algorithm)
            
            # 为每个算法单独生成报告
            # 构建只包含当前算法的输入选择
            single_algorithm_choice = algorithm
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 生成单算法报告
            try:
                filtered_results = []
                for image_name, result_group in all_results:
                    filtered_group = [(func_id, result) for func_id, result in result_group 
                                    if str(func_id) == algorithm]
                    if filtered_group:  # 只添加有结果的图片
                        filtered_results.append((image_name, filtered_group))
                        
                if filtered_results:
                    algorithm_report = generate_algorithm_summary_report(
                        paths, single_algorithm_choice, config)
                    overall_report = generate_overall_quality_report(
                        filtered_results, config, single_algorithm_choice, paths)
                    
                    # 确定报告文件名
                    report_names = {
                        '1': '图像准确度',
                        '2': '图像质量',
                        '3': '图像纹理',
                        '4': '图像清晰度'
                    }
                    
                    report_name = report_names.get(algorithm, f'算法{algorithm}')
                    filename = os.path.join(paths['report_dir'], 
                                          f"{report_name}_{timestamp}.html")
                    
                    # 生成HTML内容
                    html_content = f"""
                    <html>
                    <head>
                    <meta charset=\"UTF-8\">
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                        th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
                        th {{ background-color: #f2f2f2; }}
                        td {{ text-align: center; }}
                    </style>
                    </head>
                    <body>
                    <h1 style=\"text-align: center;\">{report_name}分析报告</h1>
                    {algorithm_report}
                    {overall_report}
                    </body>
                    </html>
                    """
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("为算法 %s 生成了单独报告: %s", algorithm, filename)
                    
                    # 如果是唯一选择的算法，同时生成一个名为report.html的主报告文件，供后端识别
                    if len(actual_input_choice) == 1:
                        main_report_file = os.path.join(paths['report_dir'], "report.html")
                        with open(main_report_file, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        logger.info("为算法 %s 生成了主报告文件: %s", algorithm, main_report_file)
            except Exception as report_error:
                logger.error("为算法 %s 生成报告时出错: %s", algorithm, str(report_error))
                
        except Exception as algorithm_error:
            logger.error("执行算法 %s 时出错: %s", algorithm, str(algorithm_error))
            # 错误只影响当前算法，不影响其他算法的执行
    
    # 如果至少有一个算法成功执行，生成综合报告
    if any(algorithm_success.values()):
        # 筛选出成功执行的算法
        successful_algorithms = ''.join([alg for alg, success in algorithm_success.items() 
                                       if success])
        
        if len(successful_algorithms) > 0:
            try:
                # 生成综合报告
                logger.info("生成综合报告，包含算法: %s", successful_algorithms)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                
                if successful_algorithms == '1234' or input_choice == '5':
                    report_name = '综合质量AI检测'
                else:
                    report_names = {
                        '1': '图像准确度',
                        '2': '图像质量',
                        '3': '图像纹理',
                        '4': '图像清晰度'
                    }
                    report_name = '+'.join([report_names.get(alg, f'算法{alg}') 
                                          for alg in successful_algorithms])
                
                filename = os.path.join(paths['report_dir'], f"{report_name}_{timestamp}.html")
                
                # 筛选出成功算法的结果
                filtered_results = []
                for image_name, result_group in all_results:
                    filtered_group = [(func_id, result) for func_id, result in result_group 
                                    if str(func_id) in successful_algorithms]
                    if filtered_group:  # 只添加有结果的图片
                        filtered_results.append((image_name, filtered_group))
                
                if filtered_results:
                    algorithm_report = generate_algorithm_summary_report(
                        paths, successful_algorithms, config)
                    overall_report = generate_overall_quality_report(
                        filtered_results, config, successful_algorithms, paths)
                    
                    html_content = f"""
                    <html>
                    <head>
                    <meta charset=\"UTF-8\">
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                        th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
                        th {{ background-color: #f2f2f2; }}
                        td {{ text-align: center; }}
                    </style>
                    </head>
                    <body>
                    <h1 style=\"text-align: center;\">{report_name}综合报告</h1>
                    {algorithm_report}
                    {overall_report}
                    </body>
                    </html>
                    """
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("生成了综合报告: %s", filename)
                    
                    # 同时生成一个名为report.html的主报告文件，供后端识别
                    main_report_file = os.path.join(paths['report_dir'], "report.html")
                    with open(main_report_file, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    logger.info("生成了主报告文件: %s", main_report_file)
            except Exception as report_error:
                logger.error("生成综合报告时出错: %s", str(report_error))
    
    # 如果是特殊选项
    if input_choice == '6':
        generate_prompt(paths['input_image_uid'], paths['x_token'])
        logger.info("生成了AI提示")
    elif input_choice == '7':
        generate_anomaly_images(paths['anomaly_output_dir'])
        logger.info("已生成异常图像数据")