from PIL import Image
import imagehash
def is_similar(image_path1, image_path2, threshold=10):
    # 加载图像并计算哈希
    image1 = Image.open(image_path1)
    image2 = Image.open(image_path2)
    # 使用感知哈希（pHash）
    hash1 = imagehash.phash(image1, hash_size=32)  # hash_size越大，精度越高
    hash2 = imagehash.phash(image2, hash_size=32)
    # 计算汉明距离
    hamming_distance = hash1 - hash2
    #print(f"汉明距离: {hamming_distance}")
    # 判断相似性
    is_similar = hamming_distance <= threshold
    result = {
        "distance": hamming_distance,
        "similar": is_similar,

    }
    # 返回汉明距离和相似性结果
    #return hamming_distance, is_similar
    return result


# 示例调用
#image1 = r"C:\Users\Administrator\Desktop\test\1.jpg"
#image2 = r"C:\Users\Administrator\Desktop\test\2.jpg"
#if is_similar(image1, image2, threshold=10):
 #   print("图像高度相似或重复！")
#else:
 #   print("图像差异显著。")

    #导入必要的库：ImageIO、BufferedImage、Apache Commons、Math的DCT类等。
    #编写加载图像的方法：使用ImageIO.read()。
    #调整图像大小到32x32。
    #转换为灰度图像。
    #将图像数据转换为二维数组。
    #应用DCT变换。
    #提取左上角的数值，计算中值。
    #生成哈希的二进制表示。
    #计算两个哈希之间的汉明距离。
    #比较距离是否小于阈值。


