#!/usr/bin/env python3
"""
图像OCR处理器 - 多语言光学字符识别
功能：支持中英文、数字、符号识别，图像预处理增强
版本: 2.1.0
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

try:
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter

    HAS_IMAGE_DEPS = True
except ImportError as e:
    logging.warning(f"图像处理依赖缺失: {e}")
    HAS_IMAGE_DEPS = False


class IntelligentOCRProcessor:
    """智能OCR处理器"""

    def __init__(self, tesseract_path: str = None):
        """
        初始化OCR处理器

        Args:
            tesseract_path: Tesseract可执行文件路径
        """
        self.logger = logging.getLogger(__name__)

        if not HAS_IMAGE_DEPS:
            self.logger.error("图像处理依赖未安装，OCR功能不可用")
            return

        # 配置Tesseract路径
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # 尝试自动查找tesseract路径（Windows常见路径）
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

        self.supported_languages = {
            "chi_sim": "简体中文",
            "chi_tra": "繁体中文",
            "eng": "英语",
            "jpn": "日语",
            "kor": "韩语",
            "fra": "法语",
            "deu": "德语",
            "spa": "西班牙语",
        }

        self.ocr_configs = {
            "default": "--oem 3 --psm 6",
            "single_line": "--oem 3 --psm 7",
            "single_word": "--oem 3 --psm 8",
            "single_char": "--oem 3 --psm 10",
            "document": "--oem 3 --psm 6",
            "sparse_text": "--oem 3 --psm 11",
        }

    def process_image(
        self, image_path: str, languages: List[str] = None, preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        处理单张图片OCR

        Args:
            image_path: 图片路径
            languages: 语言列表，默认['chi_sim', 'eng']
            preprocess: 是否进行图像预处理

        Returns:
            OCR结果字典
        """
        if not HAS_IMAGE_DEPS:
            return self._create_error_result("图像处理依赖未安装")

        try:
            if not os.path.exists(image_path):
                return self._create_error_result(f"图片文件不存在: {image_path}")

            # 验证图片格式
            valid_extensions = [
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".tiff",
                ".tif",
                ".gif",
                ".webp",  # 添加webp格式支持
            ]
            file_ext = Path(image_path).suffix.lower()
            if file_ext not in valid_extensions:
                return self._create_error_result(f"不支持的图片格式: {image_path}")

            # 设置语言
            if languages is None:
                languages = ["chi_sim", "eng"]

            # 验证语言是否支持
            invalid_langs = [
                lang for lang in languages if lang not in self.supported_languages
            ]
            if invalid_langs:
                self.logger.warning(f"不支持的语言: {invalid_langs}，将使用默认语言")
                languages = [
                    lang for lang in languages if lang in self.supported_languages
                ]
                if not languages:  # 如果所有语言都不支持，使用默认
                    languages = ["chi_sim", "eng"]

            lang_str = "+".join(languages)

            # 读取图片
            image = self._load_image(image_path)
            if image is None:
                return self._create_error_result("图片加载失败")

            original_size = image.size
            image_hash = self._calculate_image_hash(image)

            # 图像预处理
            processed_image = image
            if preprocess:
                processed_image = self._preprocess_image(image)

            # OCR识别
            ocr_result = self._perform_ocr(processed_image, lang_str)

            # 后处理
            processed_text = self._postprocess_text(ocr_result["text"])

            result = {
                "file_path": image_path,
                "file_name": Path(image_path).name,
                "file_size": os.path.getsize(image_path),
                "image_hash": image_hash,
                "original_size": original_size,
                "processed_size": processed_image.size,
                "languages": languages,
                "preprocess_applied": preprocess,
                "timestamp": datetime.now().isoformat(),
                "text_content": processed_text,
                "confidence": ocr_result["confidence"],
                "word_details": ocr_result.get("word_details", []),
                "processing_time": ocr_result["processing_time"],
                "error": None,  # 明确标记无错误
            }

            return result

        except Exception as e:
            self.logger.error(f"OCR处理失败 {image_path}: {str(e)}")
            return self._create_error_result(str(e))

    def _load_image(self, image_path: str) -> Optional["Image.Image"]:
        """加载图片"""
        try:
            # 使用PIL打开图片并确保RGB模式
            image = Image.open(image_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return image
        except Exception as e:
            self.logger.error(f"图片加载失败 {image_path}: {e}")
            return None

    def _calculate_image_hash(self, image: Image.Image) -> str:
        """计算图片哈希值"""
        try:
            # 转换为RGB并调整大小以计算一致性哈希
            image_rgb = image.convert("RGB")
            image_small = image_rgb.resize((8, 8), Image.Resampling.LANCZOS)

            # 计算平均哈希
            pixels = list(image_small.getdata())
            # 转换为灰度值
            if isinstance(pixels[0], tuple):  # 如果是RGB元组
                pixels = [sum(pixel) // 3 for pixel in pixels]  # 转换为灰度值
            avg = sum(pixels) / len(pixels)
            bits = "".join("1" if pixel >= avg else "0" for pixel in pixels)

            return hex(int(bits, 2))
        except Exception as e:
            self.logger.warning(f"图片哈希计算失败: {e}")
            return "unknown"

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        图像预处理增强

        Args:
            image: 输入图像

        Returns:
            预处理后的图像
        """
        try:
            # 转换为RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 转换为OpenCV格式进行高级处理
            cv_image = np.array(image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)

            # 1. 灰度化
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # 2. 噪声去除
            denoised = cv2.medianBlur(gray, 3)

            # 3. 对比度增强 - CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # 4. 二值化 - 自适应阈值
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # 转换回PIL Image
            result_image = Image.fromarray(binary)

            return result_image

        except Exception as e:
            self.logger.warning(f"高级预处理失败，使用基础预处理: {e}")
            # 基础预处理
            return self._basic_preprocess(image)

    def _basic_preprocess(self, image: Image.Image) -> Image.Image:
        """基础图像预处理"""
        try:
            # 转换为RGB确保一致性
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 对比度增强
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # 降低增强系数避免过度处理

            # 锐化
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)

            return image
        except Exception as e:
            self.logger.warning(f"基础预处理失败，返回原图: {e}")
            return image

    def _perform_ocr(self, image: Image.Image, languages: str) -> Dict[str, Any]:
        """
        执行OCR识别

        Args:
            image: 输入图像
            languages: 语言字符串

        Returns:
            OCR结果
        """
        import time

        start_time = time.time()

        try:
            # 获取详细数据
            data = pytesseract.image_to_data(
                image,
                lang=languages,
                output_type=pytesseract.Output.DICT,
                config=self.ocr_configs["document"],
            )

            # 提取文本和置信度
            text = pytesseract.image_to_string(
                image, lang=languages, config=self.ocr_configs["document"]
            ).strip()

            # 计算平均置信度
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # 提取单词详情
            word_details = []
            n_boxes = len(data["level"])
            for i in range(n_boxes):
                if (
                    int(data["conf"][i]) > 0 and data["text"][i].strip()
                ):  # 只包含置信度大于0且非空的识别结果
                    word_details.append(
                        {
                            "text": data["text"][i],
                            "confidence": int(data["conf"][i]),
                            "position": {
                                "left": data["left"][i],
                                "top": data["top"][i],
                                "width": data["width"][i],
                                "height": data["height"][i],
                            },
                        }
                    )

            processing_time = time.time() - start_time

            return {
                "text": text,
                "confidence": round(avg_confidence, 2),  # 保留两位小数
                "word_details": word_details,
                "processing_time": round(processing_time, 3),  # 保留三位小数
            }

        except pytesseract.TesseractNotFoundError as e:
            self.logger.error(f"Tesseract未找到: {e}")
            return {
                "text": "",
                "confidence": 0,
                "word_details": [],
                "processing_time": time.time() - start_time,
            }
        except Exception as e:
            self.logger.error(f"OCR识别失败: {e}")
            return {
                "text": "",
                "confidence": 0,
                "word_details": [],
                "processing_time": time.time() - start_time,
            }

    def _postprocess_text(self, text: str) -> str:
        """
        文本后处理

        Args:
            text: 原始识别文本

        Returns:
            处理后的文本
        """
        if not text:
            return ""

        try:
            # 移除多余的空格和换行
            lines = [line.strip() for line in text.split("\n")]
            lines = [line for line in lines if line]  # 移除空行

            # 合并段落
            processed_lines = []
            current_paragraph = []

            for line in lines:
                # 改进的段落判断逻辑
                if len(line) < 50 and not line.endswith(
                    ("。", "!", "?", ".", "！", "？")
                ):
                    # 短行且不以句子结束符结尾，可能是新段落
                    if current_paragraph:
                        processed_lines.append(" ".join(current_paragraph))
                        current_paragraph = []
                    processed_lines.append(line)
                else:
                    current_paragraph.append(line)

            if current_paragraph:
                processed_lines.append(" ".join(current_paragraph))

            return "\n".join(processed_lines)
        except Exception as e:
            self.logger.warning(f"文本后处理失败: {e}")
            return text

    def batch_process(self, image_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        批量处理图片

        Args:
            image_paths: 图片路径列表
            **kwargs: 其他参数

        Returns:
            批量处理结果
        """
        results = {}

        for image_path in image_paths:
            if os.path.exists(image_path):
                results[image_path] = self.process_image(image_path, **kwargs)
            else:
                results[image_path] = self._create_error_result(
                    f"文件不存在: {image_path}"
                )

        # 统计成功和失败数量
        successful = [
            r for r in results.values() if "error" not in r or not r.get("error")
        ]
        failed = [r for r in results.values() if "error" in r and r.get("error")]

        return {
            "total_images": len(image_paths),
            "successful_ocr": len(successful),
            "failed_ocr": len(failed),
            "results": results,
        }

    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "text_content": "",
            "confidence": 0,
            "word_details": [],
        }

    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.supported_languages.copy()

    def validate_tesseract(self) -> bool:
        """验证Tesseract是否可用"""
        try:
            version = pytesseract.get_tesseract_version()
            self.logger.info(f"Tesseract版本: {version}")
            return True
        except pytesseract.TesseractNotFoundError:
            self.logger.error("Tesseract未找到，请确保已安装并配置正确路径")
            return False
        except Exception as e:
            self.logger.error(f"Tesseract验证失败: {e}")
            return False


# 全局实例
_ocr_processor = None


def get_ocr_processor(tesseract_path: str = None) -> IntelligentOCRProcessor:
    """获取OCR处理器实例"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = IntelligentOCRProcessor(tesseract_path)
    return _ocr_processor


if __name__ == "__main__":
    # 测试代码
    processor = IntelligentOCRProcessor()

    # 验证Tesseract
    if processor.validate_tesseract():
        print("✓ Tesseract可用")
        print("支持的语言:", processor.get_supported_languages())

        # 简单的功能测试
        test_image = "test.png"  # 可以替换为实际测试图片
        if os.path.exists(test_image):
            result = processor.process_image(test_image)
            if "error" not in result:
                print(f"✓ 测试图片识别成功，置信度: {result['confidence']}%")
                print(f"识别文本: {result['text_content'][:100]}...")
            else:
                print(f"✗ 测试图片识别失败: {result['error']}")
        else:
            print("ℹ 未找到测试图片，跳过功能测试")
    else:
        print("✗ Tesseract不可用，请检查安装和配置")
