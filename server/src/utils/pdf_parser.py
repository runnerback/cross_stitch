# PDF解析模块 - 专门用于Cross Stitch图案解析

import fitz  # PyMuPDF
from typing import Dict, List, Any, Tuple, Optional
import math
from collections import defaultdict

class CrossStitchPDFParser:
    """Cross Stitch PDF解析器"""
    
    def __init__(self):
        self.grid_tolerance = 1  # 网格检测容差（像素）
        self.min_grid_lines = 5  # 最少网格线数量（降低阈值）
        
    def parse(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        解析PDF主函数
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        result = {
            "pages": [],
            "pattern_info": self.extract_pattern_info(doc),
            "color_palette": [],
            "symbols": [],
            "total_pages": len(doc)
        }
        
        all_colors = set()
        all_symbols = []
        
        for page_num, page in enumerate(doc):
            page_data = self.parse_page(page, page_num)
            result["pages"].append(page_data)
            
            # 收集颜色和符号
            if page_data.get("colors"):
                # 从颜色字典列表中提取hex值
                for color in page_data["colors"]:
                    if isinstance(color, dict) and "hex" in color:
                        all_colors.add(color["hex"])
            if page_data.get("symbols"):
                all_symbols.extend(page_data["symbols"])
        
        # 整理颜色调色板
        result["color_palette"] = self.organize_color_palette(all_colors)
        result["symbols"] = self.organize_symbols(all_symbols)
        
        doc.close()
        return result
    
    def parse_page(self, page: fitz.Page, page_num: int) -> Dict[str, Any]:
        """
        解析单个页面
        """
        page_data = {
            "page_number": page_num + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "grid": None,
            "stitches": [],
            "colors": [],
            "symbols": [],
            "legend": []
        }
        
        # 获取所有绘图元素
        drawings = page.get_drawings()
        
        # 检测网格
        grid = self.detect_grid(drawings, page.rect)
        if grid:
            page_data["grid"] = grid
            
            # 基于网格提取十字绣图案
            page_data["stitches"] = self.extract_stitches(drawings, grid)
        
        # 提取文本（图例、颜色代码等）
        text_data = page.get_text("dict")
        page_data["legend"] = self.extract_legend(text_data)
        
        # 提取颜色信息
        page_data["colors"] = self.extract_colors(drawings)
        
        # 提取符号
        page_data["symbols"] = self.extract_symbols(text_data, grid)
        
        return page_data
    
    def detect_grid(self, drawings: List[dict], rect: fitz.Rect) -> Optional[Dict[str, Any]]:
        """
        检测并分析网格结构
        """
        horizontal_lines = []
        vertical_lines = []
        
        # 统计所有线条
        line_count = 0
        for drawing in drawings:
            for item in drawing.get("items", []):
                if item[0] == "l":  # 线条
                    line_count += 1
                    p1, p2 = item[1], item[2]
                    
                    # 检测水平线
                    if abs(p1.y - p2.y) < self.grid_tolerance:
                        horizontal_lines.append({
                            "y": (p1.y + p2.y) / 2,
                            "x1": min(p1.x, p2.x),
                            "x2": max(p1.x, p2.x),
                            "length": abs(p2.x - p1.x)
                        })
                    
                    # 检测垂直线
                    elif abs(p1.x - p2.x) < self.grid_tolerance:
                        vertical_lines.append({
                            "x": (p1.x + p2.x) / 2,
                            "y1": min(p1.y, p2.y),
                            "y2": max(p1.y, p2.y),
                            "length": abs(p2.y - p1.y)
                        })
        
        print(f"检测到 {line_count} 条线，其中水平线 {len(horizontal_lines)} 条，垂直线 {len(vertical_lines)} 条")
        
        # 过滤短线，只保留较长的网格线
        min_length = 50  # 最小线长
        horizontal_lines = [l for l in horizontal_lines if l["length"] > min_length]
        vertical_lines = [l for l in vertical_lines if l["length"] > min_length]
        
        print(f"过滤后：水平线 {len(horizontal_lines)} 条，垂直线 {len(vertical_lines)} 条")
        
        # 分析网格
        if len(horizontal_lines) >= self.min_grid_lines and len(vertical_lines) >= self.min_grid_lines:
            return self.analyze_grid_lines(horizontal_lines, vertical_lines)
        
        return None
    
    def analyze_grid_lines(self, h_lines: List[dict], v_lines: List[dict]) -> Dict[str, Any]:
        """
        分析网格线，计算网格参数
        """
        # 按位置排序
        h_lines.sort(key=lambda x: x["y"])
        v_lines.sort(key=lambda x: x["x"])
        
        # 计算网格间距
        h_spacings = [h_lines[i+1]["y"] - h_lines[i]["y"] for i in range(len(h_lines)-1)]
        v_spacings = [v_lines[i+1]["x"] - v_lines[i]["x"] for i in range(len(v_lines)-1)]
        
        print(f"水平间距样本: {h_spacings[:10] if h_spacings else []}")
        print(f"垂直间距样本: {v_spacings[:10] if v_spacings else []}")
        
        # 找出最常见的间距（即格子大小）
        cell_height = self.find_common_spacing(h_spacings) if h_spacings else 0
        cell_width = self.find_common_spacing(v_spacings) if v_spacings else 0
        
        print(f"检测到的格子大小: {cell_width:.2f} x {cell_height:.2f}")
        
        # 确定网格边界
        grid_top = h_lines[0]["y"]
        grid_bottom = h_lines[-1]["y"]
        grid_left = v_lines[0]["x"]
        grid_right = v_lines[-1]["x"]
        
        # 计算行列数 - 基于线条数量而不是间距
        rows = len(h_lines) - 1  # 线条数减1等于格子数
        cols = len(v_lines) - 1
        
        # 如果格子大小为0，尝试根据边界和行列数计算
        if cell_width == 0 and cols > 0:
            cell_width = (grid_right - grid_left) / cols
        if cell_height == 0 and rows > 0:
            cell_height = (grid_bottom - grid_top) / rows
        
        print(f"网格: {rows} 行 x {cols} 列")
        
        return {
            "detected": True,
            "rows": rows,
            "columns": cols,
            "cell_width": cell_width,
            "cell_height": cell_height,
            "bounds": {
                "top": grid_top,
                "bottom": grid_bottom,
                "left": grid_left,
                "right": grid_right
            },
            "total_cells": rows * cols
        }
    
    def find_common_spacing(self, spacings: List[float]) -> float:
        """
        找出最常见的间距值
        """
        if not spacings:
            return 0
        
        # 使用直方图方法找出最常见的间距
        spacing_counts = defaultdict(int)
        for spacing in spacings:
            # 四舍五入到最近的整数
            rounded = round(spacing, 1)
            spacing_counts[rounded] += 1
        
        # 返回出现次数最多的间距
        if spacing_counts:
            return max(spacing_counts.items(), key=lambda x: x[1])[0]
        return 0
    
    def extract_stitches(self, drawings: List[dict], grid: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        基于网格提取十字绣图案
        """
        if not grid or not grid.get("detected"):
            return []
        
        stitches = []
        bounds = grid["bounds"]
        cell_width = grid["cell_width"]
        cell_height = grid["cell_height"]
        
        # 检查cell_width和cell_height是否为0，避免除零错误
        if cell_width == 0 or cell_height == 0:
            print(f"警告: 网格单元大小为0 (宽:{cell_width}, 高:{cell_height})，跳过针迹提取")
            return []
        
        # 遍历所有绘图元素，查找十字或其他符号
        for drawing in drawings:
            color = self.parse_color(drawing.get("fill"))
            
            for item in drawing.get("items", []):
                if item[0] == "l":  # 线条（可能是十字的一部分）
                    p1, p2 = item[1], item[2]
                    # 计算线条所在的格子
                    grid_x = int((p1.x - bounds["left"]) / cell_width)
                    grid_y = int((p1.y - bounds["top"]) / cell_height)
                    
                    if 0 <= grid_x < grid["columns"] and 0 <= grid_y < grid["rows"]:
                        stitches.append({
                            "row": grid_y,
                            "col": grid_x,
                            "type": "cross",
                            "color": color
                        })
                
                elif item[0] == "re":  # 矩形（可能是填充的格子）
                    rect = item[1]
                    # 计算矩形中心所在的格子
                    center_x = (rect.x0 + rect.x1) / 2
                    center_y = (rect.y0 + rect.y1) / 2
                    
                    grid_x = int((center_x - bounds["left"]) / cell_width)
                    grid_y = int((center_y - bounds["top"]) / cell_height)
                    
                    if 0 <= grid_x < grid["columns"] and 0 <= grid_y < grid["rows"]:
                        stitches.append({
                            "row": grid_y,
                            "col": grid_x,
                            "type": "full",
                            "color": color
                        })
        
        return stitches
    
    def extract_colors(self, drawings: List[dict]) -> List[Dict[str, Any]]:
        """
        提取所有使用的颜色
        """
        colors = []
        seen_colors = set()
        
        for drawing in drawings:
            if "fill" in drawing:
                color = self.parse_color(drawing["fill"])
                if color and color not in seen_colors:
                    seen_colors.add(color)
                    colors.append({
                        "hex": color,
                        "rgb": self.hex_to_rgb(color)
                    })
        
        return colors
    
    def extract_symbols(self, text_dict: dict, grid: Optional[Dict]) -> List[Dict[str, Any]]:
        """
        提取符号信息
        """
        symbols = []
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 文本块
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        # 检查是否是单个字符（可能是符号）
                        if len(text) == 1 and not text.isspace():
                            bbox = span.get("bbox", [])
                            if bbox and grid and grid.get("bounds"):
                                # 检查网格单元大小是否有效
                                cell_width = grid.get("cell_width", 0)
                                cell_height = grid.get("cell_height", 0)
                                
                                if cell_width > 0 and cell_height > 0:
                                    # 计算符号所在的格子位置
                                    center_x = (bbox[0] + bbox[2]) / 2
                                    center_y = (bbox[1] + bbox[3]) / 2
                                    
                                    grid_x = int((center_x - grid["bounds"]["left"]) / cell_width)
                                    grid_y = int((center_y - grid["bounds"]["top"]) / cell_height)
                                    
                                    symbols.append({
                                        "symbol": text,
                                        "row": grid_y,
                                        "col": grid_x,
                                        "bbox": bbox
                                    })
        
        return symbols
    
    def extract_legend(self, text_dict: dict) -> List[Dict[str, Any]]:
        """
        提取图例信息（颜色代码、线程品牌等）
        """
        legend = []
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "")
                
                # 查找DMC、Anchor等线程代码
                if any(keyword in block_text.upper() for keyword in ["DMC", "ANCHOR", "MADEIRA"]):
                    legend.append({
                        "type": "thread_info",
                        "text": block_text.strip()
                    })
                
                # 查找颜色名称
                elif any(keyword in block_text.lower() for keyword in ["color", "colour", "颜色"]):
                    legend.append({
                        "type": "color_info",
                        "text": block_text.strip()
                    })
        
        return legend
    
    def extract_pattern_info(self, doc: fitz.Document) -> Dict[str, Any]:
        """
        提取图案基本信息
        """
        metadata = doc.metadata
        
        return {
            "title": metadata.get("title", "未命名图案"),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", "")
        }
    
    def organize_color_palette(self, colors: set) -> List[Dict[str, Any]]:
        """
        整理颜色调色板
        """
        palette = []
        for i, color in enumerate(colors):
            palette.append({
                "id": i + 1,
                "hex": color,
                "rgb": self.hex_to_rgb(color)
            })
        return palette
    
    def organize_symbols(self, symbols: List[Dict]) -> List[Dict[str, Any]]:
        """
        整理符号列表
        """
        unique_symbols = {}
        for symbol_data in symbols:
            symbol = symbol_data.get("symbol")
            if symbol and symbol not in unique_symbols:
                unique_symbols[symbol] = {
                    "symbol": symbol,
                    "positions": []
                }
            if symbol:
                unique_symbols[symbol]["positions"].append({
                    "row": symbol_data.get("row"),
                    "col": symbol_data.get("col")
                })
        
        return list(unique_symbols.values())
    
    def parse_color(self, color_value) -> Optional[str]:
        """
        解析颜色值，转换为十六进制格式
        """
        if color_value is None:
            return None
        
        if isinstance(color_value, int):
            # 转换整数颜色值为十六进制
            return f"#{color_value:06x}"
        elif isinstance(color_value, (list, tuple)) and len(color_value) == 3:
            # RGB值
            r, g, b = color_value
            return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        elif isinstance(color_value, str):
            return color_value
        
        return None
    
    def hex_to_rgb(self, hex_color: str) -> Dict[str, int]:
        """
        十六进制颜色转RGB
        """
        if not hex_color or not hex_color.startswith("#"):
            return {"r": 0, "g": 0, "b": 0}
        
        hex_color = hex_color.lstrip("#")
        try:
            return {
                "r": int(hex_color[0:2], 16),
                "g": int(hex_color[2:4], 16),
                "b": int(hex_color[4:6], 16)
            }
        except:
            return {"r": 0, "g": 0, "b": 0}