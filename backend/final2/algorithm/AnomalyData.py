from PIL import Image, ImageDraw
import os
import random
def generate_anomaly_images(output_dir):
    # 基础参数配置
    anomalies = [
        ("corrupted_header", lambda img: img.tobytes()[:50] + b'\x00' * 50),#文件头损坏
        ("oversized", lambda img: img.resize((10000, 10000))),#大尺寸
        ("invalid_format", lambda img: img.convert('RGB')),#无效格式修复为RGB
        ("empty_canvas", lambda img: Image.new('RGB', (1, 1), (255, 255, 255))),#空文件修复为1x1
        ("pixelated", lambda img: img.resize((10, 10)).resize((512, 512)))#图像模糊的-纯白
    ]
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    # 生成基础服装图像
    def create_base_image():
        img = Image.new('RGB', (512, 512), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 412, 312], outline="black")
        return img
    # 批量生成异常图片
    for i in range(50):
        base_img = create_base_image()
        try:
            anomaly_type, transform = random.choice(anomalies)
            if callable(transform):
                img = transform(base_img)
            else:
                img = transform
            # 保存异常图片
            filename = f"{anomaly_type}_{i}.png"
            save_path = os.path.join(output_dir, filename)
            if isinstance(img, Image.Image):
                img.save(save_path)
            else:
                with open(save_path, 'wb') as f:
                    f.write(img)
        except Exception as e:
            print(f"Error generating {anomaly_type}: {str(e)}")


