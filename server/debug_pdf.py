#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 调试PDF解析，查看PDF内容

import fitz  # PyMuPDF
import sys
import json
from pathlib import Path

def debug_pdf(pdf_path: str):
    """调试PDF内容"""
    doc = fitz.open(pdf_path)
    
    print(f"PDF文件: {pdf_path}")
    print(f"页数: {len(doc)}")
    
    for page_num, page in enumerate(doc):
        print(f"\n=== 页面 {page_num + 1} ===")
        print(f"尺寸: {page.rect.width} x {page.rect.height}")
        
        # 获取所有绘图元素
        drawings = page.get_drawings()
        print(f"绘图元素数量: {len(drawings)}")
        
        # 统计不同类型的元素
        lines = []
        rects = []
        curves = []
        
        for drawing in drawings:
            for item in drawing.get("items", []):
                if item[0] == "l":  # 线条
                    lines.append(item)
                elif item[0] == "re":  # 矩形
                    rects.append(item)
                elif item[0] == "qu":  # 曲线
                    curves.append(item)
        
        print(f"  - 线条: {len(lines)}")
        print(f"  - 矩形: {len(rects)}")
        print(f"  - 曲线: {len(curves)}")
        
        # 分析线条方向
        if lines:
            horizontal = 0
            vertical = 0
            diagonal = 0
            
            for line in lines:
                p1, p2 = line[1], line[2]
                dx = abs(p2.x - p1.x)
                dy = abs(p2.y - p1.y)
                
                if dy < 1:  # 水平线
                    horizontal += 1
                elif dx < 1:  # 垂直线
                    vertical += 1
                else:  # 斜线
                    diagonal += 1
            
            print(f"  线条方向分析:")
            print(f"    - 水平线: {horizontal}")
            print(f"    - 垂直线: {vertical}")
            print(f"    - 斜线: {diagonal}")
        
        # 获取文本
        text_dict = page.get_text("dict")
        text_blocks = text_dict.get("blocks", [])
        print(f"\n文本块数量: {len(text_blocks)}")
        
        # 提取所有文本
        all_text = []
        for block in text_blocks:
            if block.get("type") == 0:  # 文本块
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            all_text.append(text)
        
        if all_text:
            print(f"文本内容样例（前10个）:")
            for i, text in enumerate(all_text[:10]):
                print(f"  {i+1}. '{text}'")
        
        # 查看前几个绘图元素的详细信息
        if drawings:
            print(f"\n前3个绘图元素详情:")
            for i, drawing in enumerate(drawings[:3]):
                print(f"\n  绘图元素 {i+1}:")
                if "color" in drawing:
                    print(f"    颜色: {drawing['color']}")
                if "fill" in drawing:
                    print(f"    填充: {drawing['fill']}")
                if "width" in drawing:
                    print(f"    线宽: {drawing['width']}")
                
                items = drawing.get("items", [])
                if items:
                    first_item = items[0]
                    if first_item[0] == "l":
                        p1, p2 = first_item[1], first_item[2]
                        print(f"    线条: ({p1.x:.1f}, {p1.y:.1f}) -> ({p2.x:.1f}, {p2.y:.1f})")
                    elif first_item[0] == "re":
                        rect = first_item[1]
                        print(f"    矩形: x={rect.x0:.1f}, y={rect.y0:.1f}, w={rect.width:.1f}, h={rect.height:.1f}")
        
        # 保存绘图数据到JSON以便详细分析
        output_path = Path(pdf_path).with_suffix(".debug.json")
        debug_data = {
            "page": page_num + 1,
            "size": {"width": page.rect.width, "height": page.rect.height},
            "drawings_count": len(drawings),
            "lines": len(lines),
            "rects": len(rects),
            "curves": len(curves),
            "text_blocks": len(text_blocks),
            "sample_drawings": []
        }
        
        # 添加一些绘图样例
        for drawing in drawings[:10]:
            sample = {
                "color": drawing.get("color"),
                "fill": drawing.get("fill"),
                "width": drawing.get("width"),
                "items_count": len(drawing.get("items", []))
            }
            debug_data["sample_drawings"].append(sample)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)
        print(f"\n调试数据已保存到: {output_path}")
    
    doc.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python debug_pdf.py <pdf文件路径>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"错误: 文件不存在 - {pdf_path}")
        sys.exit(1)
    
    debug_pdf(pdf_path)