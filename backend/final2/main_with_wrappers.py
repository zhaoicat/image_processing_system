#!/usr/bin/env python3
"""
图像质量检测系统主程序
集成算法包装器和报告生成功能
"""

from report_generator import generate_html_report, quick_report_generation
from algorithm_wrappers import (
    imagehash_algorithm,
    opencv1_algorithm, 
    opencv2_algorithm,
    opencv3_algorithm,
    openai_algorithm,
    anomaly_data_algorithm,
    comprehensive_algorithm
)
import os
from .config import get_config, get_paths

def main():
    """主程序入口"""
    # 使用统一的配置
    config = get_config()
    paths = get_paths()

    print("=" * 60)
    print("图像质量检测系统 (包装器版本)")
    print("=" * 60)
    print("功能说明：")
    print("1. 图像准确度AI检测报告（ImageHash算法）")
    print("2. 图像质量AI检测报告（OpenCV算法1）")
    print("3. 图像纹理质量AI检测报告（OpenCV算法2）")
    print("4. 清晰度AI检测报告（OpenCV+ScikitImage算法3）")
    print("5. 整体图像质量AI检测报告（功能1+2+3+4）")
    print("6. OpenAI提示生成")
    print("7. 异常图像数据生成")
    print("8. 单独算法测试")
    print("9. 快速报告生成")
    print("0. 退出程序")
    print("=" * 60)

    while True:
        input_choice = input("\n请输入功能选择（例如：'12' 表示功能1和2）：")
        
        if input_choice == '0':
            print("退出程序")
            break
            
        elif input_choice in ['1', '2', '3', '4', '5', '12', '13', '14', '23', '24', '34', '123', '124', '134', '234', '1234']:
            # 生成HTML报告
            try:
                print(f"\n正在生成功能{input_choice}的检测报告...")
                report_path = generate_html_report(paths, config, input_choice)
                print(f"✅ 报告生成成功: {report_path}")
                
                # 显示报告文件大小
                if os.path.exists(report_path):
                    file_size = os.path.getsize(report_path)
                    print(f"   文件大小: {file_size} bytes")
                    
            except Exception as e:
                print(f"❌ 报告生成失败: {e}")
                
        elif input_choice == '6':
            # OpenAI提示生成
            try:
                print("\n正在调用OpenAI提示生成...")
                result = openai_algorithm(paths['input_image_uid'], paths['x_token'])
                print(f"✅ 提示生成结果: {result}")
            except Exception as e:
                print(f"❌ 提示生成失败: {e}")
                
        elif input_choice == '7':
            # 异常图像数据生成
            try:
                print("\n正在生成异常图像数据...")
                anomaly_data_algorithm(paths['anomaly_output_dir'])
                print(f"✅ 异常图像数据已生成到: {paths['anomaly_output_dir']}")
                
                # 显示生成的文件数量
                if os.path.exists(paths['anomaly_output_dir']):
                    files = os.listdir(paths['anomaly_output_dir'])
                    print(f"   生成文件数量: {len(files)}")
                    
            except Exception as e:
                print(f"❌ 异常数据生成失败: {e}")
                
        elif input_choice == '8':
            # 单独算法测试
            test_individual_algorithms(paths, config)
            
        elif input_choice == '9':
            # 快速报告生成
            try:
                print("\n使用快速报告生成...")
                report_path = quick_report_generation(
                    template_dir=paths['template_image_dir'],
                    comparison_dir=paths['comparison_image_dir'],
                    report_dir=paths['report_dir'],
                    algorithms="1234"
                )
                print(f"✅ 快速报告生成成功: {report_path}")
                
                if os.path.exists(report_path):
                    file_size = os.path.getsize(report_path)
                    print(f"   文件大小: {file_size} bytes")
                    
            except Exception as e:
                print(f"❌ 快速报告生成失败: {e}")
                
        else:
            print("❌ 无效的功能选择，请重新输入")

def test_individual_algorithms(paths, config):
    """测试单独的算法"""
    print("\n" + "=" * 50)
    print("单独算法测试")
    print("=" * 50)
    
    template_path = 'data/template/2.jpg'
    comparison_path = 'data/comparision/1.jpg'
    
    # 测试ImageHash算法
    print("\n1. ImageHash算法测试:")
    try:
        result1 = imagehash_algorithm(template_path, comparison_path, config['distance_threshold'])
        print(f"   汉明距离: {result1['distance']}")
        print(f"   是否相似: {result1['similar']}")
        print("   ✅ ImageHash算法测试成功")
    except Exception as e:
        print(f"   ❌ ImageHash算法测试失败: {e}")

    # 测试OpenCV1算法
    print("\n2. OpenCV1算法测试:")
    try:
        result2 = opencv1_algorithm(comparison_path, (255, 255, 255))
        print(f"   颜色匹配度: {result2['color_score']:.3f}")
        print(f"   清晰度: {result2['sharpness_score']:.3f}")
        print(f"   综合质量: {result2['quality_score']:.3f}")
        print("   ✅ OpenCV1算法测试成功")
    except Exception as e:
        print(f"   ❌ OpenCV1算法测试失败: {e}")

    # 测试OpenCV2算法
    print("\n3. OpenCV2算法测试:")
    try:
        result3 = opencv2_algorithm(template_path, comparison_path)
        print(f"   纹理复杂度: {result3['texture']:.3f}")
        print(f"   元素完整性: {result3['completeness']:.3f}")
        print(f"   质量等级: {result3['quality_grade']}")
        print("   ✅ OpenCV2算法测试成功")
    except Exception as e:
        print(f"   ❌ OpenCV2算法测试失败: {e}")

    # 测试OpenCV3算法
    print("\n4. OpenCV3算法测试:")
    try:
        result4 = opencv3_algorithm(comparison_path)
        print(f"   Brenner梯度: {result4['raw_scores']['brenner']:.2f}")
        print(f"   SSIM对比度: {result4['raw_scores']['ssim']:.2f}")
        print(f"   综合得分: {result4['composite']:.1f}")
        print("   ✅ OpenCV3算法测试成功")
    except Exception as e:
        print(f"   ❌ OpenCV3算法测试失败: {e}")

    # 测试综合算法
    print("\n5. 综合算法测试:")
    try:
        comprehensive_config = {
            'distance_threshold': config['distance_threshold'],
            'color_score_threshold_high': config['color_score_threshold_high'],
            'color_score_threshold_low': config['color_score_threshold_low'],
            'sharpness_score_threshold_high': config['sharpness_score_threshold_high'],
            'sharpness_score_threshold_low': config['sharpness_score_threshold_low'],
        }
        result5 = comprehensive_algorithm(template_path, comparison_path, comprehensive_config)
        print("   包含的算法结果:")
        for alg_name in result5.keys():
            print(f"     - {alg_name}: ✓")
        print("   ✅ 综合算法测试成功")
    except Exception as e:
        print(f"   ❌ 综合算法测试失败: {e}")

    print("\n" + "=" * 50)
    print("单独算法测试完成!")
    print("=" * 50)

if __name__ == '__main__':
    main() 