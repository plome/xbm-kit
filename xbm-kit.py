import matplotlib.pyplot as plt
import numpy as np
import re
import os

# 可选依赖
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告：PIL (Pillow) 未安装，保存 BMP 和编码功能将不可用。")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("警告：pyperclip 未安装，剪贴板复制功能将不可用。")

try:
    import tkinter as tk
    from tkinter import filedialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("警告：tkinter 未安装，文件保存对话框将不可用。")

def parse_xbm_array(array_str):
    """解析XBM数组字符串，提取所有十六进制值"""
    hex_values = re.findall(r'0x[0-9A-Fa-f]+', array_str)
    return [int(x, 16) for x in hex_values]

def xbm_to_image(data, width, height):
    """将XBM数据转换为图像"""
    bytes_per_row = (width + 7) // 8
    img_array = np.zeros((height, width), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            byte_index = y * bytes_per_row + x // 8
            bit_index = x % 8  # LSB顺序（低位在前）
            
            if byte_index < len(data):
                if data[byte_index] & (1 << bit_index):
                    img_array[y, x] = 0  # 黑色
                else:
                    img_array[y, x] = 255  # 白色
    
    return img_array

def image_to_xbm(image_path):
    """
    将图像文件转换为XBM十六进制数组（LSB顺序）
    返回 (width, height, hex_string)
    hex_string 格式：每行12个字节，缩进2空格，字节间逗号分隔，最后一行末尾无逗号
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL (Pillow) 未安装，无法进行编码。")
    
    # 打开图像并转换为灰度
    img = Image.open(image_path).convert('L')
    width, height = img.size
    pixels = np.array(img)
    
    # 二值化：灰度值 < 128 视为黑色（位=1），否则白色（位=0）
    binary = (pixels < 128).astype(np.uint8)  # 黑色为1，白色为0
    
    bytes_per_row = (width + 7) // 8
    total_bytes = bytes_per_row * height
    data = [0] * total_bytes
    
    for y in range(height):
        for x in range(width):
            byte_index = y * bytes_per_row + x // 8
            bit_index = x % 8
            if binary[y, x] == 1:  # 黑色
                data[byte_index] |= (1 << bit_index)
    
    # 格式化输出为十六进制字符串，每行12个，行首缩进2个空格
    hex_values = [f"0x{byte:02X}" for byte in data]
    lines = []
    for i in range(0, len(hex_values), 12):
        line = ", ".join(hex_values[i:i+12])
        lines.append(f"  {line}")  # 增加两个空格缩进
    hex_string = ",\n".join(lines)
    
    return width, height, hex_string

def validate_array_name(name):
    """检查数组名称是否为合法的C标识符"""
    if not name:
        return False
    # C标识符：字母、数字、下划线，不能以数字开头
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None

def save_as_bmp(img_array, default_name="image.bmp"):
    """弹出保存对话框，将图像保存为BMP文件（原始尺寸）"""
    if not PIL_AVAILABLE or not TKINTER_AVAILABLE:
        print("无法保存：缺少PIL或tkinter。")
        return False
    
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    file_path = filedialog.asksaveasfilename(
        defaultextension=".bmp",
        filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")],
        initialfile=default_name
    )
    if file_path:
        img = Image.fromarray(img_array, mode='L')
        img.save(file_path)
        print(f"图像已保存至: {file_path}")
        return True
    else:
        print("未保存文件。")
        return False

def clear_screen():
    """清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        try:
            clear_screen()
            print("XBM图像工具")
            print("=" * 30)
            print("输入 'q' 退出程序")
            print("解码：输入数字宽度，随后输入高度并点击鼠标右键粘贴XBM数组")
            print("编码：输入图片文件路径，将自动转换为XBM十六进制数组")
            print()
            
            user_input = input("请输入图像宽度【数字】或【拖入图片文件】: ").strip()
            if user_input.lower() == 'q':
                break
            
            # 尝试判断是否为数字
            if user_input.isdigit():
                # -------------------- 解码模式 --------------------
                try:
                    width = int(user_input)
                    height_input = input("请输入图像高度: ").strip()
                    if height_input.lower() == 'q':
                        break
                    height = int(height_input)
                    
                    print("\n请点击【鼠标右键】粘贴XBM数组数据:")
                    print("格式: {0x00, 0x01, 0x02, ...}")
                    print("粘贴后按回车继续:")
                    
                    array_lines = []
                    while True:
                        line = input()
                        if line == '':
                            break
                        array_lines.append(line)
                    
                    array_str = " ".join(array_lines)
                    data = parse_xbm_array(array_str)
                    
                    if len(data) == 0:
                        print("未检测到有效数据，请重新输入")
                        input("按回车继续...")
                        continue
                    
                    print(f"解析到 {len(data)} 字节数据，正在预览...")
                    
                    # 渲染图像
                    img_array = xbm_to_image(data, width, height)
                    
                    # 显示图像（预览框放大）
                    plt.figure(figsize=(width/50, height/50))
                    plt.imshow(img_array, cmap='gray')
                    plt.axis('off')
                    plt.tight_layout(pad=0)
                    plt.show(block=False)
                    
                    # 询问是否保存BMP
                    save_choice = input("\n是否保存为BMP文件？(y/n): ").strip().lower()
                    if save_choice in ('y', 'yes'):
                        save_as_bmp(img_array)
                    else:
                        print("未保存。")
                    
                    input("按回车继续...")
                    
                except ValueError:
                    print("输入错误，请确保输入的是数字")
                    input("按回车继续...")
                except Exception as e:
                    print(f"处理错误: {e}")
                    input("按回车继续...")
            
            else:
                # -------------------- 编码模式 --------------------
                file_path = user_input
                if not os.path.isfile(file_path):
                    print("文件不存在，请重新输入。")
                    input("按回车继续...")
                    continue
                
                try:
                    width, height, hex_string = image_to_xbm(file_path)
                    print(f"\n图片尺寸: {width} x {height}，已编码完毕。")
                    
                    # 提示用户输入数组名称
                    while True:
                        name_input = input("\n请输入数组名称（直接按回车仅复制数组内容）: ").strip()
                        if name_input == "":
                            # 直接回车：只复制数组内容
                            content_to_copy = hex_string
                            print("\n生成的XBM十六进制数组（每行12个，已缩进2空格）:")
                            print(hex_string)
                            if PYPERCLIP_AVAILABLE:
                                pyperclip.copy(content_to_copy)
                                print("\n已复制数组内容到剪贴板。")
                            else:
                                print("\n未安装 pyperclip，请手动复制上方内容。")
                                print("安装命令: pip install pyperclip")
                            break
                        else:
                            # 验证名称合法性
                            if validate_array_name(name_input):
                                # 生成模板
                                template = f"static const uint8_t {name_input}[] PROGMEM =      //{name_input}，{width}*{height}\n{{\n{hex_string}\n}};"
                                print("\n生成的模板数组:")
                                print(template)
                                if PYPERCLIP_AVAILABLE:
                                    pyperclip.copy(template)
                                    print("\n已复制完整模板到剪贴板。")
                                else:
                                    print("\n未安装 pyperclip，请手动复制上方内容。")
                                    print("安装命令: pip install pyperclip")
                                break
                            else:
                                print("数组名称无效，只允许字母、数字、下划线，且不能以数字开头。请重新输入。")
                                continue
                    
                    input("\n按回车继续...")
                    
                except Exception as e:
                    print(f"编码错误: {e}")
                    input("按回车继续...")
        except KeyboardInterrupt:
            # 允许用户通过 Ctrl+C 退出
            print("\n用户中断，退出程序。")
            break
        except Exception as e:
            print(f"未预期的错误: {e}")
            input("按回车继续...")

if __name__ == "__main__":
    main()