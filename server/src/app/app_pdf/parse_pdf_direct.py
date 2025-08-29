#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 直接解析Cross Stitch PDF文件

import sys
from pathlib import Path
# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.pdf_parser import CrossStitchPDFParser
import json
import argparse

def parse_pdf_file(pdf_path: str, output_json: bool = True):
    """
    直接解析PDF文件
    
    Args:
        pdf_path: PDF文件路径
        output_json: 是否输出为JSON文件
    """
    parser = CrossStitchPDFParser()
    
    # 读取PDF文件
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print(f"正在解析PDF文件: {pdf_path}")
    print(f"文件大小: {len(pdf_bytes) / 1024 / 1024:.2f} MB")
    
    # 解析PDF
    result = parser.parse(pdf_bytes)
    
    # 显示解析结果摘要
    print("\n=== 解析结果 ===")
    print(f"总页数: {result['total_pages']}")
    print(f"图案信息: {result['pattern_info'].get('title', '未命名')}")
    print(f"颜色数量: {len(result['color_palette'])}")
    print(f"符号数量: {len(result['symbols'])}")
    
    # 显示每页的网格信息
    for page in result['pages']:
        page_num = page['page_number']
        grid = page.get('grid')
        if grid and grid.get('detected'):
            print(f"\n页面 {page_num}:")
            print(f"  - 网格: {grid['rows']} 行 x {grid['columns']} 列")
            print(f"  - 格子大小: {grid['cell_width']:.1f} x {grid['cell_height']:.1f}")
            print(f"  - 检测到 {len(page['stitches'])} 个针迹")
        else:
            print(f"\n页面 {page_num}: 未检测到网格")
    
    # 保存为JSON文件
    if output_json:
        output_path = Path(pdf_path).with_suffix('.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_path}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description='解析Cross Stitch PDF文件')
    parser.add_argument('pdf_file', help='PDF文件路径')
    parser.add_argument('--no-json', action='store_true', help='不输出JSON文件')
    parser.add_argument('--show-colors', action='store_true', help='显示颜色列表')
    parser.add_argument('--show-symbols', action='store_true', help='显示符号列表')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not Path(args.pdf_file).exists():
        print(f"错误: 文件不存在 - {args.pdf_file}")
        sys.exit(1)
    
    # 解析PDF
    result = parse_pdf_file(args.pdf_file, not args.no_json)
    
    # 显示额外信息
    if args.show_colors and result['color_palette']:
        print("\n=== 颜色列表 ===")
        for color in result['color_palette']:
            rgb = color['rgb']
            print(f"颜色 {color['id']}: {color['hex']} (R:{rgb['r']}, G:{rgb['g']}, B:{rgb['b']})")
    
    if args.show_symbols and result['symbols']:
        print("\n=== 符号列表 ===")
        for symbol_info in result['symbols']:
            positions = len(symbol_info['positions'])
            print(f"符号 '{symbol_info['symbol']}': 出现 {positions} 次")

if __name__ == "__main__":
    main()