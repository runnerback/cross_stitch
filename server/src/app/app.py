from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utils.pdf_parser import CrossStitchPDFParser
from typing import Dict, List, Any
import json

app = FastAPI(title="Cross Stitch PDF Parser")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Cross Stitch PDF解析服务", "status": "运行中"}

@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """
    解析Cross Stitch PDF文件
    提取矢量图形、文本、颜色等信息
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="文件必须是PDF格式")
    
    try:
        # 读取上传的PDF文件
        pdf_bytes = await file.read()
        
        # 使用专门的解析器
        parser = CrossStitchPDFParser()
        result = parser.parse(pdf_bytes)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF解析失败: {str(e)}")

@app.post("/parse-pdf-simple")
async def parse_pdf_simple(file: UploadFile = File(...)):
    """
    简单PDF解析接口（用于快速测试）
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="文件必须是PDF格式")
    
    try:
        pdf_bytes = await file.read()
        result = parse_cross_stitch_pdf_simple(pdf_bytes)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF解析失败: {str(e)}")

def parse_cross_stitch_pdf_simple(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    简单解析Cross Stitch PDF
    提取基本信息用于测试
    """
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    result = {
        "pages": [],
        "metadata": {},
        "total_pages": len(doc)
    }
    
    # 提取文档元数据
    result["metadata"] = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "keywords": doc.metadata.get("keywords", ""),
    }
    
    # 遍历每一页
    for page_num, page in enumerate(doc):
        page_data = {
            "page_number": page_num + 1,
            "width": page.rect.width,
            "height": page.rect.height,
            "graphics": [],
            "texts": [],
            "grid_info": {}
        }
        
        # 提取矢量图形（路径、线条等）
        drawings = page.get_drawings()
        for drawing in drawings:
            graphic_info = parse_drawing(drawing)
            if graphic_info:
                page_data["graphics"].append(graphic_info)
        
        # 提取文本信息
        text_dict = page.get_text("dict")
        page_data["texts"] = extract_text_info(text_dict)
        
        # 分析格子结构
        page_data["grid_info"] = analyze_grid_structure(page_data["graphics"])
        
        result["pages"].append(page_data)
    
    doc.close()
    return result

def parse_drawing(drawing: dict) -> Dict[str, Any]:
    """
    解析单个矢量图形元素
    """
    graphic_info = {
        "type": "",
        "items": [],
        "color": None,
        "fill": None,
        "stroke_width": 1
    }
    
    # 提取颜色信息
    if "color" in drawing:
        graphic_info["color"] = drawing["color"]
    
    if "fill" in drawing:
        graphic_info["fill"] = drawing["fill"]
    
    if "width" in drawing:
        graphic_info["stroke_width"] = drawing["width"]
    
    # 解析图形项
    for item in drawing.get("items", []):
        item_type = item[0]
        
        if item_type == "l":  # 线条
            graphic_info["type"] = "line"
            graphic_info["items"].append({
                "type": "line",
                "start": {"x": item[1].x, "y": item[1].y},
                "end": {"x": item[2].x, "y": item[2].y}
            })
        
        elif item_type == "re":  # 矩形
            graphic_info["type"] = "rect"
            rect = item[1]
            graphic_info["items"].append({
                "type": "rect",
                "x": rect.x0,
                "y": rect.y0,
                "width": rect.width,
                "height": rect.height
            })
        
        elif item_type == "qu":  # 曲线
            graphic_info["type"] = "curve"
            quad = item[1]
            graphic_info["items"].append({
                "type": "curve",
                "start": {"x": quad.p0.x, "y": quad.p0.y},
                "control": {"x": quad.p1.x, "y": quad.p1.y},
                "end": {"x": quad.p2.x, "y": quad.p2.y}
            })
    
    return graphic_info if graphic_info["items"] else None

def extract_text_info(text_dict: dict) -> List[Dict[str, Any]]:
    """
    提取文本信息（符号、颜色代码等）
    """
    texts = []
    
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # 文本块
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text_info = {
                        "text": span.get("text", ""),
                        "font": span.get("font", ""),
                        "size": span.get("size", 0),
                        "flags": span.get("flags", 0),
                        "color": span.get("color", 0),
                        "bbox": span.get("bbox", [])
                    }
                    if text_info["text"].strip():
                        texts.append(text_info)
    
    return texts

def analyze_grid_structure(graphics: List[Dict]) -> Dict[str, Any]:
    """
    分析格子结构
    识别十字绣图案的网格布局
    """
    grid_info = {
        "detected": False,
        "rows": 0,
        "columns": 0,
        "cell_width": 0,
        "cell_height": 0,
        "grid_lines": []
    }
    
    # 收集所有线条
    horizontal_lines = []
    vertical_lines = []
    
    for graphic in graphics:
        if graphic.get("type") == "line":
            for item in graphic.get("items", []):
                if item["type"] == "line":
                    # 判断是水平线还是垂直线
                    if abs(item["start"]["y"] - item["end"]["y"]) < 0.1:
                        horizontal_lines.append(item)
                    elif abs(item["start"]["x"] - item["end"]["x"]) < 0.1:
                        vertical_lines.append(item)
    
    # 如果有足够的线条，则认为检测到网格
    if len(horizontal_lines) > 5 and len(vertical_lines) > 5:
        grid_info["detected"] = True
        grid_info["rows"] = len(horizontal_lines) - 1
        grid_info["columns"] = len(vertical_lines) - 1
        
        # 计算平均格子大小
        if len(horizontal_lines) > 1:
            y_positions = sorted([line["start"]["y"] for line in horizontal_lines])
            if len(y_positions) > 1:
                grid_info["cell_height"] = (y_positions[-1] - y_positions[0]) / (len(y_positions) - 1)
        
        if len(vertical_lines) > 1:
            x_positions = sorted([line["start"]["x"] for line in vertical_lines])
            if len(x_positions) > 1:
                grid_info["cell_width"] = (x_positions[-1] - x_positions[0]) / (len(x_positions) - 1)
    
    return grid_info

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)