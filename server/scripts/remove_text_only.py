#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅删除文本层的水印，完全保留图像层
使用redaction但只针对文本，不触及图像
"""

import fitz
import sys

def remove_text_watermark_only(input_pdf: str, output_pdf: str):
    """
    只删除文本水印，保留所有图像
    
    Args:
        input_pdf: 输入PDF文件路径
        output_pdf: 输出PDF文件路径
    """
    try:
        # 打开PDF文档
        doc = fitz.open(input_pdf)
        
        print(f"正在处理PDF: {input_pdf}")
        print(f"总页数: {len(doc)}")
        
        watermark_text = "仅限办理理想车辆保险使用"
        
        # 处理每一页
        for page_num, page in enumerate(doc):
            print(f"\n处理第 {page_num + 1} 页...")
            
            # 获取页面信息
            page_rect = page.rect
            print(f"  页面尺寸: {page_rect}")
            
            # 获取所有图像信息（用于验证）
            images_before = page.get_images()
            print(f"  图像数量: {len(images_before)}")
            
            # 查找水印文本
            text_instances = page.search_for(watermark_text)
            
            if text_instances:
                print(f"  找到 {len(text_instances)} 个水印文本")
                
                # 对每个水印文本实例添加redaction注释
                # 但使用特殊设置以保护图像
                for i, rect in enumerate(text_instances):
                    print(f"    水印 {i+1} 位置: {rect}")
                    
                    # 添加redaction注释
                    # 重要：只标记文本区域，不扩大范围
                    redact_rect = fitz.Rect(
                        rect.x0,
                        rect.y0,
                        rect.x1,
                        rect.y1
                    )
                    
                    # 添加redaction注释
                    page.add_redact_annot(redact_rect)
                
                # 应用redactions
                # 重要：使用特殊选项只删除文本
                # images=PDF_REDACT_IMAGE_NONE 确保不删除图像
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
                print("  已应用文本删除")
            
            # 验证图像是否保留
            images_after = page.get_images()
            if len(images_after) == len(images_before):
                print(f"  ✓ 图像保持不变: {len(images_after)} 个")
            else:
                print(f"  ⚠️ 图像数量改变: {len(images_before)} -> {len(images_after)}")
        
        # 保存处理后的PDF
        doc.save(output_pdf, garbage=4, deflate=True)
        
        print(f"\n验证结果...")
        
        # 重新打开验证
        verify_doc = fitz.open(output_pdf)
        orig_doc = fitz.open(input_pdf)
        
        for page_num in range(len(verify_doc)):
            new_page = verify_doc[page_num]
            old_page = orig_doc[page_num]
            
            # 检查水印
            text = new_page.get_text()
            if watermark_text in text:
                print(f"  第 {page_num + 1} 页: 水印仍存在")
            else:
                print(f"  第 {page_num + 1} 页: 水印已删除")
            
            # 比较图像
            old_images = old_page.get_images()
            new_images = new_page.get_images()
            
            if len(old_images) == len(new_images):
                print(f"  第 {page_num + 1} 页: 图像完整 ({len(new_images)} 个)")
                
                # 检查每个图像是否相同
                for i, (old_img, new_img) in enumerate(zip(old_images, new_images)):
                    if old_img[0] == new_img[0]:  # xref相同
                        print(f"    图像 {i+1}: ✓ 保持不变")
                    else:
                        print(f"    图像 {i+1}: ⚠️ 可能有变化")
            else:
                print(f"  第 {page_num + 1} 页: 图像数量变化 ({len(old_images)} -> {len(new_images)})")
        
        verify_doc.close()
        orig_doc.close()
        doc.close()
        
        print(f"\n✅ 处理完成！")
        print(f"输出文件: {output_pdf}")
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python remove_text_only.py <输入PDF> <输出PDF>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    remove_text_watermark_only(input_file, output_file)