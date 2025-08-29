#!/bin/bash
# PDF转SVG快捷脚本

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: ./pdf2svg.sh <pdf文件> [选项]"
    echo "选项:"
    echo "  -o <目录>  指定输出目录"
    echo "  --merge    合并所有页面"
    echo "  --interactive  添加交互特性"
    echo ""
    echo "示例:"
    echo "  ./pdf2svg.sh input.pdf"
    echo "  ./pdf2svg.sh input.pdf -o output/"
    echo "  ./pdf2svg.sh input.pdf --merge --interactive"
    exit 1
fi

# 激活虚拟环境并运行
source venv/bin/activate
python src/app/app_pdf/pdf_to_svg.py "$@"