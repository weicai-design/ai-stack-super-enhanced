"""
文件生成服务
支持生成Word/Excel/PPT/PDF等文件
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import io
import json

class FileGenerationService:
    """
    文件生成服务
    
    功能：
    1. Word文档生成
    2. Excel表格生成
    3. PPT演示文稿生成
    4. PDF文档生成
    5. 图片生成
    6. 模板管理
    """
    
    def __init__(self):
        self.templates = {}
        self.use_libraries = {
            "word": False,  # python-docx
            "excel": True,  # openpyxl (已在ERP中使用)
            "ppt": False,   # python-pptx
            "pdf": False    # reportlab/weasyprint
        }
        
    async def generate_word(
        self,
        content: str,
        template: Optional[str] = None,
        output_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成Word文档
        
        Args:
            content: 内容（Markdown或HTML格式）
            template: 模板名称
            output_path: 输出路径
            title: 文档标题
            
        Returns:
            包含文件数据和元数据的字典
        """
        try:
            # 检查是否安装了python-docx
            try:
                from docx import Document
                from docx.shared import Inches, Pt
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                self.use_libraries["word"] = True
            except ImportError:
                self.use_libraries["word"] = False
            
            if self.use_libraries["word"]:
                # 使用python-docx生成Word文档
                doc = Document()
                
                # 添加标题
                if title:
                    heading = doc.add_heading(title, 0)
                    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # 解析Markdown内容（简单实现）
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        doc.add_paragraph()
                        continue
                    
                    # 处理标题
                    if line.startswith('# '):
                        doc.add_heading(line[2:], level=1)
                    elif line.startswith('## '):
                        doc.add_heading(line[3:], level=2)
                    elif line.startswith('### '):
                        doc.add_heading(line[4:], level=3)
                    # 处理列表
                    elif line.startswith('- ') or line.startswith('* '):
                        doc.add_paragraph(line[2:], style='List Bullet')
                    elif line.startswith('1. ') or line.startswith('2. '):
                        doc.add_paragraph(line[3:], style='List Number')
                    else:
                        doc.add_paragraph(line)
                
                # 保存到内存
                buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                file_data = buffer.read()
                
                return {
                    "success": True,
                    "file_data": file_data,
                    "format": "docx",
                    "filename": output_path or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    "size": len(file_data),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用方案：返回HTML格式（浏览器可以打开）
                html_content = self._markdown_to_html(content, title)
                return {
                    "success": True,
                    "file_data": html_content.encode('utf-8'),
                    "format": "html",
                    "filename": output_path or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    "note": "python-docx未安装，返回HTML格式",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _markdown_to_html(self, markdown: str, title: Optional[str] = None) -> str:
        """简单的Markdown转HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title or '文档'}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #777; }}
        ul, ol {{ margin-left: 20px; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
"""
        if title:
            html += f"<h1>{title}</h1>\n"
        
        lines = markdown.split('\n')
        for line in lines:
            if line.startswith('# '):
                html += f"<h1>{line[2:]}</h1>\n"
            elif line.startswith('## '):
                html += f"<h2>{line[3:]}</h2>\n"
            elif line.startswith('### '):
                html += f"<h3>{line[4:]}</h3>\n"
            elif line.startswith('- ') or line.startswith('* '):
                html += f"<li>{line[2:]}</li>\n"
            else:
                html += f"<p>{line}</p>\n"
        
        html += """
</body>
</html>
"""
        return html
    
    async def generate_excel(
        self,
        data: List[List[Any]],
        headers: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        sheet_name: str = "Sheet1"
    ) -> Dict[str, Any]:
        """
        生成Excel表格
        
        Args:
            data: 数据（二维列表）
            headers: 表头
            output_path: 输出路径
            sheet_name: 工作表名称
            
        Returns:
            包含文件数据和元数据的字典
        """
        try:
            # 使用openpyxl（已在ERP中使用）
            try:
                from openpyxl import Workbook
                from openpyxl.styles import Font, Alignment
                self.use_libraries["excel"] = True
            except ImportError:
                self.use_libraries["excel"] = False
            
            if self.use_libraries["excel"]:
                wb = Workbook()
                ws = wb.active
                ws.title = sheet_name
                
                # 添加表头
                if headers:
                    for col_idx, header in enumerate(headers, 1):
                        cell = ws.cell(row=1, column=col_idx, value=header)
                        cell.font = Font(bold=True)
                        cell.alignment = Alignment(horizontal='center')
                
                # 添加数据
                start_row = 2 if headers else 1
                for row_idx, row_data in enumerate(data, start_row):
                    for col_idx, value in enumerate(row_data, 1):
                        ws.cell(row=row_idx, column=col_idx, value=value)
                
                # 自动调整列宽
                for col in ws.columns:
                    max_length = 0
                    col_letter = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[col_letter].width = adjusted_width
                
                # 保存到内存
                buffer = io.BytesIO()
                wb.save(buffer)
                buffer.seek(0)
                file_data = buffer.read()
                
                return {
                    "success": True,
                    "file_data": file_data,
                    "format": "xlsx",
                    "filename": output_path or f"excel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "size": len(file_data),
                    "rows": len(data) + (1 if headers else 0),
                    "columns": len(headers) if headers else (len(data[0]) if data else 0),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用方案：返回CSV格式
                csv_lines = []
                if headers:
                    csv_lines.append(",".join(str(h) for h in headers))
                for row in data:
                    csv_lines.append(",".join(str(v) for v in row))
                csv_content = "\n".join(csv_lines)
                
                return {
                    "success": True,
                    "file_data": csv_content.encode('utf-8-sig'),  # UTF-8 BOM for Excel
                    "format": "csv",
                    "filename": output_path or f"excel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "note": "openpyxl未安装，返回CSV格式",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_ppt(
        self,
        slides: List[Dict[str, Any]],
        template: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        生成PPT演示文稿
        
        Args:
            slides: 幻灯片列表
            template: 模板名称
            output_path: 输出路径
            
        Returns:
            PPT文件字节流
        """
        # TODO: 使用python-pptx库生成PPT
        
        return b""
    
    async def generate_pdf(
        self,
        content: str,
        template: Optional[str] = None,
        output_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成PDF文档
        
        Args:
            content: 内容（HTML或Markdown格式）
            template: 模板名称
            output_path: 输出路径
            title: 文档标题
            
        Returns:
            包含文件数据和元数据的字典
        """
        try:
            # 尝试使用weasyprint（推荐，支持HTML转PDF）
            try:
                from weasyprint import HTML
                self.use_libraries["pdf"] = True
                pdf_method = "weasyprint"
            except ImportError:
                # 尝试使用reportlab
                try:
                    from reportlab.lib.pagesizes import letter, A4
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                    from reportlab.lib.styles import getSampleStyleSheet
                    self.use_libraries["pdf"] = True
                    pdf_method = "reportlab"
                except ImportError:
                    self.use_libraries["pdf"] = False
                    pdf_method = None
            
            if self.use_libraries["pdf"] and pdf_method == "weasyprint":
                # 使用weasyprint生成PDF
                html_content = self._markdown_to_html(content, title)
                pdf_bytes = HTML(string=html_content).write_pdf()
                
                return {
                    "success": True,
                    "file_data": pdf_bytes,
                    "format": "pdf",
                    "filename": output_path or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    "size": len(pdf_bytes),
                    "method": "weasyprint",
                    "timestamp": datetime.now().isoformat()
                }
            elif self.use_libraries["pdf"] and pdf_method == "reportlab":
                # 使用reportlab生成PDF
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                
                if title:
                    story.append(Paragraph(title, styles['Title']))
                    story.append(Spacer(1, 12))
                
                # 解析内容
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        story.append(Spacer(1, 6))
                        continue
                    story.append(Paragraph(line, styles['Normal']))
                
                doc.build(story)
                buffer.seek(0)
                pdf_bytes = buffer.read()
                
                return {
                    "success": True,
                    "file_data": pdf_bytes,
                    "format": "pdf",
                    "filename": output_path or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    "size": len(pdf_bytes),
                    "method": "reportlab",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 备用方案：返回HTML格式（浏览器可以打印为PDF）
                html_content = self._markdown_to_html(content, title)
                return {
                    "success": True,
                    "file_data": html_content.encode('utf-8'),
                    "format": "html",
                    "filename": output_path or f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    "note": "PDF库未安装，返回HTML格式（可在浏览器中打印为PDF）",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_image(
        self,
        content: str,
        width: int = 800,
        height: int = 600,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        生成图片
        
        Args:
            content: 内容（文本或HTML）
            width: 宽度
            height: 高度
            output_path: 输出路径
            
        Returns:
            图片字节流
        """
        # TODO: 使用PIL/Pillow生成图片
        
        return b""

