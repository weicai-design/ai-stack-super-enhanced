"""
Office Document Handler for AI Stack Super Enhanced
Comprehensive office document processing with advanced text extraction

Version: 1.0.0
Author: AI Stack Super Enhanced Team
Created: 2024
"""

import logging
import xml.etree.ElementTree as ET
import zipfile
from typing import Dict, List

from . import FileMetadata, FileProcessorBase, ProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class OfficeDocumentHandler(FileProcessorBase):
    """
    Advanced office document processor supporting:
    - Microsoft Office formats (doc, docx, xls, xlsx, ppt, pptx)
    - OpenDocument formats (odt, ods, odp)
    - PDF documents
    - Advanced metadata extraction
    - Structured content parsing
    """

    def __init__(self):
        super().__init__()
        self.processor_name = "OfficeDocumentHandler"

        # Supported file extensions
        self.supported_extensions = [
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            "pdf",
            "odt",
            "ods",
            "odp",
        ]

        # Supported MIME types
        self.supported_mime_types = [
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "application/vnd.ms-excel",
            "application/vnd.ms-powerpoint",
            "application/pdf",
            "application/vnd.oasis.opendocument",
        ]

        # Processing libraries
        self._text_extraction_libs = {}
        self._pdf_processor = None
        self._docx_processor = None
        self._excel_processor = None
        self._presentation_processor = None

    def initialize(self) -> bool:
        """Initialize office document handler with all required libraries"""
        try:
            self._load_text_extraction_libraries()
            self._initialize_pdf_processor()
            self._initialize_docx_processor()
            self._initialize_excel_processor()
            self._initialize_presentation_processor()

            self._initialized = True
            logger.info("OfficeDocumentHandler initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OfficeDocumentHandler: {str(e)}")
            self._initialized = False
            return False

    def _load_text_extraction_libraries(self):
        """Load text extraction libraries dynamically"""
        libs_to_try = [
            ("pdfplumber", "pdfplumber"),
            ("docx", "docx"),
            ("openpyxl", "openpyxl"),
            ("PyPDF2", "PyPDF2"),
            ("python-pptx", "pptx"),
            ("odf", "odf"),
        ]

        for lib_name, import_name in libs_to_try:
            try:
                module = __import__(import_name)
                self._text_extraction_libs[lib_name] = module
                logger.debug(f"Loaded text extraction library: {lib_name}")
            except ImportError:
                logger.warning(f"Text extraction library not available: {lib_name}")

    def _initialize_pdf_processor(self):
        """Initialize PDF processing capabilities"""
        if "pdfplumber" in self._text_extraction_libs:
            self._pdf_processor = self._text_extraction_libs["pdfplumber"]
            logger.debug("PDF processor initialized with pdfplumber")
        elif "PyPDF2" in self._text_extraction_libs:
            self._pdf_processor = self._text_extraction_libs["PyPDF2"]
            logger.debug("PDF processor initialized with PyPDF2")
        else:
            logger.warning("No PDF processing library available")

    def _initialize_docx_processor(self):
        """Initialize DOCX processing capabilities"""
        if "docx" in self._text_extraction_libs:
            self._docx_processor = self._text_extraction_libs["docx"]
            logger.debug("DOCX processor initialized with python-docx")
        else:
            logger.warning("No DOCX processing library available")

    def _initialize_excel_processor(self):
        """Initialize Excel processing capabilities"""
        if "openpyxl" in self._text_extraction_libs:
            self._excel_processor = self._text_extraction_libs["openpyxl"]
            logger.debug("Excel processor initialized with openpyxl")
        else:
            logger.warning("No Excel processing library available")

    def _initialize_presentation_processor(self):
        """Initialize presentation processing capabilities"""
        if "pptx" in self._text_extraction_libs:
            self._presentation_processor = self._text_extraction_libs["pptx"]
            logger.debug("Presentation processor initialized with python-pptx")
        else:
            logger.warning("No presentation processing library available")

    def _process_file(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """
        Process office document with format-specific handling
        """
        try:
            file_extension = metadata.file_extension.lower()

            # Route to appropriate processor based on file type
            if file_extension == "pdf":
                return self._process_pdf(filepath, metadata)
            elif file_extension in ["docx", "doc"]:
                return self._process_word_document(filepath, metadata)
            elif file_extension in ["xlsx", "xls"]:
                return self._process_excel_document(filepath, metadata)
            elif file_extension in ["pptx", "ppt"]:
                return self._process_presentation(filepath, metadata)
            elif file_extension in ["odt", "ods", "odp"]:
                return self._process_opendocument(filepath, metadata)
            else:
                return self._fallback_processing(filepath, metadata)

        except Exception as e:
            logger.error(f"Office document processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"Processing error: {str(e)}",
                metadata=metadata,
            )

    def _process_pdf(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """Process PDF documents with advanced text extraction"""
        try:
            content_parts = []
            page_count = 0
            word_count = 0

            if self._pdf_processor and hasattr(self._pdf_processor, "open"):
                # Using pdfplumber
                with self._pdf_processor.open(filepath) as pdf:
                    page_count = len(pdf.pages)

                    for page_num, page in enumerate(pdf.pages, 1):
                        try:
                            text = page.extract_text()
                            if text:
                                content_parts.append(f"--- Page {page_num} ---\n{text}")
                                word_count += len(text.split())

                                # Extract tables if available
                                tables = page.extract_tables()
                                for table_num, table in enumerate(tables):
                                    table_text = self._format_table(table)
                                    content_parts.append(
                                        f"--- Table {table_num + 1} ---\n{table_text}"
                                    )

                        except Exception as page_error:
                            logger.warning(
                                f"Error processing PDF page {page_num}: {page_error}"
                            )
                            continue

            elif "PyPDF2" in self._text_extraction_libs:
                # Fallback to PyPDF2
                with open(filepath, "rb") as file:
                    pdf_reader = self._text_extraction_libs["PyPDF2"].PdfReader(file)
                    page_count = len(pdf_reader.pages)

                    for page_num in range(page_count):
                        try:
                            page = pdf_reader.pages[page_num]
                            text = page.extract_text()
                            if text:
                                content_parts.append(
                                    f"--- Page {page_num + 1} ---\n{text}"
                                )
                                word_count += len(text.split())
                        except Exception as page_error:
                            logger.warning(
                                f"Error processing PDF page {page_num}: {page_error}"
                            )
                            continue

            content = "\n\n".join(content_parts)

            # Update metadata with page count
            metadata.page_count = page_count

            return ProcessingResult(
                success=bool(content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=page_count,
            )

        except Exception as e:
            logger.error(f"PDF processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"PDF processing error: {str(e)}",
                metadata=metadata,
            )

    def _process_word_document(
        self, filepath: str, metadata: FileMetadata
    ) -> ProcessingResult:
        """Process Word documents (DOCX and DOC)"""
        try:
            content_parts = []
            word_count = 0

            if self._docx_processor:
                # Process DOCX files
                doc = self._docx_processor.Document(filepath)

                # Extract paragraphs
                for para in doc.paragraphs:
                    if para.text.strip():
                        content_parts.append(para.text)
                        word_count += len(para.text.split())

                # Extract tables
                for table in doc.tables:
                    table_content = self._extract_docx_table(table)
                    if table_content:
                        content_parts.append(f"--- Table ---\n{table_content}")

            content = "\n".join(content_parts)

            return ProcessingResult(
                success=bool(content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=len(content_parts),
            )

        except Exception as e:
            logger.error(f"Word document processing failed for {filepath}: {str(e)}")
            return self._fallback_processing(filepath, metadata)

    def _process_excel_document(
        self, filepath: str, metadata: FileMetadata
    ) -> ProcessingResult:
        """Process Excel documents with sheet-wise extraction"""
        try:
            content_parts = []
            word_count = 0

            if self._excel_processor:
                workbook = self._excel_processor.load_workbook(filepath, data_only=True)

                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    sheet_content = []

                    # Extract cell values
                    for row in sheet.iter_rows(values_only=True):
                        row_data = [
                            str(cell) if cell is not None else "" for cell in row
                        ]
                        row_text = " | ".join(row_data)
                        if row_text.strip():
                            sheet_content.append(row_text)
                            word_count += len(row_text.split())

                    if sheet_content:
                        content_parts.append(f"--- Sheet: {sheet_name} ---")
                        content_parts.extend(sheet_content)

            content = "\n".join(content_parts)

            return ProcessingResult(
                success=bool(content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=len(content_parts),
            )

        except Exception as e:
            logger.error(f"Excel document processing failed for {filepath}: {str(e)}")
            return self._fallback_processing(filepath, metadata)

    def _process_presentation(
        self, filepath: str, metadata: FileMetadata
    ) -> ProcessingResult:
        """Process PowerPoint presentations"""
        try:
            content_parts = []
            word_count = 0

            if self._presentation_processor:
                presentation = self._presentation_processor.Presentation(filepath)

                for slide_num, slide in enumerate(presentation.slides, 1):
                    slide_content = []

                    # Extract text from shapes
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            slide_content.append(shape.text)
                            word_count += len(shape.text.split())

                    if slide_content:
                        content_parts.append(f"--- Slide {slide_num} ---")
                        content_parts.extend(slide_content)

            content = "\n".join(content_parts)

            # Update metadata with slide count
            metadata.page_count = (
                len(presentation.slides) if "presentation" in locals() else 0
            )

            return ProcessingResult(
                success=bool(content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=len(content_parts),
            )

        except Exception as e:
            logger.error(f"Presentation processing failed for {filepath}: {str(e)}")
            return self._fallback_processing(filepath, metadata)

    def _process_opendocument(
        self, filepath: str, metadata: FileMetadata
    ) -> ProcessingResult:
        """Process OpenDocument formats"""
        try:
            # Basic text extraction from OpenDocument files
            content = ""

            if "odf" in self._text_extraction_libs:
                # Implementation for ODF processing would go here
                logger.info(f"OpenDocument processing for {filepath} - using fallback")

            # Fallback to ZIP-based extraction for ODF files
            if file_extension in ["odt", "ods", "odp"]:
                content = self._extract_odf_content(filepath)

            word_count = len(content.split()) if content else 0

            return ProcessingResult(
                success=bool(content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=1,
            )

        except Exception as e:
            logger.error(f"OpenDocument processing failed for {filepath}: {str(e)}")
            return self._fallback_processing(filepath, metadata)

    def _extract_odf_content(self, filepath: str) -> str:
        """Extract content from ODF files using ZIP archive approach"""
        try:
            content_parts = []

            with zipfile.ZipFile(filepath, "r") as odf_file:
                # Look for content.xml in the archive
                if "content.xml" in odf_file.namelist():
                    with odf_file.open("content.xml") as content_file:
                        # Basic XML text extraction
                        tree = ET.parse(content_file)
                        root = tree.getroot()

                        # Extract text from XML elements
                        for elem in root.iter():
                            if elem.text and elem.text.strip():
                                content_parts.append(elem.text.strip())

            return "\n".join(content_parts)

        except Exception as e:
            logger.warning(f"ODF content extraction failed: {str(e)}")
            return ""

    def _extract_docx_table(self, table) -> str:
        """Extract content from DOCX tables"""
        table_content = []

        for row in table.rows:
            row_content = []
            for cell in row.cells:
                if cell.text and cell.text.strip():
                    row_content.append(cell.text.strip())
            if row_content:
                table_content.append(" | ".join(row_content))

        return "\n".join(table_content)

    def _format_table(self, table_data: List[List[str]]) -> str:
        """Format table data for text output"""
        formatted_lines = []

        for row in table_data:
            formatted_row = [str(cell).strip() if cell else "" for cell in row]
            formatted_lines.append(" | ".join(formatted_row))

        return "\n".join(formatted_lines)

    def _fallback_processing(
        self, filepath: str, metadata: FileMetadata
    ) -> ProcessingResult:
        """Fallback processing when specific processors fail"""
        try:
            # Try to extract any readable text using basic methods
            content = ""

            # For ZIP-based formats (DOCX, XLSX, PPTX, ODF)
            if metadata.file_extension in ["docx", "xlsx", "pptx", "odt", "ods", "odp"]:
                content = self._extract_from_zip(filepath)

            # For binary formats, we might need more advanced fallbacks
            word_count = len(content.split()) if content else 0

            return ProcessingResult(
                success=bool(content.strip()),
                status=(
                    ProcessingStatus.COMPLETED if content else ProcessingStatus.FAILED
                ),
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=1,
                error_message=(
                    "Used fallback processing"
                    if content
                    else "All processing methods failed"
                ),
            )

        except Exception as e:
            logger.error(f"Fallback processing also failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"All processing methods failed: {str(e)}",
                metadata=metadata,
            )

    def _extract_from_zip(self, filepath: str) -> str:
        """Basic text extraction from ZIP-based office documents"""
        try:
            content_parts = []

            with zipfile.ZipFile(filepath, "r") as zip_ref:
                # Look for text-containing files
                text_files = [
                    name
                    for name in zip_ref.namelist()
                    if name.endswith(".xml") or name.endswith(".rels")
                ]

                for text_file in text_files:
                    try:
                        with zip_ref.open(text_file) as file:
                            content = file.read().decode("utf-8", errors="ignore")
                            # Extract text between tags
                            import re

                            text_matches = re.findall(r">([^<]+)<", content)
                            if text_matches:
                                content_parts.extend(
                                    [
                                        match.strip()
                                        for match in text_matches
                                        if match.strip()
                                    ]
                                )
                    except Exception as e:
                        continue

            return " ".join(content_parts)

        except Exception as e:
            logger.warning(f"ZIP-based extraction failed: {str(e)}")
            return ""

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get detailed information about supported formats"""
        return {
            "pdf": ["PDF Documents"],
            "microsoft_office": ["DOC", "DOCX", "XLS", "XLSX", "PPT", "PPTX"],
            "opendocument": ["ODT", "ODS", "ODP"],
            "libraries_available": list(self._text_extraction_libs.keys()),
        }


# Factory function for easy access
def create_office_handler() -> OfficeDocumentHandler:
    """Create and initialize an office document handler instance"""
    handler = OfficeDocumentHandler()
    if handler.initialize():
        return handler
    else:
        raise RuntimeError("Failed to initialize OfficeDocumentHandler")


logger.info("OfficeDocumentHandler module loaded successfully")
