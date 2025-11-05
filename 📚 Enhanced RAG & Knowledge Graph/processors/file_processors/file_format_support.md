# 文件格式支持清单

根据需求1.1，需要支持**所有格式**的文件。

---

## 📋 当前支持情况

### ✅ 已支持的格式

#### 办公文件
- ✅ DOC, DOCX (Word)
- ✅ XLS, XLSX (Excel)
- ✅ PPT, PPTX (PowerPoint)
- ✅ PDF
- ✅ ODT, ODS, ODP (OpenDocument)

#### 电子书
- ✅ EPUB
- ✅ MOBI
- ✅ AZW3
- ✅ FB2

#### 编程文件
- ✅ Python (.py)
- ✅ JavaScript (.js)
- ✅ Java (.java)
- ✅ C/C++ (.c, .cpp)
- ✅ HTML/CSS (.html, .css)
- ✅ PHP (.php)
- ✅ Ruby (.rb)
- ✅ Go (.go)
- ✅ Rust (.rs)
- ✅ TypeScript (.ts)

#### 图片
- ✅ JPG/JPEG
- ✅ PNG
- ✅ GIF
- ✅ BMP
- ✅ TIFF
- ✅ WEBP
- ✅ SVG

#### 音频
- ✅ MP3
- ✅ WAV
- ✅ FLAC
- ✅ AAC

#### 视频
- ✅ MP4
- ✅ AVI
- ✅ MOV
- ✅ MKV

#### 思维导图
- ✅ XMIND (.xmind)

#### 数据库
- ✅ CSV
- ✅ SQL

#### 文本
- ✅ TXT
- ✅ MD
- ✅ JSON
- ✅ XML
- ✅ YAML

---

## ⚠️ 需要添加的格式

### 办公文件（扩展）
- ⚠️ RTF (Rich Text Format)
- ⚠️ DOCM (Word Macro-enabled)
- ⚠️ DOT, DOTX (Word Templates)
- ⚠️ XLSM, XLSB (Excel Macro-enabled/Binary)
- ⚠️ XLT, XLTX (Excel Templates)
- ⚠️ POT, POTX, PPTM (PowerPoint Templates/Macro)
- ⚠️ MSG (Outlook Message)
- ⚠️ EML (Email)

### 电子书（扩展）
- ⚠️ AZW (Kindle)
- ⚠️ LIT (Microsoft Reader)
- ⚠️ PRC (Palm)
- ⚠️ TXT (纯文本电子书)
- ⚠️ RTF (作为电子书)

### 编程文件（扩展）
- ⚠️ C# (.cs)
- ⚠️ Swift (.swift)
- ⚠️ Kotlin (.kt)
- ⚠️ Scala (.scala)
- ⚠️ Dart (.dart)
- ⚠️ Lua (.lua)
- ⚠️ Perl (.pl, .pm)
- ⚠️ Shell Script (.sh, .bash)
- ⚠️ PowerShell (.ps1)
- ⚠️ R (.r, .R)
- ⚠️ MATLAB (.m)
- ⚠️ SQL (.sql)
- ⚠️ Markdown (.md)
- ⚠️ Config files (.conf, .ini, .toml)
- ⚠️ Dockerfile
- ⚠️ Makefile
- ⚠️ YAML (.yaml, .yml)
- ⚠️ JSON (.json)

### 图片（扩展）
- ⚠️ HEIC/HEIF (iOS照片)
- ⚠️ RAW (相机原始格式: CR2, NEF, ARW等)
- ⚠️ ICO
- ⚠️ PSD (Photoshop)
- ⚠️ AI (Illustrator)

### 音频（扩展）
- ⚠️ OGG
- ⚠️ M4A
- ⚠️ WMA
- ⚠️ OPUS
- ⚠️ AMR
- ⚠️ 3GP

### 视频（扩展）
- ⚠️ MPEG, MPG
- ⚠️ WMV
- ⚠️ FLV
- ⚠️ WEBM
- ⚠️ 3GP
- ⚠️ RM/RMVB
- ⚠️ VOB

### 思维导图（扩展）
- ⚠️ MM (FreeMind)
- ⚠️ MMAP (MindManager)
- ⚠️ OPML (大纲格式)

### 数据库（扩展）
- ⚠️ DB (SQLite)
- ⚠️ MDB, ACCDB (Access)
- ⚠️ FDB (Firebird)
- ⚠️ ODB (OpenOffice Base)

### 其他
- ⚠️ ZIP, RAR, 7Z (压缩文件，需要解压后处理)
- ⚠️ Archive formats

---

## 🎯 实施计划

### 阶段1: 扩展常见格式（立即）
1. 添加更多编程语言支持
2. 添加更多音频/视频格式
3. 添加更多办公文件格式
4. 添加更多电子书格式

### 阶段2: 特殊格式处理（后续）
1. 压缩文件解压支持
2. RAW图片格式
3. 专业格式（PSD, AI等）

---

**最后更新**: 2025-11-02

