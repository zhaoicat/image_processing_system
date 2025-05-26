# 图像处理任务模块使用说明

本模块提供图像处理任务的创建、管理和执行功能。通过简化的导入机制，您可以直接访问final2包中的`process_images`函数和任务相关的其他功能。

## 导入方式

```python
# 导入process_images函数
from final2 import process_images

# 导入任务相关功能
from image_processing_system.backend.tasks import (
    process_single_image,
    start_worker,
    stop_worker,
    add_task,
    submit_task
)
```

## 主要功能

### 1. 处理单个图像

```python
result = process_single_image(
    image_path="path/to/image.jpg",
    report_dir="path/to/report",
    algorithm_choice="1234",  # 使用多种算法
    task_id="task_001"
)
```

### 2. 启动工作进程

```python
# 启动处理图像的工作进程
worker = start_worker()
```

### 3. 提交任务

```python
# 提交处理任务
success = submit_task({
    "task_id": "task_001",
    "algorithm_choice": "1234",
    "report_dir": "path/to/report",
    "image_paths": ["path/to/image1.jpg", "path/to/image2.jpg"]
})
```

### 4. 停止工作进程

```python
# 停止工作进程
stop_worker()
```

## 任务状态跟踪

任务执行过程中会自动更新状态文件，您可以通过监控状态文件了解任务进度：

```python
# 任务状态文件路径
status_file = os.path.join(report_dir, "task_status.json")

# 读取状态信息
with open(status_file, "r", encoding="utf-8") as f:
    status_data = json.load(f)
    
print(f"状态: {status_data['status']}")
print(f"进度: {status_data['progress']}%")
print(f"更新时间: {status_data['updated_at']}")
```

## 注意事项

1. 确保final2包已正确安装
2. 处理大量图像时，推荐使用submit_task函数自动分割为子任务
3. 对于长时间运行的任务，可以通过状态文件跟踪进度 