#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from django.core.management import execute_from_command_line


def main():
    """Run administrative tasks."""
    # 将项目根目录添加到Python路径中
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, BASE_DIR)
    
    # 使用image_processing目录下的settings.py
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_processing.settings')
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
