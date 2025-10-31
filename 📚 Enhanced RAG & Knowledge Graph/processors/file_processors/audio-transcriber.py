#!/usr/bin/env python3
"""
音频转录器 - 多格式音频转文本
功能：支持MP3、WAV、M4A等格式，语音识别，说话人分离
版本: 2.1.0
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    import pydub
    import speech_recognition as sr
    from pydub import AudioSegment

    HAS_AUDIO_DEPS = True
except ImportError as e:
    logging.warning(f"音频处理依赖缺失: {e}")
    HAS_AUDIO_DEPS = False


class IntelligentAudioTranscriber:
    """智能音频转录器"""

    def __init__(self, model_size: str = "base"):
        """
        初始化音频转录器

        Args:
            model_size: 语音识别模型大小 [tiny, base, small, medium, large]
        """
        self.logger = logging.getLogger(__name__)

        if not HAS_AUDIO_DEPS:
            self.logger.error("音频处理依赖未安装，转录功能不可用")
            return

        self.recognizer = sr.Recognizer()

        self.supported_formats = {
            ".wav": "WAV",
            ".mp3": "MP3",
            ".m4a": "M4A",
            ".flac": "FLAC",
            ".aac": "AAC",
            ".ogg": "OGG",
            ".wma": "WMA",
        }

        self.recognition_engines = {
            "google": self._recognize_google,
            "sphinx": self._recognize_sphinx,
            "whisper": self._recognize_whisper,
        }

        self.model_size = model_size

    def transcribe_audio(
        self,
        audio_path: str,
        engine: str = "google",
        language: str = "zh-CN",
        chunk_duration: int = 30,
        speaker_diarization: bool = False,
    ) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            engine: 识别引擎 [google, sphinx, whisper]
            language: 语言代码
            chunk_duration: 分块时长(秒)
            speaker_diarization: 是否进行说话人分离

        Returns:
            转录结果字典
        """
        if not HAS_AUDIO_DEPS:
            return self._create_error_result("音频处理依赖未安装")

        try:
            if not os.path.exists(audio_path):
                return self._create_error_result(f"音频文件不存在: {audio_path}")

            # 验证音频格式
            file_ext = Path(audio_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return self._create_error_result(f"不支持的音频格式: {file_ext}")

            # 获取文件信息
            file_info = self._get_audio_info(audio_path)
            if "error" in file_info:
                return file_info

            # 转换为WAV格式（如果需要）
            wav_path = self._convert_to_wav(audio_path)
            if wav_path is None:
                return self._create_error_result("音频格式转换失败")

            # 分块处理长音频
            if file_info["duration"] > chunk_duration:
                transcription_result = self._transcribe_long_audio(
                    wav_path, engine, language, chunk_duration, speaker_diarization
                )
            else:
                transcription_result = self._transcribe_short_audio(
                    wav_path, engine, language, speaker_diarization
                )

            # 清理临时文件
            if wav_path != audio_path:
                try:
                    os.remove(wav_path)
                except:
                    pass

            # 构建完整结果
            result = {
                "file_path": audio_path,
                "file_name": Path(audio_path).name,
                "file_size": os.path.getsize(audio_path),
                "file_info": file_info,
                "transcription_engine": engine,
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "transcription": transcription_result["text"],
                "segments": transcription_result.get("segments", []),
                "confidence": transcription_result.get("confidence", 0),
                "speaker_count": transcription_result.get("speaker_count", 1),
                "processing_time": transcription_result.get("processing_time", 0),
            }

            return result

        except Exception as e:
            self.logger.error(f"音频转录失败 {audio_path}: {str(e)}")
            return self._create_error_result(str(e))

    def _get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """获取音频文件信息"""
        try:
            audio = AudioSegment.from_file(audio_path)

            return {
                "format": self.supported_formats.get(
                    Path(audio_path).suffix.lower(), "unknown"
                ),
                "duration": len(audio) / 1000.0,  # 转换为秒
                "channels": audio.channels,
                "sample_width": audio.sample_width,
                "frame_rate": audio.frame_rate,
                "frame_count": audio.frame_count(),
                "max_amplitude": audio.max,
                "rms": audio.rms,
            }
        except Exception as e:
            return {"error": f"音频信息获取失败: {str(e)}"}

    def _convert_to_wav(self, audio_path: str) -> Optional[str]:
        """转换为WAV格式"""
        try:
            if audio_path.lower().endswith(".wav"):
                return audio_path

            # 创建临时WAV文件
            temp_wav = f"temp_{os.path.basename(audio_path)}.wav"
            audio = AudioSegment.from_file(audio_path)
            audio.export(temp_wav, format="wav")

            return temp_wav
        except Exception as e:
            self.logger.error(f"音频转换失败: {e}")
            return None

    def _transcribe_short_audio(
        self, wav_path: str, engine: str, language: str, speaker_diarization: bool
    ) -> Dict[str, Any]:
        """转录短音频（小于分块时长）"""
        import time

        start_time = time.time()

        try:
            with sr.AudioFile(wav_path) as source:
                # 调整环境噪声
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # 读取整个音频
                audio_data = self.recognizer.record(source)

                # 选择识别引擎
                if engine in self.recognition_engines:
                    result = self.recognition_engines[engine](audio_data, language)
                else:
                    result = self._recognize_google(audio_data, language)

                result["processing_time"] = time.time() - start_time
                return result

        except Exception as e:
            self.logger.error(f"短音频转录失败: {e}")
            return {
                "text": "",
                "confidence": 0,
                "processing_time": time.time() - start_time,
            }

    def _transcribe_long_audio(
        self,
        wav_path: str,
        engine: str,
        language: str,
        chunk_duration: int,
        speaker_diarization: bool,
    ) -> Dict[str, Any]:
        """转录长音频（分块处理）"""
        import time

        start_time = time.time()

        try:
            audio = AudioSegment.from_wav(wav_path)
            duration_ms = len(audio)
            chunk_ms = chunk_duration * 1000

            segments = []
            full_text = []

            for i in range(0, duration_ms, chunk_ms):
                # 提取音频块
                chunk = audio[i : i + chunk_ms]

                # 保存临时块文件
                chunk_path = f"chunk_{i//chunk_ms}.wav"
                chunk.export(chunk_path, format="wav")

                # 转录当前块
                with sr.AudioFile(chunk_path) as source:
                    audio_data = self.recognizer.record(source)

                    if engine in self.recognition_engines:
                        chunk_result = self.recognition_engines[engine](
                            audio_data, language
                        )
                    else:
                        chunk_result = self._recognize_google(audio_data, language)

                # 记录分段信息
                segment_info = {
                    "start_time": i / 1000.0,
                    "end_time": (i + chunk_ms) / 1000.0,
                    "text": chunk_result.get("text", ""),
                    "confidence": chunk_result.get("confidence", 0),
                }

                segments.append(segment_info)
                full_text.append(chunk_result.get("text", ""))

                # 清理临时文件
                try:
                    os.remove(chunk_path)
                except:
                    pass

            # 计算整体置信度
            confidences = [s["confidence"] for s in segments if s["confidence"] > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": " ".join(full_text),
                "segments": segments,
                "confidence": avg_confidence,
                "speaker_count": (
                    self._detect_speakers(segments) if speaker_diarization else 1
                ),
                "processing_time": time.time() - start_time,
            }

        except Exception as e:
            self.logger.error(f"长音频转录失败: {e}")
            return {
                "text": "",
                "segments": [],
                "confidence": 0,
                "processing_time": time.time() - start_time,
            }

    def _recognize_google(self, audio_data, language: str) -> Dict[str, Any]:
        """使用Google语音识别"""
        try:
            text = self.recognizer.recognize_google(audio_data, language=language)
            return {"text": text, "confidence": 0.8}  # Google不返回置信度
        except sr.UnknownValueError:
            return {"text": "", "confidence": 0}
        except sr.RequestError as e:
            self.logger.error(f"Google识别请求失败: {e}")
            return {"text": "", "confidence": 0}

    def _recognize_sphinx(self, audio_data, language: str) -> Dict[str, Any]:
        """使用CMU Sphinx离线识别"""
        try:
            text = self.recognizer.recognize_sphinx(audio_data, language=language)
            return {"text": text, "confidence": 0.6}
        except sr.UnknownValueError:
            return {"text": "", "confidence": 0}
        except Exception as e:
            self.logger.error(f"Sphinx识别失败: {e}")
            return {"text": "", "confidence": 0}

    def _recognize_whisper(self, audio_data, language: str) -> Dict[str, Any]:
        """使用OpenAI Whisper识别"""
        try:
            # 这里需要安装openai-whisper
            import whisper

            # 保存临时音频文件
            temp_path = "temp_whisper.wav"
            with open(temp_path, "wb") as f:
                f.write(audio_data.get_wav_data())

            # 加载模型并转录
            model = whisper.load_model(self.model_size)
            result = model.transcribe(temp_path, language=language)

            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass

            return {
                "text": result["text"],
                "confidence": (
                    np.mean([seg["confidence"] for seg in result["segments"]])
                    if "segments" in result
                    else 0.8
                ),
            }

        except ImportError:
            self.logger.warning("Whisper未安装，使用Google引擎")
            return self._recognize_google(audio_data, language)
        except Exception as e:
            self.logger.error(f"Whisper识别失败: {e}")
            return self._recognize_google(audio_data, language)

    def _detect_speakers(self, segments: List[Dict]) -> int:
        """简单说话人检测（基于文本特征）"""
        if len(segments) < 2:
            return 1

        # 基于停顿和文本特征检测说话人变化
        speaker_changes = 0
        prev_segment = segments[0]

        for i in range(1, len(segments)):
            current_segment = segments[i]

            # 检查时间间隔（长停顿可能表示说话人变化）
            time_gap = current_segment["start_time"] - prev_segment["end_time"]

            # 检查文本特征变化（词汇使用、句子长度等）
            prev_text = prev_segment["text"].strip()
            curr_text = current_segment["text"].strip()

            if time_gap > 2.0 or (  # 长停顿
                prev_text and curr_text and abs(len(prev_text) - len(curr_text)) > 50
            ):  # 文本长度显著变化
                speaker_changes += 1

            prev_segment = current_segment

        return min(speaker_changes + 1, 4)  # 最多4个说话人

    def batch_transcribe(self, audio_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        批量转录音频文件

        Args:
            audio_paths: 音频文件路径列表
            **kwargs: 其他参数

        Returns:
            批量处理结果
        """
        results = {}

        for audio_path in audio_paths:
            if os.path.exists(audio_path):
                results[audio_path] = self.transcribe_audio(audio_path, **kwargs)
            else:
                results[audio_path] = self._create_error_result(
                    f"文件不存在: {audio_path}"
                )

        return {
            "total_audios": len(audio_paths),
            "successful_transcriptions": len(
                [r for r in results.values() if "error" not in r]
            ),
            "failed_transcriptions": len([r for r in results.values() if "error" in r]),
            "results": results,
        }

    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {"error": error_msg, "timestamp": datetime.now().isoformat()}

    def get_supported_formats(self) -> Dict[str, str]:
        """获取支持的音频格式"""
        return self.supported_formats.copy()


# 全局实例
_audio_transcriber = None


def get_audio_transcriber(model_size: str = "base") -> IntelligentAudioTranscriber:
    """获取音频转录器实例"""
    global _audio_transcriber
    if _audio_transcriber is None:
        _audio_transcriber = IntelligentAudioTranscriber(model_size)
    return _audio_transcriber


if __name__ == "__main__":
    # 测试代码
    transcriber = IntelligentAudioTranscriber()
    print("支持的音频格式:", transcriber.get_supported_formats())

class AudioTranscriber:
    def __init__(self):
        self.supported_formats = ['mp3', 'wav', 'm4a', 'flac']
    
    def transcribe(self, audio_path):
        # 基本的转录功能占位
        print(f'音频转录: {audio_path}')
        return '音频转录文本'
    
    def get_supported_formats(self):
        return self.supported_formats
