#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF转SVG工具 - 使用PyMuPDF直接转换
保持矢量特性，适合Cross Stitch图案的Web展示和交互
"""

import fitz  # PyMuPDF
import argparse
from pathlib import Path
import sys

def pdf_to_svg(pdf_path: str, output_dir: str = None, merge_pages: bool = False):
    """
    将PDF转换为SVG文件
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录，默认为PDF所在目录
        merge_pages: 是否合并多页为单个SVG（垂直排列）
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"错误: 文件不存在 - {pdf_path}")
        return False
    
    # 设置输出目录
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = pdf_path.parent
    
    # 打开PDF文档
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"错误: 无法打开PDF文件 - {e}")
        return False
    
    print(f"正在转换: {pdf_path}")
    print(f"页数: {len(doc)}")
    
    svg_files = []
    merged_svg = []
    total_height = 0
    max_width = 0
    
    # 转换每一页
    for page_num, page in enumerate(doc):
        print(f"转换第 {page_num + 1}/{len(doc)} 页...", end="")
        
        # 获取页面尺寸
        rect = page.rect
        width = rect.width
        height = rect.height
        max_width = max(max_width, width)
        
        # 获取SVG内容
        svg_text = page.get_svg_image()
        
        if merge_pages:
            # 提取SVG的内容部分（去掉外层svg标签）
            # 调整Y坐标偏移
            import re
            # 提取viewBox和内容
            viewbox_match = re.search(r'viewBox="([^"]+)"', svg_text)
            content_match = re.search(r'<svg[^>]*>(.*)</svg>', svg_text, re.DOTALL)
            
            if content_match:
                content = content_match.group(1)
                # 添加transform来偏移这一页
                transformed_content = f'<g transform="translate(0,{total_height})">{content}</g>'
                merged_svg.append(transformed_content)
                total_height += height
        else:
            # 保存单页SVG
            output_file = output_dir / f"{pdf_path.stem}_page_{page_num + 1}.svg"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(svg_text)
            svg_files.append(output_file)
            print(f" ✓ 保存到: {output_file}")
    
    # 如果需要合并页面
    if merge_pages and merged_svg:
        merged_file = output_dir / f"{pdf_path.stem}_merged.svg"
        merged_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{max_width}" 
     height="{total_height}"
     viewBox="0 0 {max_width} {total_height}">
    {"".join(merged_svg)}
</svg>'''
        with open(merged_file, "w", encoding="utf-8") as f:
            f.write(merged_content)
        print(f"\n合并的SVG保存到: {merged_file}")
        svg_files.append(merged_file)
    
    doc.close()
    
    print(f"\n转换完成! 共生成 {len(svg_files)} 个SVG文件")
    return svg_files

def add_interactive_features(svg_path: str, output_path: str = None):
    """
    为SVG添加交互特性（可选的后处理）
    
    Args:
        svg_path: SVG文件路径
        output_path: 输出路径，默认覆盖原文件
    """
    svg_path = Path(svg_path)
    if not output_path:
        output_path = svg_path
    
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()
    
    # 添加CSS样式，支持悬停效果
    css_style = '''
    <style>
        .clickable { cursor: pointer; }
        .clickable:hover { opacity: 0.8; }
        .grid-line { stroke: #ccc; stroke-width: 0.5; }
        .symbol { pointer-events: all; }
        .completed { opacity: 0.3; }
    </style>
    '''
    
    # 在<svg>标签后插入样式
    import re
    svg_content = re.sub(
        r'(<svg[^>]*>)',
        r'\1\n' + css_style,
        svg_content,
        count=1
    )
    
    # 添加JavaScript交互（可选）
    js_script = '''
    <script><![CDATA[
        // 点击格子标记完成
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('symbol')) {
                e.target.classList.toggle('completed');
            }
        });
    ]]></script>
    '''
    
    # 在</svg>前插入脚本
    svg_content = svg_content.replace('</svg>', js_script + '\n</svg>')
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print(f"交互特性已添加到: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description='将Cross Stitch PDF转换为SVG格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 转换单个PDF（每页一个SVG）
  python pdf_to_svg.py input.pdf
  
  # 指定输出目录
  python pdf_to_svg.py input.pdf -o output_dir/
  
  # 合并所有页面为单个SVG
  python pdf_to_svg.py input.pdf --merge
  
  # 添加交互特性
  python pdf_to_svg.py input.pdf --interactive
        '''
    )
    
    parser.add_argument('pdf_file', help='输入的PDF文件路径')
    parser.add_argument('-o', '--output', help='输出目录（默认为PDF所在目录）')
    parser.add_argument('--merge', action='store_true', 
                       help='合并所有页面为单个SVG文件')
    parser.add_argument('--interactive', action='store_true',
                       help='添加交互特性（悬停效果、点击标记等）')
    
    args = parser.parse_args()
    
    # 执行转换
    svg_files = pdf_to_svg(args.pdf_file, args.output, args.merge)
    
    # 如果需要添加交互特性
    if args.interactive and svg_files:
        print("\n添加交互特性...")
        for svg_file in svg_files:
            if svg_file.exists():
                interactive_file = svg_file.parent / f"{svg_file.stem}_interactive.svg"
                add_interactive_features(svg_file, interactive_file)

if __name__ == "__main__":
    main()