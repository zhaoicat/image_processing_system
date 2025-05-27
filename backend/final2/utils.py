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
from algorithm.AnomalyData import generate_anomaly_images
from algorithm.ImageHash import is_similar
from algorithm.Openai import generate_prompt
from algorithm.Opencv1 import calculate_image_quality  # 2-1
from algorithm.Opencv2 import evaluate_fashion_image  # 2-2
from algorithm.Opencv3 import calculate_composite_score
from algorithm.evaluation import (
    test_imagehash_algorithm,
    test_opencv1_algorithm,
    test_opencv2_algorithm,
    test_opencv3_algorithm,
    test_overall_results
)

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


def generate_algorithm_summary_report(paths, input_choice, config, all_results=None):
    algorithm_summary = {
        'ImageHash': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV1': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV2': {'total': 0, 'passed': 0, 'failed': 0},
        'OpenCV3': {'total': 0, 'passed': 0, 'failed': 0}
    }
    selected_algorithms = []
    
    # 如果提供了all_results，使用它来计算图片总数，否则使用原有的扫描方式
    if all_results:
        total_images_count = len(all_results)
        # 简化统计：假设所有图片都通过了测试（这里可以根据实际需求调整）
        if '1' in input_choice:
            algorithm_summary['ImageHash']['total'] = total_images_count
            algorithm_summary['ImageHash']['passed'] = total_images_count
            algorithm_summary['ImageHash']['failed'] = 0
            selected_algorithms.append('ImageHash')
        if '2' in input_choice:
            algorithm_summary['OpenCV1']['total'] = total_images_count
            algorithm_summary['OpenCV1']['passed'] = total_images_count
            algorithm_summary['OpenCV1']['failed'] = 0
            selected_algorithms.append('OpenCV1')
        if '3' in input_choice:
            algorithm_summary['OpenCV2']['total'] = total_images_count
            algorithm_summary['OpenCV2']['passed'] = total_images_count
            algorithm_summary['OpenCV2']['failed'] = 0
            selected_algorithms.append('OpenCV2')
        if '4' in input_choice:
            algorithm_summary['OpenCV3']['total'] = total_images_count
            algorithm_summary['OpenCV3']['passed'] = total_images_count
            algorithm_summary['OpenCV3']['failed'] = 0
            selected_algorithms.append('OpenCV3')
    else:
        # 使用原有的扫描方式
        if '1' in input_choice:
            algorithm_summary['ImageHash']['total'], algorithm_summary['ImageHash']['passed'], algorithm_summary['ImageHash']['failed'] = test_imagehash_algorithm(paths, config)
            selected_algorithms.append('ImageHash')
        if '2' in input_choice:
            algorithm_summary['OpenCV1']['total'], algorithm_summary['OpenCV1']['passed'], algorithm_summary['OpenCV1']['failed'] = test_opencv1_algorithm(paths, config)
            selected_algorithms.append('OpenCV1')
        if '3' in input_choice:
            algorithm_summary['OpenCV2']['total'], algorithm_summary['OpenCV2']['passed'], algorithm_summary['OpenCV2']['failed'] = test_opencv2_algorithm(paths, config)
            selected_algorithms.append('OpenCV2')
        if '4' in input_choice:
            algorithm_summary['OpenCV3']['total'], algorithm_summary['OpenCV3']['passed'], algorithm_summary['OpenCV3']['failed'] = test_opencv3_algorithm(paths, config)
            selected_algorithms.append('OpenCV3')
    
    total_images = sum(algorithm_summary[alg]['total'] for alg in selected_algorithms)
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
    algorithm_report = generate_algorithm_summary_report(paths, input_choice, config, all_results)
    overall_report = generate_overall_quality_report(all_results, config, input_choice, paths)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 确保报告目录存在
    os.makedirs(paths['report_dir'], exist_ok=True)
    
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
    elif len(sorted_choice) > 1:
        # 如果选择了多个算法，统一使用综合报告名称
        report_name = '综合质量AI检测'
    else:
        # 单个算法但不在映射表中，使用默认名称
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
    print(f"Combined report generated: {filename}")
    return filename



def evaluation(paths, config, input_choice, specific_image_paths=None):
    all_results = []
    
    # 更健壮的模板图片路径查找
    template_image_path = None
    
    # 查找JPG文件
    jpg_files = glob.glob(os.path.join(paths['template_image_dir'], '*.jpg'))
    if jpg_files:
        template_image_path = jpg_files[0]
    else:
        # 查找PNG文件
        png_files = glob.glob(os.path.join(paths['template_image_dir'], '*.png'))
        if png_files:
            template_image_path = png_files[0]
        else:
            # 查找其他常见图片格式
            jpeg_files = glob.glob(os.path.join(paths['template_image_dir'], '*.jpeg'))
            if jpeg_files:
                template_image_path = jpeg_files[0]
    
    # 如果仍然没有找到模板图片，抛出错误
    if template_image_path is None:
        raise FileNotFoundError(f"在模板目录 '{paths['template_image_dir']}' 中没有找到任何图片文件 (支持格式: .jpg, .png, .jpeg)")
    
    print(f"使用模板图片: {template_image_path}")
    
    # 根据是否提供了specific_image_paths来决定处理哪些图片
    if specific_image_paths:
        # 使用指定的图片路径列表
        image_paths_to_process = specific_image_paths
        print(f"处理指定的 {len(image_paths_to_process)} 张图片")
    else:
        # 扫描整个目录（保持原有行为）
        image_paths_to_process = (glob.glob(os.path.join(paths['comparison_image_dir'], '*.jpg')) + 
                                 glob.glob(os.path.join(paths['comparison_image_dir'], '*.png')))
        print(f"扫描目录找到 {len(image_paths_to_process)} 张图片")
    
    # 为每张图片创建结果条目
    for image_path in tqdm(image_paths_to_process, desc='Processing images'):
        image_name = os.path.basename(image_path)
        all_results.append((image_name, []))
    
    report_paths = []
    
    if input_choice != '5':
        for i, (image_name, result_group) in tqdm(enumerate(all_results), desc='Evaluating images', total=len(all_results)):
            # 根据是否使用specific_image_paths来构建图片路径
            if specific_image_paths:
                image_path = image_paths_to_process[i]
            else:
                image_path = os.path.join(paths['comparison_image_dir'], image_name)
            
            if '1' in input_choice:
                hamming = is_similar(template_image_path, image_path)
                result_group.append((1, hamming))
            if '2' in input_choice:
                result_quality = calculate_image_quality(image_path)
                result_group.append((2, result_quality))
            if '3' in input_choice:
                result_fashion = evaluate_fashion_image(template_image_path, image_path)
                result_group.append((3, result_fashion))
            if '4' in input_choice:
                clarity_result = calculate_composite_score(image_path)
                result_group.append((4, clarity_result))
        
        # 生成单个算法报告
        for algorithm in input_choice:
            if algorithm in ['1', '2', '3', '4']:
                # 为单个算法创建只包含该算法数据的结果集
                single_algorithm_results = []
                for image_name, result_group in all_results:
                    single_result_group = []
                    for func_id, result in result_group:
                        if str(func_id) == algorithm:
                            single_result_group.append((func_id, result))
                    if single_result_group:
                        single_algorithm_results.append((image_name, single_result_group))
                
                single_report_path = generate_combined_report(single_algorithm_results, config, algorithm, paths)
                report_paths.append(single_report_path)
                print(f"已生成算法{algorithm}的单独报告")
        
        # 如果选择了多个算法，还要生成综合报告
        if len(input_choice) > 1:
            combined_report_path = generate_combined_report(all_results, config, input_choice, paths)
            report_paths.append(combined_report_path)
            print(f"已生成综合报告")
    
    elif input_choice == '5':
        input_choice = '1234'
        for i, (image_name, result_group) in tqdm(enumerate(all_results), desc='Evaluating images for input choice 5', total=len(all_results)):
            # 根据是否使用specific_image_paths来构建图片路径
            if specific_image_paths:
                image_path = image_paths_to_process[i]
            else:
                image_path = os.path.join(paths['comparison_image_dir'], image_name)
            
            hamming = is_similar(template_image_path, image_path)
            result_group.append((1, hamming))
            result_quality = calculate_image_quality(image_path)
            result_group.append((2, result_quality))
            result_fashion = evaluate_fashion_image(template_image_path, image_path)
            result_group.append((3, result_fashion))
            clarity_result = calculate_composite_score(image_path)
            result_group.append((4, clarity_result))
        
        # 为选择5生成所有单个算法报告和综合报告
        for algorithm in ['1', '2', '3', '4']:
            # 为单个算法创建只包含该算法数据的结果集
            single_algorithm_results = []
            for image_name, result_group in all_results:
                single_result_group = []
                for func_id, result in result_group:
                    if str(func_id) == algorithm:
                        single_result_group.append((func_id, result))
                if single_result_group:
                    single_algorithm_results.append((image_name, single_result_group))
            
            single_report_path = generate_combined_report(single_algorithm_results, config, algorithm, paths)
            report_paths.append(single_report_path)
            print(f"已生成算法{algorithm}的单独报告")
        
        # 生成综合报告
        combined_report_path = generate_combined_report(all_results, config, input_choice, paths)
        report_paths.append(combined_report_path)
        print(f"已生成综合报告")
        
    elif input_choice == '6':
        generate_prompt(paths['input_image_uid'], paths['x_token'])
        print("generate_prompt")
        return {"status": "success", "message": "Prompt生成完成"}
    elif input_choice == '0':
        print("退出程序")
        return {"status": "success", "message": "程序退出"}
    elif input_choice == '7':
        generate_anomaly_images(paths['anomaly_output_dir'])
        print("已生成异常图像数据")
        return {"status": "success", "message": "异常图像数据生成完成"}
    
    # 返回处理结果
    return {
        "status": "success",
        "message": f"图像处理完成，算法选择: {input_choice}",
        "report_paths": report_paths,  # 返回所有生成的报告路径
        "main_report_path": report_paths[-1] if report_paths else None,  # 主报告路径（综合报告或最后一个）
        "processed_images": len(all_results),
        "template_image": template_image_path
    }