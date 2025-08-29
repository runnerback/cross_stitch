#!/usr/bin/env python
# 启动FastAPI服务器

import uvicorn

if __name__ == "__main__":
    # 启动服务器
    print("正在启动Cross Stitch PDF解析服务器...")
    print("访问 http://localhost:8000 查看API")
    print("访问 http://localhost:8000/docs 查看交互式API文档")
    
    uvicorn.run(
        "src.app.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )