import json
import os
import requests
import copy


def get_user_path():
    """交互式获取路径，防止写死出错"""
    print("\n" + "=" * 60)
    print("👇 请直接粘贴那个 .focal.json 文件的完整路径，然后按回车：")
    print("提示：在文件上按【Shift+右键】选择【复制为路径】，然后粘贴到这里。")
    print("=" * 60)
    # 去除引号和空白
    return input("路径: ").strip().strip('"').strip("'")


def download_file_lines(repo, sha, file_path):
    """下载文件并按行拆分"""
    url_path = file_path.replace("\\", "/")
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{url_path}"
    print(f"   🌐 下载: {url_path} ...")
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.text.split('\n')
    except:
        pass
    return None


def get_code_snippet(lines, start, end):
    """根据行号切片代码"""
    if not lines: return None
    # JSON行号从1开始，List索引从0开始
    s = max(0, start - 1)
    e = min(len(lines), end)
    # 移除首尾空行
    code = "\n".join(lines[s:e])
    return code


def main():
    # 1. 交互式获取路径
    target_file = get_user_path()

    if not os.path.exists(target_file):
        print(f"❌ 错误：找不到文件 -> {target_file}")
        return

    print("🚀 开始处理...")

    # 2. 解析仓库信息 (从路径硬解)
    try:
        path_parts = target_file.replace("/", "\\").split("\\")
        # 假设结构 ...\data\作者\项目\文件
        repo = f"{path_parts[-3]}/{path_parts[-2]}"
        sha = os.path.basename(target_file).split('.')[0]
    except:
        print("⚠️ 路径结构识别失败，尝试默认仓库: 00anupam00/Informer")
        repo = "00anupam00/Informer"
        sha = os.path.basename(target_file).split('.')[0]

    print(f"📍 仓库: {repo}")
    print(f"📍 Commit: {sha}")

    # 3. 读取数据
    with open(target_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    final_data = copy.deepcopy(original_data)
    file_cache = {}

    print(f"🔍 扫描到 {len(final_data)} 个文件条目，开始下载并清洗...")

    # 4. 遍历处理
    for test_path, content in final_data.items():
        focal_path = content.get('focal_file')
        methods = content.get('methods')

        if not focal_path or not methods: continue

        # 下载
        if test_path not in file_cache:
            file_cache[test_path] = download_file_lines(repo, sha, test_path)
        if focal_path not in file_cache:
            file_cache[focal_path] = download_file_lines(repo, sha, focal_path)

        # 填充代码 + 删除废字段
        for method_name, method_info in methods.items():

            # --- A. 测试代码 ---
            t_start = method_info.get('line', 0)
            t_end = method_info.get('line_end', 0)
            t_code = get_code_snippet(file_cache.get(test_path), t_start, t_end)

            method_info['code_content'] = t_code

            # 删除不需要的字段
            for k in ['line', 'line_end', 'indent', 'docstring', 'complexity']:
                method_info.pop(k, None)

            # --- B. 被测代码 ---
            focal_info = method_info.get('focal_method')
            if focal_info:
                f_start = focal_info.get('line', 0)
                f_end = focal_info.get('line_end', 0)
                f_code = get_code_snippet(file_cache.get(focal_path), f_start, f_end)

                focal_info['code_content'] = f_code

                # 删除不需要的字段
                for k in ['line', 'line_end', 'indent', 'docstring', 'complexity']:
                    focal_info.pop(k, None)

    # 5. 保存结果 (带缩进的标准格式)
    output_filename = "final_clean_data.json"
    with open(output_filename, "w", encoding="utf-8") as out:
        # indent=4 保证输出格式漂亮，不再是一行
        json.dump(final_data, out, ensure_ascii=False, indent=4)

    print("\n" + "=" * 50)
    print(f"🎉 成功！纯净版 JSON 已保存为: {output_filename}")
    print("✅ 已填充真实代码")
    print("✅ 已删除行号/缩进字段")
    print("✅ 格式已展开（非单行）")
    print("=" * 50)


if __name__ == "__main__":
    main()