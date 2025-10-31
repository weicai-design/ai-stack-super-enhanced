"""
Ebook Extractor for AI Stack Super Enhanced
Advanced ebook format processing with semantic extraction

Version: 1.0.0
Author: AI Stack Super Enhanced Team
Created: 2024
"""

import html
import logging
import os
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import FileMetadata, FileProcessorBase, ProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class EbookExtractor(FileProcessorBase):
    """
    Advanced ebook processor supporting:
    - EPUB format with full structure parsing
    - MOBI format (basic extraction)
    - AZW3 format (basic extraction)
    - FB2 format (XML-based extraction)
    - Metadata and chapter extraction
    - Semantic content organization
    """

    def __init__(self):
        super().__init__()
        self.processor_name = "EbookExtractor"

        # Supported ebook formats
        self.supported_extensions = ["epub", "mobi", "azw3", "fb2"]

        # Supported MIME types
        self.supported_mime_types = [
            "application/epub+zip",
            "application/x-mobipocket-ebook",
            "application/vnd.amazon.ebook",
            "text/fb2+xml",
        ]

        # EPUB-specific constants
        self.epub_container_path = "META-INF/container.xml"
        self.epub_content_types = {
            "xhtml": "application/xhtml+xml",
            "html": "text/html",
            "css": "text/css",
            "ncx": "application/x-dtbncx+xml",
            "nav": "application/xhtml+xml",
        }

        # Processing state
        self._temp_dir = None
        self._ebook_structure = {}

    def initialize(self) -> bool:
        """Initialize ebook extractor"""
        try:
            # Create temporary directory for ebook processing
            self._temp_dir = tempfile.mkdtemp(prefix="ebook_extractor_")

            # Verify we can process basic ebook formats
            self._verify_processing_capabilities()

            self._initialized = True
            logger.info("EbookExtractor initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize EbookExtractor: {str(e)}")
            self._initialized = False
            return False

    def _verify_processing_capabilities(self):
        """Verify that we have basic processing capabilities"""
        # Check for required XML processing
        try:
            ET.fromstring("<test>content</test>")
            logger.debug("XML processing verified")
        except Exception as e:
            logger.warning(f"XML processing issue: {str(e)}")

    def _process_file(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """
        Process ebook file with format-specific extraction
        """
        try:
            file_extension = metadata.file_extension.lower()

            # Route to appropriate ebook processor
            if file_extension == "epub":
                return self._process_epub(filepath, metadata)
            elif file_extension == "fb2":
                return self._process_fb2(filepath, metadata)
            elif file_extension in ["mobi", "azw3"]:
                return self._process_mobi_azw3(filepath, metadata)
            else:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message=f"Unsupported ebook format: {file_extension}",
                    metadata=metadata,
                )

        except Exception as e:
            logger.error(f"Ebook processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"Ebook processing error: {str(e)}",
                metadata=metadata,
            )

    def _process_epub(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """
        Process EPUB format with full structure parsing
        """
        try:
            # Extract EPUB structure
            epub_structure = self._analyze_epub_structure(filepath)

            # Extract content from all text files
            content_parts = []
            total_word_count = 0
            chapter_count = 0

            # Process content documents in reading order
            reading_order = self._determine_reading_order(epub_structure)

            for content_file in reading_order:
                try:
                    file_content = self._extract_epub_file_content(
                        filepath, content_file
                    )
                    if file_content:
                        cleaned_content = self._clean_ebook_content(file_content)
                        if cleaned_content:
                            content_parts.append(cleaned_content)
                            total_word_count += len(cleaned_content.split())
                            chapter_count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to process EPUB file {content_file}: {str(e)}"
                    )
                    continue

            # Combine all content
            full_content = "\n\n".join(content_parts)

            # Extract metadata
            ebook_metadata = self._extract_epub_metadata(filepath, epub_structure)

            # Update file metadata with ebook-specific information
            metadata.page_count = chapter_count
            metadata.language = ebook_metadata.get("language", "unknown")

            return ProcessingResult(
                success=bool(full_content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=full_content,
                metadata=metadata,
                chunks=content_parts,
                word_count=total_word_count,
                chunk_count=chapter_count,
            )

        except Exception as e:
            logger.error(f"EPUB processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"EPUB processing error: {str(e)}",
                metadata=metadata,
            )

    def _analyze_epub_structure(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze EPUB structure and extract file manifest
        """
        structure = {
            "container": {},
            "package_document": {},
            "manifest": [],
            "spine": [],
            "toc": None,
        }

        try:
            with zipfile.ZipFile(filepath, "r") as epub_zip:
                # Parse container to find package document
                if self.epub_container_path in epub_zip.namelist():
                    container_content = epub_zip.read(self.epub_container_path).decode(
                        "utf-8"
                    )
                    rootfile = self._parse_container_xml(container_content)
                    structure["container"]["rootfile"] = rootfile

                # Parse package document (OPF)
                if "rootfile" in structure["container"]:
                    opf_path = structure["container"]["rootfile"]
                    if opf_path in epub_zip.namelist():
                        opf_content = epub_zip.read(opf_path).decode("utf-8")
                        package_info = self._parse_package_document(
                            opf_content, opf_path
                        )
                        structure["package_document"] = package_info
                        structure["manifest"] = package_info.get("manifest", [])
                        structure["spine"] = package_info.get("spine", [])

                # Look for table of contents
                structure["toc"] = self._find_epub_toc(epub_zip, structure)

        except Exception as e:
            logger.warning(f"EPUB structure analysis incomplete: {str(e)}")

        return structure

    def _parse_container_xml(self, container_content: str) -> str:
        """Parse EPUB container.xml to find rootfile"""
        try:
            root = ET.fromstring(container_content)
            ns = {"ns": "urn:oasis:names:tc:opendocument:xmlns:container"}
            rootfile = root.find(".//ns:rootfile", ns)
            return (
                rootfile.get("full-path")
                if rootfile is not None
                else "OEBPS/content.opf"
            )
        except Exception as e:
            logger.warning(f"Container XML parsing failed: {str(e)}")
            return "OEBPS/content.opf"

    def _parse_package_document(
        self, opf_content: str, opf_path: str
    ) -> Dict[str, Any]:
        """Parse EPUB package document (OPF)"""
        package_info = {"metadata": {}, "manifest": [], "spine": []}

        try:
            root = ET.fromstring(opf_content)

            # Extract metadata
            metadata_elem = root.find(".//{http://www.idpf.org/2007/opf}metadata")
            if metadata_elem is not None:
                for child in metadata_elem:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    package_info["metadata"][tag] = child.text

            # Extract manifest (all files in the EPUB)
            manifest_elem = root.find(".//{http://www.idpf.org/2007/opf}manifest")
            if manifest_elem is not None:
                for item in manifest_elem.findall("{http://www.idpf.org/2007/opf}item"):
                    item_info = {
                        "id": item.get("id"),
                        "href": item.get("href"),
                        "media_type": item.get("media-type"),
                    }
                    # Resolve relative paths
                    opf_dir = os.path.dirname(opf_path)
                    if opf_dir:
                        item_info["resolved_path"] = os.path.join(
                            opf_dir, item_info["href"]
                        )
                    else:
                        item_info["resolved_path"] = item_info["href"]

                    package_info["manifest"].append(item_info)

            # Extract spine (reading order)
            spine_elem = root.find(".//{http://www.idpf.org/2007/opf}spine")
            if spine_elem is not None:
                for itemref in spine_elem.findall(
                    "{http://www.idpf.org/2007/opf}itemref"
                ):
                    spine_item = {"idref": itemref.get("idref")}
                    package_info["spine"].append(spine_item)

        except Exception as e:
            logger.warning(f"Package document parsing failed: {str(e)}")

        return package_info

    def _find_epub_toc(
        self, epub_zip: zipfile.ZipFile, structure: Dict
    ) -> Optional[str]:
        """Find table of contents in EPUB"""
        try:
            # Look for NCX file
            for manifest_item in structure["manifest"]:
                if manifest_item["media_type"] == "application/x-dtbncx+xml":
                    return manifest_item["resolved_path"]

            # Look for NAV file (EPUB 3)
            for manifest_item in structure["manifest"]:
                if manifest_item[
                    "media_type"
                ] == "application/xhtml+xml" and "nav" in manifest_item.get(
                    "properties", ""
                ):
                    return manifest_item["resolved_path"]

        except Exception as e:
            logger.warning(f"TOC finding failed: {str(e)}")

        return None

    def _determine_reading_order(self, structure: Dict) -> List[str]:
        """Determine reading order from spine and manifest"""
        reading_order = []

        try:
            # Use spine order if available
            if structure["spine"]:
                manifest_by_id = {item["id"]: item for item in structure["manifest"]}

                for spine_item in structure["spine"]:
                    item_id = spine_item.get("idref")
                    if item_id in manifest_by_id:
                        manifest_item = manifest_by_id[item_id]
                        if manifest_item["media_type"] in [
                            "application/xhtml+xml",
                            "text/html",
                        ]:
                            reading_order.append(manifest_item["resolved_path"])

            # Fallback: all XHTML/HTML files
            if not reading_order:
                for manifest_item in structure["manifest"]:
                    if manifest_item["media_type"] in [
                        "application/xhtml+xml",
                        "text/html",
                    ]:
                        reading_order.append(manifest_item["resolved_path"])

        except Exception as e:
            logger.warning(f"Reading order determination failed: {str(e)}")

        return reading_order

    def _extract_epub_file_content(self, filepath: str, content_file: str) -> str:
        """Extract content from a specific file in EPUB"""
        try:
            with zipfile.ZipFile(filepath, "r") as epub_zip:
                if content_file in epub_zip.namelist():
                    content = epub_zip.read(content_file).decode(
                        "utf-8", errors="ignore"
                    )
                    return self._extract_text_from_xhtml(content)
        except Exception as e:
            logger.warning(
                f"EPUB file content extraction failed for {content_file}: {str(e)}"
            )

        return ""

    def _extract_text_from_xhtml(self, xhtml_content: str) -> str:
        """Extract readable text from XHTML/HTML content"""
        try:
            # Remove script and style elements
            cleaned_content = re.sub(
                r"<script.*?</script>", "", xhtml_content, flags=re.DOTALL
            )
            cleaned_content = re.sub(
                r"<style.*?</style>", "", cleaned_content, flags=re.DOTALL
            )

            # Extract text from HTML tags
            text_content = re.sub(r"<[^>]+>", " ", cleaned_content)

            # Decode HTML entities
            text_content = html.unescape(text_content)

            # Clean up whitespace
            text_content = re.sub(r"\s+", " ", text_content).strip()

            return text_content

        except Exception as e:
            logger.warning(f"XHTML text extraction failed: {str(e)}")
            return xhtml_content  # Return raw content as fallback

    def _extract_epub_metadata(self, filepath: str, structure: Dict) -> Dict[str, str]:
        """Extract metadata from EPUB"""
        metadata = {}

        try:
            # Use metadata from package document
            if "metadata" in structure["package_document"]:
                metadata.update(structure["package_document"]["metadata"])

            # Additional metadata extraction could go here

        except Exception as e:
            logger.warning(f"EPUB metadata extraction failed: {str(e)}")

        return metadata

    def _process_fb2(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """
        Process FictionBook (FB2) format
        """
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fb2_file:
                fb2_content = fb2_file.read()

            # Parse FB2 XML
            content_parts = []
            total_word_count = 0

            try:
                root = ET.fromstring(fb2_content)

                # Extract body content
                body_elem = root.find(
                    ".//{http://www.gribuser.ru/xml/fictionbook/2.0}body"
                )
                if body_elem is not None:
                    sections = body_elem.findall(
                        ".//{http://www.gribuser.ru/xml/fictionbook/2.0}section"
                    )

                    for section in sections:
                        section_text = self._extract_fb2_section_text(section)
                        if section_text:
                            content_parts.append(section_text)
                            total_word_count += len(section_text.split())

            except ET.ParseError:
                # Fallback: basic text extraction
                text_content = self._extract_text_from_xml_like(fb2_content)
                if text_content:
                    content_parts.append(text_content)
                    total_word_count = len(text_content.split())

            full_content = "\n\n".join(content_parts)

            return ProcessingResult(
                success=bool(full_content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=full_content,
                metadata=metadata,
                word_count=total_word_count,
                chunk_count=len(content_parts),
            )

        except Exception as e:
            logger.error(f"FB2 processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"FB2 processing error: {str(e)}",
                metadata=metadata,
            )

    def _extract_fb2_section_text(self, section_elem) -> str:
        """Extract text from FB2 section"""
        text_parts = []

        try:
            # Recursively extract text from all paragraph elements
            paragraphs = section_elem.findall(
                ".//{http://www.gribuser.ru/xml/fictionbook/2.0}p"
            )
            for para in paragraphs:
                if para.text:
                    text_parts.append(para.text.strip())

            # Also get direct text content
            if section_elem.text and section_elem.text.strip():
                text_parts.append(section_elem.text.strip())

        except Exception as e:
            logger.warning(f"FB2 section text extraction failed: {str(e)}")

        return "\n".join(text_parts)

    def _extract_text_from_xml_like(self, xml_content: str) -> str:
        """Basic text extraction from XML-like content"""
        try:
            # Remove XML tags and extract text
            text_content = re.sub(r"<[^>]+>", " ", xml_content)
            text_content = html.unescape(text_content)
            text_content = re.sub(r"\s+", " ", text_content).strip()
            return text_content
        except Exception as e:
            logger.warning(f"XML-like text extraction failed: {str(e)}")
            return xml_content

    def _process_mobi_azw3(
        self, filepath: str, metadata: FileMetadata
    ) -> ProcessingResult:
        """
        Process MOBI and AZW3 formats with basic extraction
        """
        try:
            # For MOBI/AZW3, we use a basic approach since full parsing requires specialized libraries
            content = self._extract_text_from_binary_ebook(filepath)
            word_count = len(content.split()) if content else 0

            return ProcessingResult(
                success=bool(content.strip()),
                status=ProcessingStatus.COMPLETED,
                content=content,
                metadata=metadata,
                word_count=word_count,
                chunk_count=1,
                error_message="Used basic extraction for MOBI/AZW3 format",
            )

        except Exception as e:
            logger.error(f"MOBI/AZW3 processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"MOBI/AZW3 processing error: {str(e)}",
                metadata=metadata,
            )

    def _extract_text_from_binary_ebook(self, filepath: str) -> str:
        """Basic text extraction from binary ebook formats"""
        try:
            content_parts = []

            # Try to read as binary and extract readable text
            with open(filepath, "rb") as ebook_file:
                binary_content = ebook_file.read()

                # Decode with error handling
                try:
                    text_content = binary_content.decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    text_content = binary_content.decode("latin-1", errors="ignore")

                # Extract sequences that look like text
                text_matches = re.findall(r"[a-zA-Z]{4,}", text_content)
                if text_matches:
                    content_parts.extend(text_matches)

            return " ".join(content_parts)

        except Exception as e:
            logger.warning(f"Binary ebook text extraction failed: {str(e)}")
            return ""

    def _clean_ebook_content(self, content: str) -> str:
        """Clean and normalize ebook content"""
        try:
            # Remove excessive whitespace
            cleaned = re.sub(r"\s+", " ", content)

            # Remove common ebook artifacts
            cleaned = re.sub(r"\bPage\s*\d+\b", "", cleaned)  # Page numbers
            cleaned = re.sub(r"\n\s*\n", "\n\n", cleaned)  # Multiple newlines

            return cleaned.strip()

        except Exception as e:
            logger.warning(f"Ebook content cleaning failed: {str(e)}")
            return content

    def get_ebook_info(self, filepath: str) -> Dict[str, Any]:
        """Get detailed information about ebook structure"""
        try:
            if not self._initialized:
                return {"error": "EbookExtractor not initialized"}

            file_extension = Path(filepath).suffix.lower().lstrip(".")

            if file_extension == "epub":
                structure = self._analyze_epub_structure(filepath)
                return {
                    "format": "EPUB",
                    "structure_analyzed": True,
                    "chapter_count": len(structure.get("spine", [])),
                    "files_count": len(structure.get("manifest", [])),
                    "has_toc": structure.get("toc") is not None,
                    "metadata": structure.get("package_document", {}).get(
                        "metadata", {}
                    ),
                }
            else:
                return {
                    "format": file_extension.upper(),
                    "structure_analyzed": False,
                    "note": "Detailed structure analysis available only for EPUB",
                }

        except Exception as e:
            logger.error(f"Ebook info extraction failed: {str(e)}")
            return {"error": str(e)}


# Factory function for easy access
def create_ebook_extractor() -> EbookExtractor:
    """Create and initialize an ebook extractor instance"""
    extractor = EbookExtractor()
    if extractor.initialize():
        return extractor
    else:
        raise RuntimeError("Failed to initialize EbookExtractor")


logger.info("EbookExtractor module loaded successfully")
