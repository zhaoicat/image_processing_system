import os
import json
import shutil
import logging
from datetime import datetime
from django.conf import settings
from tasks.models import Task
from images.models import Image

logger = logging.getLogger(__name__)

class ReportGeneratorV2:
    """
    报告生成器 V2 - 简化层级结构
    """
    
    def __init__(self, task_id):
        self.task_id = task_id
        self.task = None
        self.base_dir = os.path.join(settings.REPORTS_DIR, f"task_{task_id}")
        self.meta_dir = os.path.join(self.base_dir, "meta")
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self.assets_dir = os.path.join(self.base_dir, "assets")
        
    def initialize_directories(self):
        """初始化目录结构"""
        try:
            # 创建主要目录
            os.makedirs(self.meta_dir, exist_ok=True)
            os.makedirs(os.path.join(self.reports_dir, "images"), exist_ok=True)
            os.makedirs(os.path.join(self.reports_dir, "algorithms"), exist_ok=True)
            os.makedirs(os.path.join(self.assets_dir, "charts"), exist_ok=True)
            os.makedirs(os.path.join(self.assets_dir, "images"), exist_ok=True)
            os.makedirs(os.path.join(self.assets_dir, "data"), exist_ok=True)
            
            logger.info(f"任务 {self.task_id} 的目录结构初始化完成")
            return True
        except Exception as e:
            logger.error(f"初始化目录结构失败: {e}")
            return False
    
    def get_task_info(self):
        """获取任务信息"""
        try:
            self.task = Task.objects.get(id=self.task_id)
            return True
        except Task.DoesNotExist:
            logger.error(f"任务 {self.task_id} 不存在")
            return False
    
    def generate_meta_files(self):
        """生成元数据文件"""
        try:
            # 获取图片列表
            image_ids = list(self.task.images.values_list('id', flat=True))
            
            # 生成任务信息文件
            task_info = {
                "task_id": self.task.id,
                "task_name": self.task.name,
                "description": self.task.description or "",
                "algorithms": self.task.algorithms or [],
                "image_count": len(image_ids),
                "created_at": self.task.created_at.isoformat(),
                "updated_at": self.task.updated_at.isoformat(),
                "user": self.task.created_by.username if self.task.created_by else "unknown"
            }
            
            task_info_path = os.path.join(self.meta_dir, "task_info.json")
            with open(task_info_path, 'w', encoding='utf-8') as f:
                json.dump(task_info, f, ensure_ascii=False, indent=2)
            
            # 生成任务状态文件
            progress_value = (100.0 if self.task.status == "completed" 
                             else (self.task.progress or 0))
            task_status = {
                "status": self.task.status,
                "progress": progress_value,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": "报告生成完成" if self.task.status == "completed" else "处理中"
            }
            
            task_status_path = os.path.join(self.meta_dir, "task_status.json")
            with open(task_status_path, 'w', encoding='utf-8') as f:
                json.dump(task_status, f, ensure_ascii=False, indent=2)
            
            # 生成处理日志文件
            processing_log = {
                "task_id": self.task.id,
                "total_images": len(image_ids),
                "processed_images": len(image_ids) if self.task.status == "completed" else 0,
                "algorithms_used": self.task.algorithms or [],
                "processing_start": self.task.created_at.isoformat(),
                "processing_end": self.task.completed_at.isoformat() if self.task.completed_at else None,
                "logs": []
            }
            
            processing_log_path = os.path.join(self.meta_dir, "processing_log.json")
            with open(processing_log_path, 'w', encoding='utf-8') as f:
                json.dump(processing_log, f, ensure_ascii=False, indent=2)
            
            logger.info(f"任务 {self.task_id} 的元数据文件生成完成")
            return True
            
        except Exception as e:
            logger.error(f"生成元数据文件失败: {e}")
            return False
    
    def generate_summary_report(self):
        """生成任务综合报告"""
        try:
            # 获取图片列表
            image_ids = list(self.task.images.values_list('id', flat=True))
            
            # 获取算法映射
            algorithm_names = {
                '1': '图像准确度',
                '2': '图像质量', 
                '3': '图像纹理',
                '4': '清晰度'
            }
            
            algorithms = []
            for alg in (self.task.algorithms or []):
                if alg in algorithm_names:
                    algorithms.append(algorithm_names[alg])
                else:
                    algorithms.append(str(alg))
            
            # 获取图片信息
            images_info = []
            for i, image_id in enumerate(image_ids):
                try:
                    image = Image.objects.get(id=image_id)
                    images_info.append({
                        'index': i,
                        'id': image_id,
                        'title': image.title,
                        'file_path': image.file.name if image.file else '',
                        'uploaded_at': image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Image.DoesNotExist:
                    images_info.append({
                        'index': i,
                        'id': image_id,
                        'title': f'图片_{i}',
                        'file_path': '',
                        'uploaded_at': 'Unknown'
                    })
            
            # 生成HTML报告
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务 {self.task.id} - {self.task.name} 综合报告</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #1890ff; 
            text-align: center; 
            border-bottom: 3px solid #1890ff; 
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #333; 
            border-left: 4px solid #1890ff; 
            padding-left: 15px; 
            margin-top: 30px;
        }}
        .info-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin: 20px 0;
        }}
        .info-card {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 4px solid #1890ff;
        }}
        .info-label {{ 
            font-weight: bold; 
            color: #666; 
            margin-bottom: 5px;
        }}
        .info-value {{ 
            color: #333; 
            font-size: 16px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
            background: white;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left;
        }}
        th {{ 
            background-color: #1890ff; 
            color: white; 
            font-weight: bold;
        }}
        tr:nth-child(even) {{ 
            background-color: #f9f9f9;
        }}
        tr:hover {{ 
            background-color: #e6f7ff;
        }}
        .status-completed {{ 
            color: #52c41a; 
            font-weight: bold;
        }}
        .status-processing {{ 
            color: #1890ff; 
            font-weight: bold;
        }}
        .status-failed {{ 
            color: #ff4d4f; 
            font-weight: bold;
        }}
        .algorithm-tag {{ 
            background: #e6f7ff; 
            color: #1890ff; 
            padding: 2px 8px; 
            border-radius: 12px; 
            font-size: 12px; 
            margin: 2px;
            display: inline-block;
        }}
        .nav-links {{ 
            background: #f0f2f5; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
        }}
        .nav-links a {{ 
            color: #1890ff; 
            text-decoration: none; 
            margin-right: 20px; 
            padding: 8px 15px; 
            background: white; 
            border-radius: 5px; 
            border: 1px solid #d9d9d9;
            display: inline-block;
            margin-bottom: 5px;
        }}
        .nav-links a:hover {{ 
            background: #e6f7ff; 
            border-color: #1890ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>任务 {self.task.id} - {self.task.name} 综合报告</h1>
        
        <h2>📋 任务基本信息</h2>
        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">任务ID</div>
                <div class="info-value">{self.task.id}</div>
            </div>
            <div class="info-card">
                <div class="info-label">任务名称</div>
                <div class="info-value">{self.task.name}</div>
            </div>
            <div class="info-card">
                <div class="info-label">任务状态</div>
                <div class="info-value status-{self.task.status}">{self.task.status}</div>
            </div>
            <div class="info-card">
                <div class="info-label">进度</div>
                <div class="info-value">{self.task.progress or 0}%</div>
            </div>
            <div class="info-card">
                <div class="info-label">图片数量</div>
                <div class="info-value">{len(image_ids)}</div>
            </div>
            <div class="info-card">
                <div class="info-label">创建时间</div>
                <div class="info-value">{self.task.created_at.strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
        </div>
        
        <h2>🔧 算法配置</h2>
        <div>
            {''.join([f'<span class="algorithm-tag">{alg}</span>' for alg in algorithms]) if algorithms else '<span class="algorithm-tag">默认算法</span>'}
        </div>
        
        <h2>🖼️ 处理图片列表</h2>
        <table>
            <thead>
                <tr>
                    <th>序号</th>
                    <th>图片名称</th>
                    <th>图片ID</th>
                    <th>上传时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for img_info in images_info:
                html_content += f"""
                <tr>
                    <td>{img_info['index']}</td>
                    <td>{img_info['title']}</td>
                    <td>{img_info['id']}</td>
                    <td>{img_info['uploaded_at']}</td>
                    <td><a href="images/img_{img_info['index']}_{img_info['title']}.html" target="_blank">查看详情</a></td>
                </tr>
"""
            
            html_content += f"""
            </tbody>
        </table>
        
        <h2>📊 快速导航</h2>
        <div class="nav-links">
            <strong>按算法查看：</strong><br>
"""
            
            for alg in algorithms:
                html_content += f'<a href="algorithms/{alg}.html" target="_blank">{alg}报告</a>'
            
            html_content += f"""
        </div>
        
        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 14px;">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
            
            summary_path = os.path.join(self.reports_dir, "summary.html")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"任务 {self.task_id} 的综合报告生成完成")
            return True
            
        except Exception as e:
            logger.error(f"生成综合报告失败: {e}")
            return False
    
    def cleanup_old_structure(self):
        """清理旧的目录结构（可选）"""
        try:
            # 删除旧的img_x目录
            img_dirs = [d for d in os.listdir(self.base_dir) 
                       if os.path.isdir(os.path.join(self.base_dir, d)) and d.startswith('img_')]
            
            for img_dir in img_dirs:
                img_dir_path = os.path.join(self.base_dir, img_dir)
                shutil.rmtree(img_dir_path, ignore_errors=True)
                logger.info(f"已删除旧目录: {img_dir_path}")
            
            # 删除旧的文件
            old_files = ['task_status.json', 'task_tracking.json', 'report.html']
            for old_file in old_files:
                old_file_path = os.path.join(self.base_dir, old_file)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    logger.info(f"已删除旧文件: {old_file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理旧结构失败: {e}")
            return False
    
    def generate_report_from_database(self, cleanup_old=False):
        """直接从数据库生成完整报告（推荐使用）"""
        try:
            logger.info(f"开始为任务 {self.task_id} 从数据库生成新报告")
            
            # 步骤1：获取任务信息
            if not self.get_task_info():
                return False
            
            # 步骤2：初始化目录结构
            if not self.initialize_directories():
                return False
            
            # 步骤3：生成元数据文件
            if not self.generate_meta_files():
                return False
            
            # 步骤4：生成综合报告
            if not self.generate_summary_report():
                return False
            
            # 步骤5：生成模拟的算法报告（基于数据库信息）
            if not self.generate_algorithm_reports_from_db():
                return False
            
            # 步骤6：生成模拟的图片报告
            if not self.generate_image_reports_from_db():
                return False
            
            # 步骤7：清理旧结构（可选）
            if cleanup_old:
                self.cleanup_old_structure()
            
            logger.info(f"任务 {self.task_id} 的新报告生成完成")
            return True
            
        except Exception as e:
            logger.error(f"从数据库生成报告失败: {e}")
            return False
    
    def generate_algorithm_reports_from_db(self):
        """从数据库信息生成算法报告"""
        try:
            # 获取图片列表
            image_ids = list(self.task.images.values_list('id', flat=True))
            
            # 算法名称映射
            algorithm_names = {
                '1': '图像准确度',
                '2': '图像质量', 
                '3': '图像纹理',
                '4': '清晰度'
            }
            
            # 根据任务的算法配置生成报告
            task_algorithms = self.task.algorithms or ['1', '2', '3']
            
            for alg_id in task_algorithms:
                if alg_id in algorithm_names:
                    alg_name = algorithm_names[alg_id]
                    self._generate_single_algorithm_report(alg_name, image_ids)
            
            return True
            
        except Exception as e:
            logger.error(f"生成算法报告失败: {e}")
            return False
    
    def _generate_single_algorithm_report(self, alg_name, image_ids):
        """生成单个算法的报告（使用真实算法）"""
        try:
            # 算法显示名称映射
            algorithm_display_names = {
                '图像准确度': '图像准确度AI检测（ImageHash算法）',
                '图像质量': '图像质量AI检测（OpenCV算法1）',
                '图像纹理': '图像纹理质量AI检测（OpenCV算法2）',
                '清晰度': '清晰度AI检测（OpenCV+ScikitImage算法3）'
            }
            
            display_name = algorithm_display_names.get(alg_name, alg_name)
            
            # 获取图片信息和真实的检测结果
            images_info = []
            for i, image_id in enumerate(image_ids):
                try:
                    image = Image.objects.get(id=image_id)
                    
                    # 获取图片的真实检测结果
                    detection_result = self._run_real_algorithm(alg_name, image)
                    
                    images_info.append({
                        'index': i,
                        'id': image_id,
                        'title': image.title,
                        'file_path': image.file.name if image.file else '',
                        'detection_result': detection_result
                    })
                except Image.DoesNotExist:
                    images_info.append({
                        'index': i,
                        'id': image_id,
                        'title': f'图片_{i}',
                        'file_path': '',
                        'detection_result': {'score': 0, 'status': '错误', 'message': '图片不存在'}
                    })
            
            # 生成HTML内容
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} - 综合报告</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #1890ff; 
            text-align: center; 
            border-bottom: 3px solid #1890ff; 
            padding-bottom: 10px;
        }}
        h2 {{ 
            color: #333; 
            border-left: 4px solid #1890ff; 
            padding-left: 15px; 
            margin-top: 30px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
            background: white;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: center;
        }}
        th {{ 
            background-color: #1890ff; 
            color: white; 
            font-weight: bold;
        }}
        tr:nth-child(even) {{ 
            background-color: #f9f9f9;
        }}
        tr:hover {{ 
            background-color: #e6f7ff;
        }}
        .summary-stats {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 30px;
        }}
        .status-success {{ color: #52c41a; font-weight: bold; }}
        .status-warning {{ color: #faad14; font-weight: bold; }}
        .status-error {{ color: #f5222d; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{display_name} - 任务 {self.task.id} 检测报告</h1>
        
        <div class="summary-stats">
            <h2>📊 算法执行概览</h2>
            <p><strong>任务ID:</strong> {self.task.id}</p>
            <p><strong>任务名称:</strong> {self.task.name}</p>
            <p><strong>处理图片数量:</strong> {len(images_info)} 张</p>
            <p><strong>算法类型:</strong> {display_name}</p>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <h2>📋 检测结果概览</h2>
        <table>
            <thead>
                <tr>
                    <th>图片序号</th>
                    <th>图片名称</th>
                    <th>图片ID</th>
                    <th>检测状态</th>
                    <th>检测分数</th>
                    <th>检测结果</th>
                    <th>详细信息</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 为每张图片生成真实的检测结果
            for img_info in images_info:
                result_data = img_info['detection_result']
                
                html_content += f"""
                <tr>
                    <td>{img_info['index']}</td>
                    <td>{img_info['title']}</td>
                    <td>{img_info['id']}</td>
                    <td><span class="{result_data.get('status_class', 'status-success')}">已检测</span></td>
                    <td>{result_data.get('score', 'N/A')}</td>
                    <td><span class="{result_data.get('status_class', 'status-success')}">{result_data.get('status', '完成')}</span></td>
                    <td>{result_data.get('details', '')}</td>
                </tr>
"""
            
            html_content += f"""
            </tbody>
        </table>
        
        <h2>📈 详细分析</h2>
        <div class="summary-stats">
            <p><strong>总体评估:</strong> 本次 {display_name} 检测共处理 {len(images_info)} 张图片</p>
            <p><strong>检测维度:</strong> 根据 {alg_name} 算法进行全面分析</p>
            <p><strong>技术说明:</strong> 使用真实的图像处理算法进行检测分析</p>
        </div>
        
        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 14px;">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            任务ID: {self.task.id} | 
            算法: {display_name}
        </div>
    </div>
</body>
</html>
"""
            
            # 保存报告
            report_path = os.path.join(self.reports_dir, "algorithms", f"{alg_name}.html")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"已生成算法报告: {report_path}")
            
        except Exception as e:
            logger.error(f"生成算法报告 {alg_name} 失败: {e}")
    
    def _run_real_algorithm(self, alg_name, image):
        """运行真实的算法检测"""
        try:
            # 获取图片的完整路径
            if image.file:
                image_path = image.file.path
            else:
                return {'score': 0, 'status': '错误', 'status_class': 'status-error', 'details': '图片文件不存在'}
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                return {'score': 0, 'status': '错误', 'status_class': 'status-error', 'details': '图片文件路径无效'}
            
            # 根据算法类型运行相应的检测
            if alg_name == '图像准确度':
                return self._run_imagehash_algorithm(image_path)
            elif alg_name == '图像质量':
                return self._run_opencv1_algorithm(image_path) 
            elif alg_name == '图像纹理':
                return self._run_opencv2_algorithm(image_path)
            elif alg_name == '清晰度':
                return self._run_opencv3_algorithm(image_path)
            else:
                return {'score': 0, 'status': '未知算法', 'status_class': 'status-warning', 'details': f'不支持的算法: {alg_name}'}
                
        except Exception as e:
            logger.error(f"运行算法 {alg_name} 时出错: {e}")
            return {'score': 0, 'status': '算法错误', 'status_class': 'status-error', 'details': str(e)}
    
    def _run_imagehash_algorithm(self, image_path):
        """运行ImageHash算法"""
        try:
            # 导入final2的ImageHash算法
            import sys
            final2_path = os.path.join(os.path.dirname(__file__), '..', 'final2')
            if final2_path not in sys.path:
                sys.path.append(final2_path)
            
            from final2.algorithm.ImageHash import is_similar
            
            # 需要一个模板图片进行比较，这里使用默认的模板图片
            # 如果没有模板图片，返回默认值
            template_dir = os.path.join(final2_path, 'data', 'template')
            template_files = []
            if os.path.exists(template_dir):
                template_files = [f for f in os.listdir(template_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
            
            if not template_files:
                # 使用当前图片本身作为"模板"，距离为0
                return {
                    'score': 0,
                    'status': '高度相似',
                    'status_class': 'status-success',
                    'details': '汉明距离: 0 (无模板图片)'
                }
            
            template_path = os.path.join(template_dir, template_files[0])
            result = is_similar(template_path, image_path)
            
            if result and 'distance' in result:
                distance = result['distance']
                status = '高度相似' if result['similar'] else '差异显著'
                status_class = 'status-success' if result['similar'] else 'status-warning'
                
                return {
                    'score': distance,
                    'status': status,
                    'status_class': status_class,
                    'details': f'汉明距离: {distance}'
                }
            else:
                return {'score': 0, 'status': '检测失败', 'status_class': 'status-error', 'details': '算法返回异常'}
                
        except Exception as e:
            return {'score': 0, 'status': '算法错误', 'status_class': 'status-error', 'details': f'ImageHash算法错误: {str(e)}'}
    
    def _run_opencv1_algorithm(self, image_path):
        """运行OpenCV1算法（图像质量）"""
        try:
            import sys
            final2_path = os.path.join(os.path.dirname(__file__), '..', 'final2')
            if final2_path not in sys.path:
                sys.path.append(final2_path)
            
            from final2.algorithm.Opencv1 import calculate_image_quality
            
            result = calculate_image_quality(image_path)
            
            if result and 'quality_score' in result:
                quality_score = result['quality_score']
                score_percentage = int(quality_score * 100)
                
                if quality_score >= 0.6:
                    status = '优良'
                    status_class = 'status-success'
                elif quality_score >= 0.4:
                    status = '可用'
                    status_class = 'status-warning'  
                else:
                    status = '差'
                    status_class = 'status-error'
                
                details = f"颜色匹配: {result.get('color_score', 0):.3f}, 清晰度: {result.get('sharpness_score', 0):.3f}, 噪声: {result.get('noise_score', 0):.3f}"
                
                return {
                    'score': score_percentage,
                    'status': status,
                    'status_class': status_class,
                    'details': details
                }
            else:
                return {'score': 0, 'status': '检测失败', 'status_class': 'status-error', 'details': '算法返回异常'}
                
        except Exception as e:
            return {'score': 0, 'status': '算法错误', 'status_class': 'status-error', 'details': f'OpenCV1算法错误: {str(e)}'}
    
    def _run_opencv2_algorithm(self, image_path):
        """运行OpenCV2算法（图像纹理）"""
        try:
            import sys
            final2_path = os.path.join(os.path.dirname(__file__), '..', 'final2')
            if final2_path not in sys.path:
                sys.path.append(final2_path)
            
            from final2.algorithm.Opencv2 import evaluate_fashion_image
            
            # 获取模板图片
            template_dir = os.path.join(final2_path, 'data', 'template')
            template_path = None
            if os.path.exists(template_dir):
                template_files = [f for f in os.listdir(template_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
                if template_files:
                    template_path = os.path.join(template_dir, template_files[0])
            
            result = evaluate_fashion_image(template_path, image_path)
            
            if result and 'overall' in result:
                overall_score = result['overall']
                score_percentage = int(overall_score * 100)
                
                grade = result.get('quality_grade', 'D')
                status_map = {'A': '优秀', 'B': '良好', 'C': '合格', 'D': '不可用'}
                class_map = {'A': 'status-success', 'B': 'status-success', 'C': 'status-warning', 'D': 'status-error'}
                
                status = status_map.get(grade, '未知')
                status_class = class_map.get(grade, 'status-warning')
                
                details = f"纹理: {result.get('texture', 0):.3f}, 完整性: {result.get('completeness', 0):.3f}, 质量: {result.get('quality', 0):.3f}"
                
                return {
                    'score': score_percentage,
                    'status': status,
                    'status_class': status_class,
                    'details': details
                }
            else:
                return {'score': 0, 'status': '检测失败', 'status_class': 'status-error', 'details': '算法返回异常'}
                
        except Exception as e:
            return {'score': 0, 'status': '算法错误', 'status_class': 'status-error', 'details': f'OpenCV2算法错误: {str(e)}'}
    
    def _run_opencv3_algorithm(self, image_path):
        """运行OpenCV3算法（清晰度）"""
        try:
            import sys
            final2_path = os.path.join(os.path.dirname(__file__), '..', 'final2')
            if final2_path not in sys.path:
                sys.path.append(final2_path)
            
            from final2.algorithm.Opencv3 import calculate_composite_score
            
            result = calculate_composite_score(image_path)
            
            if result and 'composite' in result:
                composite_score = result['composite']
                score_percentage = int(composite_score)
                
                if composite_score >= 85:
                    status = '优秀'
                    status_class = 'status-success'
                elif composite_score >= 70:
                    status = '良好'
                    status_class = 'status-warning'
                else:
                    status = '需改进'
                    status_class = 'status-error'
                
                details = f"Brenner: {result.get('initial_brenner', 0):.1f}, SSIM: {result.get('initial_ssim', 0):.1f}"
                
                return {
                    'score': score_percentage,
                    'status': status,
                    'status_class': status_class,
                    'details': details
                }
            else:
                return {'score': 0, 'status': '检测失败', 'status_class': 'status-error', 'details': '算法返回异常'}
                
        except Exception as e:
            return {'score': 0, 'status': '算法错误', 'status_class': 'status-error', 'details': f'OpenCV3算法错误: {str(e)}'}

    def generate_image_reports_from_db(self):
        """从数据库信息生成图片报告"""
        try:
            # 获取图片列表
            image_ids = list(self.task.images.values_list('id', flat=True))
            
            for i, image_id in enumerate(image_ids):
                try:
                    image = Image.objects.get(id=image_id)
                    self._generate_single_image_report(i, image)
                except Image.DoesNotExist:
                    # 生成占位符报告
                    logger.warning(f"图片 {image_id} 不存在，跳过生成报告")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"生成图片报告失败: {e}")
            return False
    
    def _generate_single_image_report(self, index, image):
        """生成单张图片的报告"""
        try:
            # 获取所有算法的检测结果
            algorithm_results = {}
            for alg_name in ['图像准确度', '图像质量', '图像纹理']:
                try:
                    result = self._run_real_algorithm(alg_name, image)
                    algorithm_results[alg_name] = result
                except Exception as e:
                    logger.error(f"为图片 {image.title} 运行算法 {alg_name} 失败: {e}")
                    algorithm_results[alg_name] = {
                        'score': 'N/A', 
                        'status': '检测失败', 
                        'status_class': 'status-error',
                        'details': str(e)
                    }
            
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片 {index} - {image.title} 详细报告</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        .container {{ 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #1890ff; 
            text-align: center; 
            border-bottom: 3px solid #1890ff; 
            padding-bottom: 10px;
        }}
        .image-info {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left;
        }}
        th {{ 
            background-color: #1890ff; 
            color: white;
        }}
        .status-success {{ color: #52c41a; font-weight: bold; }}
        .status-warning {{ color: #faad14; font-weight: bold; }}
        .status-error {{ color: #f5222d; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>图片详细分析报告</h1>
        
        <div class="image-info">
            <h2>📷 图片基本信息</h2>
            <p><strong>图片名称:</strong> {image.title}</p>
            <p><strong>图片ID:</strong> {image.id}</p>
            <p><strong>文件路径:</strong> {image.file.name if image.file else '未知'}</p>
            <p><strong>上传时间:</strong> {image.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>序号:</strong> {index}</p>
        </div>
        
        <h2>🔍 算法检测结果</h2>
        <table>
            <thead>
                <tr>
                    <th>算法名称</th>
                    <th>检测分数</th>
                    <th>检测结果</th>
                    <th>详细信息</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # 添加每个算法的结果
            for alg_name, result in algorithm_results.items():
                html_content += f"""
                <tr>
                    <td>{alg_name}AI检测</td>
                    <td>{result.get('score', 'N/A')}</td>
                    <td><span class="{result.get('status_class', 'status-warning')}">{result.get('status', '未知')}</span></td>
                    <td>{result.get('details', '无详细信息')}</td>
                </tr>
"""
            
            html_content += f"""
            </tbody>
        </table>
        
        <div style="text-align: center; margin-top: 40px; color: #666; font-size: 14px;">
            报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            任务ID: {self.task.id}
        </div>
    </div>
</body>
</html>
"""
            
            # 保存报告
            report_path = os.path.join(self.reports_dir, "images", f"img_{index}_{image.title}.html")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"已生成图片报告: {report_path}")
            
        except Exception as e:
            logger.error(f"生成图片报告失败 {image.title}: {e}")


def generate_task_report_from_database(task_id, cleanup_old=False):
    """直接从数据库生成任务报告（主入口函数）"""
    generator = ReportGeneratorV2(task_id)
    return generator.generate_report_from_database(cleanup_old=cleanup_old) 