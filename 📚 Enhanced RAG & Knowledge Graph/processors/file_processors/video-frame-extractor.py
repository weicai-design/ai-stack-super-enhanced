#!/usr/bin/env python3
"""
视频帧提取器 - 智能视频分析与关键帧提取
功能：支持MP4、AVI、MOV等格式，关键帧检测，场景分割
版本: 2.1.0
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    import cv2
    import numpy as np
    from PIL import Image

    HAS_VIDEO_DEPS = True
except ImportError as e:
    logging.warning(f"视频处理依赖缺失: {e}")
    HAS_VIDEO_DEPS = False


class IntelligentVideoFrameExtractor:
    """智能视频帧提取器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        if not HAS_VIDEO_DEPS:
            self.logger.error("视频处理依赖未安装，帧提取功能不可用")
            return

        self.supported_formats = {
            ".mp4": "MP4",
            ".avi": "AVI",
            ".mov": "MOV",
            ".mkv": "MKV",
            ".wmv": "WMV",
            ".flv": "FLV",
            ".webm": "WEBM",
            ".m4v": "M4V",
        }

        self.extraction_modes = {
            "uniform": self._extract_uniform_frames,
            "keyframe": self._extract_keyframes,
            "scene_change": self._extract_scene_change_frames,
            "motion": self._extract_motion_frames,
        }

    def extract_frames(
        self,
        video_path: str,
        output_dir: str = None,
        mode: str = "keyframe",
        interval: int = 5,
        max_frames: int = 100,
        quality: int = 85,
    ) -> Dict[str, Any]:
        """
        提取视频帧

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录，默认为视频同目录
            mode: 提取模式 [uniform, keyframe, scene_change, motion]
            interval: 均匀提取时间间隔(秒)
            max_frames: 最大帧数
            quality: 输出图片质量(1-100)

        Returns:
            提取结果字典
        """
        if not HAS_VIDEO_DEPS:
            return self._create_error_result("视频处理依赖未安装")

        try:
            if not os.path.exists(video_path):
                return self._create_error_result(f"视频文件不存在: {video_path}")

            # 验证视频格式
            file_ext = Path(video_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return self._create_error_result(f"不支持的视频格式: {file_ext}")

            # 设置输出目录
            if output_dir is None:
                output_dir = Path(video_path).parent / f"{Path(video_path).stem}_frames"

            os.makedirs(output_dir, exist_ok=True)

            # 获取视频信息
            video_info = self._get_video_info(video_path)
            if "error" in video_info:
                return video_info

            # 选择提取模式
            if mode in self.extraction_modes:
                extraction_func = self.extraction_modes[mode]
            else:
                extraction_func = self._extract_keyframes

            # 执行帧提取
            extraction_result = extraction_func(
                video_path, output_dir, video_info, interval, max_frames, quality
            )

            # 构建完整结果
            result = {
                "video_path": video_path,
                "video_name": Path(video_path).name,
                "file_size": os.path.getsize(video_path),
                "video_info": video_info,
                "extraction_mode": mode,
                "output_dir": str(output_dir),
                "timestamp": datetime.now().isoformat(),
                "extracted_frames": extraction_result["frame_count"],
                "frames_info": extraction_result["frames_info"],
                "processing_time": extraction_result["processing_time"],
                "keyframe_ratio": extraction_result.get("keyframe_ratio", 0),
                "scene_changes": extraction_result.get("scene_changes", 0),
            }

            return result

        except Exception as e:
            self.logger.error(f"视频帧提取失败 {video_path}: {str(e)}")
            return self._create_error_result(str(e))

    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频文件信息"""
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return {"error": "无法打开视频文件"}

            # 基础信息
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0

            # 视频尺寸
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 编码信息
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

            cap.release()

            return {
                "frame_count": frame_count,
                "fps": fps,
                "duration": duration,
                "width": width,
                "height": height,
                "codec": codec,
                "aspect_ratio": width / height if height > 0 else 0,
            }

        except Exception as e:
            return {"error": f"视频信息获取失败: {str(e)}"}

    def _extract_uniform_frames(
        self,
        video_path: str,
        output_dir: str,
        video_info: Dict,
        interval: int,
        max_frames: int,
        quality: int,
    ) -> Dict[str, Any]:
        """均匀提取帧（按时间间隔）"""
        import time

        start_time = time.time()

        cap = cv2.VideoCapture(video_path)
        frames_info = []
        frame_count = 0

        # 计算提取间隔（帧数）
        interval_frames = int(video_info["fps"] * interval)

        frame_index = 0
        while frame_index < video_info["frame_count"] and frame_count < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()

            if not ret:
                break

            # 保存帧
            frame_filename = f"frame_{frame_index:06d}.jpg"
            frame_path = os.path.join(output_dir, frame_filename)

            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

            # 记录帧信息
            frames_info.append(
                {
                    "frame_number": frame_index,
                    "timestamp": frame_index / video_info["fps"],
                    "file_path": frame_path,
                    "file_size": os.path.getsize(frame_path),
                }
            )

            frame_count += 1
            frame_index += interval_frames

        cap.release()

        return {
            "frame_count": frame_count,
            "frames_info": frames_info,
            "processing_time": time.time() - start_time,
        }

    def _extract_keyframes(
        self,
        video_path: str,
        output_dir: str,
        video_info: Dict,
        interval: int,
        max_frames: int,
        quality: int,
    ) -> Dict[str, Any]:
        """提取关键帧（I帧）"""
        import time

        start_time = time.time()

        # 使用OpenCV的简单关键帧检测
        cap = cv2.VideoCapture(video_path)
        frames_info = []
        frame_count = 0

        prev_frame = None
        frame_index = 0
        keyframe_count = 0

        while frame_index < video_info["frame_count"] and frame_count < max_frames:
            ret, frame = cap.read()

            if not ret:
                break

            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 第一帧或与前一帧差异较大时保存为关键帧
            if prev_frame is None:
                is_keyframe = True
            else:
                # 计算帧间差异
                diff = cv2.absdiff(prev_frame, gray)
                non_zero_count = np.count_nonzero(diff)
                diff_ratio = non_zero_count / (gray.shape[0] * gray.shape[1])

                # 差异超过阈值视为关键帧
                is_keyframe = diff_ratio > 0.1

            if is_keyframe:
                # 保存关键帧
                frame_filename = f"keyframe_{frame_index:06d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)

                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

                frames_info.append(
                    {
                        "frame_number": frame_index,
                        "timestamp": frame_index / video_info["fps"],
                        "file_path": frame_path,
                        "file_size": os.path.getsize(frame_path),
                        "keyframe_score": diff_ratio if prev_frame is not None else 1.0,
                    }
                )

                frame_count += 1
                keyframe_count += 1

            prev_frame = gray
            frame_index += 1

        cap.release()

        keyframe_ratio = (
            keyframe_count / video_info["frame_count"]
            if video_info["frame_count"] > 0
            else 0
        )

        return {
            "frame_count": frame_count,
            "frames_info": frames_info,
            "processing_time": time.time() - start_time,
            "keyframe_ratio": keyframe_ratio,
        }

    def _extract_scene_change_frames(
        self,
        video_path: str,
        output_dir: str,
        video_info: Dict,
        interval: int,
        max_frames: int,
        quality: int,
    ) -> Dict[str, Any]:
        """基于场景变化的帧提取"""
        import time

        start_time = time.time()

        cap = cv2.VideoCapture(video_path)
        frames_info = []
        frame_count = 0

        # 场景变化检测参数
        scene_threshold = 0.3
        prev_hist = None
        scene_changes = 0

        frame_index = 0
        while frame_index < video_info["frame_count"] and frame_count < max_frames:
            ret, frame = cap.read()

            if not ret:
                break

            # 计算直方图
            hist = cv2.calcHist(
                [frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
            )
            hist = cv2.normalize(hist, hist).flatten()

            # 比较直方图差异
            if prev_hist is not None:
                correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)

                # 相关性低表示场景变化
                if correlation < scene_threshold:
                    scene_changes += 1

                    # 保存场景变化帧
                    frame_filename = (
                        f"scene_{scene_changes:03d}_frame_{frame_index:06d}.jpg"
                    )
                    frame_path = os.path.join(output_dir, frame_filename)

                    cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

                    frames_info.append(
                        {
                            "frame_number": frame_index,
                            "timestamp": frame_index / video_info["fps"],
                            "file_path": frame_path,
                            "file_size": os.path.getsize(frame_path),
                            "scene_change_score": 1 - correlation,
                        }
                    )

                    frame_count += 1

            prev_hist = hist
            frame_index += 1

        cap.release()

        return {
            "frame_count": frame_count,
            "frames_info": frames_info,
            "processing_time": time.time() - start_time,
            "scene_changes": scene_changes,
        }

    def _extract_motion_frames(
        self,
        video_path: str,
        output_dir: str,
        video_info: Dict,
        interval: int,
        max_frames: int,
        quality: int,
    ) -> Dict[str, Any]:
        """基于运动检测的帧提取"""
        import time

        start_time = time.time()

        cap = cv2.VideoCapture(video_path)
        frames_info = []
        frame_count = 0

        # 运动检测参数
        motion_threshold = 1000
        prev_gray = None
        fgbg = cv2.createBackgroundSubtractorMOG2()

        frame_index = 0
        motion_frames = 0

        while frame_index < video_info["frame_count"] and frame_count < max_frames:
            ret, frame = cap.read()

            if not ret:
                break

            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 应用背景减除
            fgmask = fgbg.apply(frame)

            # 计算运动区域
            motion_pixels = np.count_nonzero(fgmask)

            # 检测到显著运动
            if motion_pixels > motion_threshold:
                motion_frames += 1

                # 保存运动帧
                frame_filename = (
                    f"motion_{motion_frames:03d}_frame_{frame_index:06d}.jpg"
                )
                frame_path = os.path.join(output_dir, frame_filename)

                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

                frames_info.append(
                    {
                        "frame_number": frame_index,
                        "timestamp": frame_index / video_info["fps"],
                        "file_path": frame_path,
                        "file_size": os.path.getsize(frame_path),
                        "motion_score": motion_pixels / (gray.shape[0] * gray.shape[1]),
                    }
                )

                frame_count += 1

            prev_gray = gray
            frame_index += 1

        cap.release()

        return {
            "frame_count": frame_count,
            "frames_info": frames_info,
            "processing_time": time.time() - start_time,
            "motion_frames": motion_frames,
        }

    def batch_extract(
        self, video_paths: List[str], output_base_dir: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        批量提取视频帧

        Args:
            video_paths: 视频文件路径列表
            output_base_dir: 输出基础目录
            **kwargs: 其他参数

        Returns:
            批量处理结果
        """
        results = {}

        for video_path in video_paths:
            if os.path.exists(video_path):
                # 为每个视频创建单独的输出目录
                if output_base_dir:
                    video_output_dir = os.path.join(
                        output_base_dir, Path(video_path).stem
                    )
                else:
                    video_output_dir = None

                results[video_path] = self.extract_frames(
                    video_path, video_output_dir, **kwargs
                )
            else:
                results[video_path] = self._create_error_result(
                    f"文件不存在: {video_path}"
                )

        return {
            "total_videos": len(video_paths),
            "successful_extractions": len(
                [r for r in results.values() if "error" not in r]
            ),
            "failed_extractions": len([r for r in results.values() if "error" in r]),
            "total_frames_extracted": sum(
                [
                    r.get("extracted_frames", 0)
                    for r in results.values()
                    if "error" not in r
                ]
            ),
            "results": results,
        }

    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {"error": error_msg, "timestamp": datetime.now().isoformat()}

    def get_supported_formats(self) -> Dict[str, str]:
        """获取支持的视频格式"""
        return self.supported_formats.copy()

    def validate_video_file(self, video_path: str) -> bool:
        """验证视频文件是否可读"""
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                return ret
            return False
        except:
            return False


# 全局实例
_frame_extractor = None


def get_frame_extractor() -> IntelligentVideoFrameExtractor:
    """获取视频帧提取器实例"""
    global _frame_extractor
    if _frame_extractor is None:
        _frame_extractor = IntelligentVideoFrameExtractor()
    return _frame_extractor


if __name__ == "__main__":
    # 测试代码
    extractor = IntelligentVideoFrameExtractor()
    print("支持的视频格式:", extractor.get_supported_formats())
