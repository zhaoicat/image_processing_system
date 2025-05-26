#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
演示如何使用process_images函数处理批量任务
"""

import os
import time
import glob
import concurrent.futures


# 导入process_images函数
from main import process_images


class BatchProcessor:
    """批量图像处理器"""
    
    def __init__(self, base_output_dir="./batch_output"):
        """初始化批量处理器
        
        Args:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = base_output_dir
        os.makedirs(base_output_dir, exist_ok=True)
        
        # 任务配置列表
        self.tasks = []
        
        # 记录处理结果
        self.results = []
    
    def add_task(self, task_id, algorithm_choice, image_paths, 
                 custom_config=None):
        """添加处理任务
        
        Args:
            task_id: 任务ID
            algorithm_choice: 算法选择
            image_paths: 图片路径列表
            custom_config: 自定义配置
        """
        task = {
            "task_id": task_id,
            "algorithm_choice": algorithm_choice,
            "image_paths": image_paths,
            "custom_config": custom_config
        }
        self.tasks.append(task)
        print(f"已添加任务: {task_id}, 算法: {algorithm_choice}, "
              f"图片数量: {len(image_paths)}")
    
    def process_task(self, task):
        """处理单个任务
        
        Args:
            task: 任务字典
        
        Returns:
            任务处理结果
        """
        start_time = time.time()
        
        # 创建任务专属输出目录
        task_output_dir = os.path.join(self.base_output_dir, task["task_id"])
        os.makedirs(task_output_dir, exist_ok=True)
        
        # 调用process_images处理任务
        try:
            result = process_images(
                task_id=task["task_id"],
                algorithm_choice=task["algorithm_choice"],
                output_dir=task_output_dir,
                image_paths=task["image_paths"],
                custom_config=task["custom_config"]
            )
            
            # 添加耗时信息
            result["execution_time"] = time.time() - start_time
            
            return {
                "task_id": task["task_id"],
                "status": result["status"],
                "report_path": result.get("report_path", ""),
                "message": result.get("message", ""),
                "execution_time": result["execution_time"]
            }
        except Exception as e:
            # 记录异常
            return {
                "task_id": task["task_id"],
                "status": "error",
                "message": f"任务执行异常: {str(e)}",
                "execution_time": time.time() - start_time
            }
    
    def run_sequential(self):
        """顺序执行所有任务"""
        print(f"开始顺序处理 {len(self.tasks)} 个任务...")
        self.results = []
        
        for task in self.tasks:
            print(f"正在处理任务: {task['task_id']}")
            result = self.process_task(task)
            self.results.append(result)
            
            # 打印任务状态
            if result["status"] == "success":
                print(f"✓ 任务 {result['task_id']} 完成，"
                      f"耗时: {result['execution_time']:.2f}秒")
            else:
                print(f"✗ 任务 {result['task_id']} 失败: {result['message']}")
        
        return self.results
    
    def run_parallel(self, max_workers=4):
        """并行执行所有任务
        
        Args:
            max_workers: 最大并行工作线程数
        """
        print(f"开始并行处理 {len(self.tasks)} 个任务，"
              f"最大并行数: {max_workers}...")
        self.results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.process_task, task): task 
                for task in self.tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    # 打印任务状态
                    if result["status"] == "success":
                        print(f"✓ 任务 {result['task_id']} 完成，"
                              f"耗时: {result['execution_time']:.2f}秒")
                    else:
                        print(f"✗ 任务 {result['task_id']} 失败: "
                              f"{result['message']}")
                except Exception as e:
                    print(f"✗ 任务 {task['task_id']} 异常: {str(e)}")
        
        return self.results
    
    def print_summary(self):
        """打印处理结果摘要"""
        if not self.results:
            print("尚未处理任何任务")
            return
        
        print("\n===== 任务处理摘要 =====")
        success_count = sum(1 for r in self.results if r["status"] == "success")
        total_time = sum(r["execution_time"] for r in self.results)
        
        print(f"总任务数: {len(self.results)}")
        print(f"成功任务数: {success_count}")
        print(f"失败任务数: {len(self.results) - success_count}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均每任务耗时: {total_time/len(self.results):.2f}秒")
        
        # 列出失败的任务
        failed_tasks = [r for r in self.results if r["status"] != "success"]
        if failed_tasks:
            print("\n失败任务列表:")
            for task in failed_tasks:
                print(f"- 任务 {task['task_id']}: {task['message']}")


def demo_batch_processing():
    """演示批量处理功能"""
    # 创建批处理器
    processor = BatchProcessor()
    
    # 获取测试图片
    # 修正路径 - 使用当前文件所在目录的相对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(current_dir, "data/template")
    test_images = []
    
    if os.path.exists(template_dir):
        for ext in ['.jpg', '.png', '.jpeg']:
            pattern = os.path.join(template_dir, f"*{ext}")
            found_images = glob.glob(pattern)
            test_images.extend(found_images)
            print(f"在 {pattern} 找到 {len(found_images)} 张图片")
    
    if not test_images:
        print(f"错误: 找不到测试图片，无法继续演示。路径: {template_dir}")
        return
    
    print(f"找到 {len(test_images)} 张测试图片")
    
    # 创建不同的任务配置
    # 任务1: 使用算法1处理所有图片
    processor.add_task(
        task_id="all_images_algo1",
        algorithm_choice="1",
        image_paths=test_images,
        custom_config={"distance_threshold": 3}
    )
    
    # 任务2: 使用算法2处理前3张图片
    if len(test_images) >= 3:
        processor.add_task(
            task_id="first3_algo2",
            algorithm_choice="2",
            image_paths=test_images[:3]
        )
    
    # 任务3: 使用多个算法处理第一张图片
    if test_images:
        processor.add_task(
            task_id="first_image_multi_algo",
            algorithm_choice="1234",
            image_paths=[test_images[0]]
        )
    
    # 运行任务并打印结果
    print("\n使用顺序处理模式:")
    processor.run_sequential()
    processor.print_summary()
    
    print("\n使用并行处理模式:")
    processor.run_parallel(max_workers=2)
    processor.print_summary()


if __name__ == "__main__":
    demo_batch_processing() 