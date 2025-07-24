import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import shutil
from pathlib import Path
from openai import OpenAI
from config import API_KEY, API_URL

input_dir = Path("input")
output_dir = "output"

client = OpenAI(api_key=API_KEY, base_url=API_URL)

def parse_qwen_output(text: str) -> tuple:
    lines = text.strip().splitlines()
    project_name = file_type = None
    for line in lines:
        if "工程名称" in line:
            project_name = line.split("：", 1)[1].strip()
        elif "文件类型" in line:
            file_type = line.split("：", 1)[1].strip()
    return project_name, file_type

def process_pdf(file_path: Path):
    prompt = """
请根据pdf的文本内容，提取出：
1. 工程名称（如果是会议，请提取会议名称）
2. 文件类型（如xx合同书）

返回格式如下，请勿返回其他内容：
工程名称：xxx工程
文件类型：xxx
"""
    try:
        file_object = client.files.create(file=file_path, purpose='file-extract')
        completion = client.chat.completions.create(
            model="qwen-long",
            messages=[
                {'role': 'system', 'content': f'fileid://{file_object.id}'},
                {'role': 'user', 'content': prompt}
            ]
        )
        response = completion.choices[0].message.content
        return parse_qwen_output(response)
    except Exception as e:
        print(f"❌ 处理失败: {file_path.name}, 错误: {e}")
        return None, None

def start_processing(status_label):
    pdf_files = list(input_dir.glob("*.pdf"))
    total = len(pdf_files)

    if not total:
        messagebox.showinfo("提示", "未找到任何 PDF 文件")
        return

    for pdf in pdf_files:
        status_label.config(text=f"正在处理：{pdf.name}")
        status_label.update()  # 立刻刷新界面显示当前文件名
        project_name, file_type = process_pdf(pdf)
        if project_name and file_type:
            target_folder = os.path.join(output_dir, project_name)
            os.makedirs(target_folder, exist_ok=True)
            new_filename = f"{file_type}.pdf"
            target_path = os.path.join(target_folder, new_filename)
            shutil.copy2(str(pdf), target_path)
            os.remove(pdf)
            status_label.config(text=f"✅ 成功处理：{pdf.name}")
        else:
            status_label.config(text=f"❌ 处理失败：{pdf.name}")
        status_label.update()
    messagebox.showinfo("完成", "所有 PDF 已分类完毕！")
    status_label.config(text="处理完成，等待下一次操作")


def run_gui():
    window = tk.Tk()
    window.title("PDF分类工具")
    window.geometry("400x150")

    ttk.Label(window, text="点击开始分类 PDF").pack(pady=10)

    status = ttk.Label(window, text="等待开始")
    status.pack()

    start_button = ttk.Button(
        window,
        text="开始处理",
        command=lambda: threading.Thread(target=start_processing, args=(status,)).start()
    )
    start_button.pack(pady=10)

    window.mainloop()

if __name__ == "__main__":
    run_gui()

