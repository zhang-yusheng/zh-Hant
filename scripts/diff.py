import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import opencc
import difflib
import re

# 定義常見文字檔案擴展名
TEXT_FILE_EXTENSIONS = {
    '.md', '.txt', '.html', '.htm', '.xml', '.yaml', '.yml',
    '.toml', '.ini'
}

def is_text_file(file_path):
    """判斷檔案是否為文字檔案"""
    return file_path.suffix.lower() in TEXT_FILE_EXTENSIONS

def load_custom_phrase_map(file_path):
    phrase_map = {}
    if not Path(file_path).exists():
        print(f"字典檔不存在：{file_path}")
        return phrase_map
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=>" not in line:
                print(f"格式錯誤（缺少 =>）: {line}")
                continue
            left, right = line.split("=>", 1)
            phrase_map[left.strip()] = right.strip()
    return phrase_map

def normalize_content(content):
    content = re.sub(r' +$', '', content, flags=re.MULTILINE)
    content = content.replace('\r\n', '\n')
    return content

def convert_files(directory, converter):
    for file_path in directory.glob("**/*"):
        if file_path.is_file() and is_text_file(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(converter.convert(content))
            except Exception as e:
                print(f"轉換失敗 {file_path}: {e}")

def create_semantic_diff(source_dir, target_dir, output_file, phrase_map, t2s_converter):
    # 只收集文字檔案
    source_files = {p.relative_to(source_dir): p for p in Path(source_dir).glob("**/*") 
                   if p.is_file() and is_text_file(p)}
    target_files = {p.relative_to(target_dir): p for p in Path(target_dir).glob("**/*") 
                   if p.is_file() and is_text_file(p)}
    
    all_files = sorted(set(source_files.keys()) | set(target_files.keys()))
    
    has_diff = False
    skipped_log = []
    with open(output_file, "w", encoding="utf-8") as diff_file:
        for rel_path in all_files:
            source_path = source_files.get(rel_path)
            target_path = target_files.get(rel_path)
            
            # 處理只存在於其中一方的檔案
            if not source_path:
                # 檔案僅存在於target
                source_lines = []
                with open(target_path, "r", encoding="utf-8") as f:
                    target_lines = normalize_content(f.read()).splitlines()
                
                raw_diff = list(difflib.unified_diff(
                    source_lines, target_lines,
                    fromfile=f"[不存在] {rel_path}",
                    tofile=str(target_path),
                    lineterm='', n=3
                ))
                
                diff_file.write('\n'.join(raw_diff))
                diff_file.write('\n\n')
                has_diff = True
                continue
            
            if not target_path:
                # 檔案僅存在於source
                with open(source_path, "r", encoding="utf-8") as f:
                    source_lines = normalize_content(f.read()).splitlines()
                target_lines = []
                
                raw_diff = list(difflib.unified_diff(
                    source_lines, target_lines,
                    fromfile=str(source_path),
                    tofile=f"[不存在] {rel_path}",
                    lineterm='', n=3
                ))
                
                diff_file.write('\n'.join(raw_diff))
                diff_file.write('\n\n')
                has_diff = True
                continue
            
            # 處理兩邊都存在的檔案
            try:
                with open(source_path, "r", encoding="utf-8") as f:
                    source_lines = normalize_content(f.read()).splitlines()
                
                with open(target_path, "r", encoding="utf-8") as f:
                    target_lines = normalize_content(f.read()).splitlines()
                
                raw_diff = list(difflib.unified_diff(
                    source_lines, target_lines,
                    fromfile=str(source_path),
                    tofile=str(target_path),
                    lineterm='', n=3
                ))
                
                if not raw_diff:
                    continue  # 無差異
                
                diff_blocks = []
                current_block = []
                for line in raw_diff:
                    if line.startswith('@@') and current_block:
                        diff_blocks.append(current_block)
                        current_block = [line]
                    else:
                        current_block.append(line)
                if current_block:
                    diff_blocks.append(current_block)
                
                filtered_blocks = []
                for block in diff_blocks:
                    minus_lines = [l[1:].strip() for l in block if l.startswith('-') and not l.startswith('---')]
                    plus_lines = [l[1:].strip() for l in block if l.startswith('+') and not l.startswith('+++')]
                    skip = False
                    for simp, trad in phrase_map.items():
                        trad_in_simp = t2s_converter.convert(trad)
                        if any(simp in line for line in minus_lines) and any(trad_in_simp in line for line in plus_lines):
                            skipped_log.append(f"[SKIPPED] file: {rel_path}\n- {next((l for l in minus_lines if simp in l), '')}\n+ {next((l for l in plus_lines if trad_in_simp in l), '')}\n")
                            skip = True
                            break
                    if not skip:
                        filtered_blocks.append(block)
                
                if filtered_blocks:
                    diff_file.write(f"--- {source_path}\n+++ {target_path}\n")
                    has_diff = True
                    for block in filtered_blocks:
                        diff_file.write('\n'.join(block))
                        diff_file.write('\n\n')
            
            except Exception as e:
                print(f"比較失敗 {rel_path}: {e}")
                continue

    if skipped_log:
        log_path = Path(output_file).with_suffix(".skipped.log")
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write('\n'.join(skipped_log))

    if not has_diff:
        Path(output_file).unlink()
        return False
    return True

def main():
    load_dotenv()
    yusheng_path = Path(os.getenv("YUSHENG_PATH", ""))
    zhHant_path = Path(os.getenv("ZHHANT_PATH", ""))
    phrase_map = load_custom_phrase_map("custom_phrases.txt")
    folders = ["albums", "articles", "letters", "more", "performances", "shows", "talks"]

    if not yusheng_path.exists() or not zhHant_path.exists():
        print("錯誤：請確認 YUSHENG_PATH 和 ZHHANT_PATH 是否正確")
        return

    temp_dir = Path("temp_zhHant_simplified")
    diff_dir = Path("diff_output")

    for dir_path in [temp_dir, diff_dir]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
        dir_path.mkdir()

    t2s_converter = opencc.OpenCC("tw2s")

    print("轉換繁體 repo 為簡體（以便對照）...")
    for folder in folders:
        src = zhHant_path / folder
        dest = temp_dir / folder
        if src.exists():
            shutil.copytree(src, dest)
            convert_files(dest, t2s_converter)

    print("\n生成差異檔...")
    for folder in folders:
        source = yusheng_path / folder
        target = temp_dir / folder
        diff_file = diff_dir / f"{folder}.diff"

        if not source.exists() or not target.exists():
            print(f"略過：{folder}")
            continue

        if create_semantic_diff(source, target, diff_file, phrase_map, t2s_converter):
            print(f"✅ 差異輸出：{diff_file}")
        else:
            print(f"✅ 無差異：{folder}")

    shutil.rmtree(temp_dir)
    print("\n完成 ✅ 所有差異輸出於 diff_output/")

if __name__ == "__main__":
    main()