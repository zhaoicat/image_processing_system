import os
import logging
from django.core.management.base import BaseCommand, CommandError
from tasks.models import Task
from reports.generators import generate_task_report_from_database

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '从数据库信息为指定任务生成V2报告'

    def add_arguments(self, parser):
        parser.add_argument(
            'task_ids',
            nargs='+',
            type=int,
            help='要生成报告的任务ID列表'
        )
        parser.add_argument(
            '--cleanup-old',
            action='store_true',
            help='是否清理旧的报告结构',
        )

    def handle(self, *args, **options):
        task_ids = options['task_ids']
        cleanup_old = options['cleanup_old']
        
        for task_id in task_ids:
            try:
                # 检查任务是否存在
                if not Task.objects.filter(id=task_id).exists():
                    self.stdout.write(
                        self.style.ERROR(f'任务 {task_id} 不存在')
                    )
                    continue
                
                self.stdout.write(f'开始为任务 {task_id} 生成报告...')
                
                # 生成报告
                success = generate_task_report_from_database(
                    task_id=task_id,
                    cleanup_old=cleanup_old
                )
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'任务 {task_id} 的报告生成成功！')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'任务 {task_id} 的报告生成失败')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'为任务 {task_id} 生成报告时出错: {e}')
                )
                logger.error(f'生成任务 {task_id} 报告时出错: {e}') 