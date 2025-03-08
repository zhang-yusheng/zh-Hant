import argparse
import os

try:
    from opencc import OpenCC
except ImportError:
    print(
        "错误：需要安装 opencc-python 库，请执行命令：pip install opencc-python-reimplemented"
    )
    exit(1)


def scan_and_convert(base_dir):
    """扫描并转换指定目录下的 Markdown 文件"""
    cc = OpenCC("s2t")  # 初始化转换器

    # 验证目录是否存在
    if not os.path.isdir(base_dir):
        print(f"错误：目录不存在 '{os.path.abspath(base_dir)}'")
        exit(1)

    # 遍历目录树
    for root, dirs, files in os.walk(base_dir):
        # 排除 .git 目录
        if ".git" in dirs:
            dirs.remove(".git")

        # 处理 Markdown 文件
        for filename in files:
            if filename.endswith(".md"):
                filepath = os.path.join(root, filename)
                try:
                    # 读写文件内容
                    with open(filepath, "r+", encoding="utf-8") as f:
                        content = cc.convert(f.read())
                        f.seek(0)
                        f.write(content)
                        f.truncate()
                    print(f"已转换：{os.path.relpath(filepath, base_dir)}")
                except Exception as e:
                    print(f"处理失败 {os.path.relpath(filepath, base_dir)}：{str(e)}")


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description="将指定目录中的 Markdown 文件从简体中文转换为繁体中文（排除 .git 目录）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "dir", nargs="?", default=".", help="要处理的目标目录（默认为当前目录）"
    )
    args = parser.parse_args()

    # 执行转换
    scan_and_convert(args.dir)


if __name__ == "__main__":
    main()
