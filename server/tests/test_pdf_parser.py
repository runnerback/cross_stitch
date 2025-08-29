#!/usr/bin/env python
# 测试PDF解析功能

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
import json

def test_server_health():
    """测试服务器健康状态"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ 服务器健康检查通过")
            print(f"响应: {response.json()}")
        else:
            print("❌ 服务器健康检查失败")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        print("运行命令: python run.py")

def test_pdf_upload():
    """测试PDF上传和解析"""
    # 这里需要一个测试用的PDF文件
    test_pdf_path = Path("tests/test_files/sample.pdf")
    
    if not test_pdf_path.exists():
        print("⚠️  测试PDF文件不存在，跳过上传测试")
        print(f"请在 {test_pdf_path} 放置一个测试PDF文件")
        return
    
    try:
        with open(test_pdf_path, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            response = requests.post("http://localhost:8000/parse-pdf", files=files)
        
        if response.status_code == 200:
            print("✅ PDF解析成功")
            result = response.json()
            print(f"页数: {result.get('total_pages', 0)}")
            print(f"检测到的网格: {len(result.get('pages', []))} 页")
            
            # 保存结果到文件
            output_path = Path("tests/output/parse_result.json")
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {output_path}")
        else:
            print(f"❌ PDF解析失败: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")

def test_api_docs():
    """测试API文档是否可访问"""
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ API文档可访问: http://localhost:8000/docs")
        else:
            print("❌ API文档不可访问")
    except:
        print("❌ 无法访问API文档")

if __name__ == "__main__":
    print("=== Cross Stitch PDF解析服务测试 ===\n")
    
    print("1. 测试服务器健康状态...")
    test_server_health()
    
    print("\n2. 测试API文档...")
    test_api_docs()
    
    print("\n3. 测试PDF上传和解析...")
    test_pdf_upload()
    
    print("\n测试完成！")