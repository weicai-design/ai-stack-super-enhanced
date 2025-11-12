/**
 * ERP界面通用功能库
 * 提供CRUD操作、数据验证、导出等通用功能
 */

// 通用CRUD操作
const CommonCRUD = {
    /**
     * 创建记录
     */
    async create(apiUrl, data, options = {}) {
        try {
            // 数据验证
            if (options.validate && typeof options.validate === 'function') {
                const validation = options.validate(data);
                if (!validation.valid) {
                    ElementPlus.ElMessage.warning(validation.message || '数据验证失败');
                    return { success: false, message: validation.message };
                }
            }
            
            const response = await axios.post(apiUrl, data, {
                timeout: options.timeout || 30000,
                ...options.axiosConfig
            });
            
            if (response.data.success) {
                ElementPlus.ElMessage.success(options.successMessage || '创建成功');
                return response.data;
            } else {
                throw new Error(response.data.message || '创建失败');
            }
        } catch (error) {
            const errorMsg = this._extractErrorMessage(error);
            ElementPlus.ElMessage.error(options.errorMessage || '创建失败: ' + errorMsg);
            if (options.onError && typeof options.onError === 'function') {
                options.onError(error);
            }
            throw error;
        }
    },
    
    /**
     * 提取错误信息
     */
    _extractErrorMessage(error) {
        if (error.response) {
            // 服务器返回的错误
            if (error.response.data) {
                if (typeof error.response.data === 'string') {
                    return error.response.data;
                }
                return error.response.data.detail || error.response.data.message || '服务器错误';
            }
            return `HTTP ${error.response.status}: ${error.response.statusText}`;
        } else if (error.request) {
            // 请求已发出但没有收到响应
            return '网络错误，请检查网络连接';
        } else {
            // 其他错误
            return error.message || '未知错误';
        }
    },

    /**
     * 更新记录
     */
    async update(apiUrl, id, data, options = {}) {
        try {
            if (!id) {
                throw new Error('记录ID不能为空');
            }
            
            // 数据验证
            if (options.validate && typeof options.validate === 'function') {
                const validation = options.validate(data);
                if (!validation.valid) {
                    ElementPlus.ElMessage.warning(validation.message || '数据验证失败');
                    return { success: false, message: validation.message };
                }
            }
            
            const response = await axios.put(`${apiUrl}/${id}`, data, {
                timeout: options.timeout || 30000,
                ...options.axiosConfig
            });
            
            if (response.data.success) {
                ElementPlus.ElMessage.success(options.successMessage || '更新成功');
                return response.data;
            } else {
                throw new Error(response.data.message || '更新失败');
            }
        } catch (error) {
            const errorMsg = this._extractErrorMessage(error);
            ElementPlus.ElMessage.error(options.errorMessage || '更新失败: ' + errorMsg);
            if (options.onError && typeof options.onError === 'function') {
                options.onError(error);
            }
            throw error;
        }
    },

    /**
     * 删除记录
     */
    async delete(apiUrl, id, confirmMessage = '确定要删除这条记录吗？', options = {}) {
        try {
            if (!id) {
                throw new Error('记录ID不能为空');
            }
            
            await ElementPlus.ElMessageBox.confirm(
                confirmMessage, 
                options.title || '提示', 
                {
                    confirmButtonText: options.confirmText || '确定',
                    cancelButtonText: options.cancelText || '取消',
                    type: options.type || 'warning',
                    dangerouslyUseHTMLString: options.dangerouslyUseHTMLString || false
                }
            );
            
            const response = await axios.delete(`${apiUrl}/${id}`, {
                timeout: options.timeout || 30000,
                ...options.axiosConfig
            });
            
            if (response.data.success) {
                ElementPlus.ElMessage.success(options.successMessage || '删除成功');
                return response.data;
            } else {
                throw new Error(response.data.message || '删除失败');
            }
        } catch (error) {
            if (error !== 'cancel') {
                const errorMsg = this._extractErrorMessage(error);
                ElementPlus.ElMessage.error(options.errorMessage || '删除失败: ' + errorMsg);
                if (options.onError && typeof options.onError === 'function') {
                    options.onError(error);
                }
            }
            throw error;
        }
    },

    /**
     * 批量删除
     */
    async batchDelete(apiUrl, ids, confirmMessage = '确定要删除选中的记录吗？') {
        try {
            await ElementPlus.ElMessageBox.confirm(confirmMessage, '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            });
            
            const response = await axios.post(`${apiUrl}/batch-delete`, { ids });
            if (response.data.success) {
                ElementPlus.ElMessage.success(`成功删除${response.data.count}条记录`);
                return response.data;
            } else {
                throw new Error(response.data.message || '批量删除失败');
            }
        } catch (error) {
            if (error !== 'cancel') {
                ElementPlus.ElMessage.error('批量删除失败: ' + (error.response?.data?.detail || error.message));
            }
            throw error;
        }
    }
};

// 数据导出功能
const DataExport = {
    /**
     * 导出到Excel
     */
    async exportToExcel(data, filename, title, options = {}) {
        try {
            if (!data || data.length === 0) {
                ElementPlus.ElMessage.warning('没有数据可导出');
                return;
            }
            
            // 显示加载提示
            const loading = ElementPlus.ElLoading.service({
                lock: true,
                text: '正在导出...',
                background: 'rgba(0, 0, 0, 0.7)'
            });
            
            try {
                const response = await axios.post('/api/export/excel', {
                    data: data,
                    filename: filename,
                    title: title,
                    ...options.exportConfig
                }, {
                    responseType: 'blob',
                    timeout: options.timeout || 60000
                });
                
                // 检查响应类型
                if (response.data instanceof Blob) {
                    const url = window.URL.createObjectURL(response.data);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', filename || `export_${new Date().getTime()}.xlsx`);
                    document.body.appendChild(link);
                    link.click();
                    
                    // 清理
                    setTimeout(() => {
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                    }, 100);
                    
                    ElementPlus.ElMessage.success(options.successMessage || '导出成功');
                } else {
                    throw new Error('导出文件格式错误');
                }
            } finally {
                loading.close();
            }
        } catch (error) {
            const errorMsg = error.response?.data 
                ? await this._extractBlobError(error.response.data)
                : error.message;
            ElementPlus.ElMessage.error(options.errorMessage || '导出失败: ' + errorMsg);
            if (options.onError && typeof options.onError === 'function') {
                options.onError(error);
            }
        }
    },
    
    /**
     * 提取Blob错误信息
     */
    async _extractBlobError(blob) {
        try {
            const text = await blob.text();
            const json = JSON.parse(text);
            return json.detail || json.message || '导出失败';
        } catch {
            return '导出失败';
        }
    },

    /**
     * 导出到CSV
     */
    async exportToCSV(data, filename) {
        try {
            const response = await axios.post('/api/export/csv', {
                data: data,
                filename: filename
            }, {
                responseType: 'blob'
            });
            
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename || `export_${new Date().getTime()}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            
            ElementPlus.ElMessage.success('导出成功');
        } catch (error) {
            ElementPlus.ElMessage.error('导出失败: ' + error.message);
        }
    }
};

// 数据验证
const DataValidator = {
    /**
     * 验证必填字段
     */
    validateRequired(data, requiredFields) {
        const errors = [];
        for (const field of requiredFields) {
            if (!data[field] || (typeof data[field] === 'string' && !data[field].trim())) {
                errors.push(`${field}不能为空`);
            }
        }
        return errors;
    },

    /**
     * 验证数字范围
     */
    validateNumberRange(value, min, max) {
        const num = parseFloat(value);
        if (isNaN(num)) return false;
        return num >= min && num <= max;
    },

    /**
     * 验证日期
     */
    validateDate(dateStr) {
        const date = new Date(dateStr);
        return date instanceof Date && !isNaN(date);
    }
};

// 工具函数
const Utils = {
    /**
     * 格式化日期
     */
    formatDate(date, format = 'YYYY-MM-DD') {
        if (!date) return '';
        
        try {
            const d = new Date(date);
            if (isNaN(d.getTime())) {
                return '';
            }
            
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            const hour = String(d.getHours()).padStart(2, '0');
            const minute = String(d.getMinutes()).padStart(2, '0');
            const second = String(d.getSeconds()).padStart(2, '0');
            
            return format
                .replace('YYYY', year)
                .replace('MM', month)
                .replace('DD', day)
                .replace('HH', hour)
                .replace('mm', minute)
                .replace('ss', second);
        } catch (error) {
            console.error('日期格式化失败:', error);
            return '';
        }
    },
    
    /**
     * 防抖函数
     */
    debounce(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * 节流函数
     */
    throttle(func, limit = 300) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * 格式化金额
     */
    formatCurrency(amount, currency = '¥') {
        if (amount === null || amount === undefined) return '';
        return currency + parseFloat(amount).toLocaleString('zh-CN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    },

    /**
     * 格式化百分比
     */
    formatPercent(value, decimals = 2) {
        if (value === null || value === undefined) return '';
        return (parseFloat(value) * 100).toFixed(decimals) + '%';
    },

    /**
     * 深拷贝
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    }
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CommonCRUD, DataExport, DataValidator, Utils };
}

