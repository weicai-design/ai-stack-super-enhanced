/**
 * ERP界面通用功能库
 * 提供统一的CRUD操作、表单验证、数据格式化等功能
 */

// 通用API基础URL
const API_BASE = '/api';

// 通用CRUD操作
const CommonCRUD = {
    /**
     * 创建记录
     */
    async create(endpoint, data) {
        try {
            const response = await axios.post(`${API_BASE}${endpoint}`, data);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || error.message };
        }
    },

    /**
     * 更新记录
     */
    async update(endpoint, id, data) {
        try {
            const response = await axios.put(`${API_BASE}${endpoint}/${id}`, data);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || error.message };
        }
    },

    /**
     * 删除记录
     */
    async delete(endpoint, id) {
        try {
            await axios.delete(`${API_BASE}${endpoint}/${id}`);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || error.message };
        }
    },

    /**
     * 获取记录列表
     */
    async list(endpoint, params = {}) {
        try {
            const response = await axios.get(`${API_BASE}${endpoint}`, { params });
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || error.message };
        }
    },

    /**
     * 获取单条记录
     */
    async get(endpoint, id) {
        try {
            const response = await axios.get(`${API_BASE}${endpoint}/${id}`);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || error.message };
        }
    }
};

// 表单验证工具
const FormValidator = {
    /**
     * 验证必填字段
     */
    validateRequired(fields, data) {
        const errors = [];
        fields.forEach(field => {
            if (!data[field] || (typeof data[field] === 'string' && !data[field].trim())) {
                errors.push(`${field}不能为空`);
            }
        });
        return errors;
    },

    /**
     * 验证数字范围
     */
    validateNumberRange(field, value, min, max) {
        const num = parseFloat(value);
        if (isNaN(num)) {
            return `${field}必须是数字`;
        }
        if (min !== undefined && num < min) {
            return `${field}不能小于${min}`;
        }
        if (max !== undefined && num > max) {
            return `${field}不能大于${max}`;
        }
        return null;
    },

    /**
     * 验证日期范围
     */
    validateDateRange(startDate, endDate) {
        if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
            return '开始日期不能晚于结束日期';
        }
        return null;
    }
};

// 数据格式化工具
const DataFormatter = {
    /**
     * 格式化金额
     */
    formatCurrency(amount) {
        if (amount === null || amount === undefined) return '¥0.00';
        return `¥${parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
    },

    /**
     * 格式化日期
     */
    formatDate(date, format = 'YYYY-MM-DD') {
        if (!date) return '-';
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return format.replace('YYYY', year).replace('MM', month).replace('DD', day);
    },

    /**
     * 格式化日期时间
     */
    formatDateTime(datetime) {
        if (!datetime) return '-';
        const d = new Date(datetime);
        return `${this.formatDate(d)} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
    },

    /**
     * 格式化状态标签
     */
    formatStatus(status, statusMap) {
        const statusInfo = statusMap[status] || { text: status, type: 'info' };
        return statusInfo;
    }
};

// 通用对话框组件
const CommonDialog = {
    /**
     * 显示确认对话框
     */
    confirm(message, title = '确认') {
        return new Promise((resolve) => {
            ElementPlus.ElMessageBox.confirm(message, title, {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(() => resolve(true)).catch(() => resolve(false));
        });
    },

    /**
     * 显示表单对话框
     */
    showFormDialog(formConfig, initialData = {}) {
        return new Promise((resolve) => {
            const formData = { ...initialData };
            const formRef = {};

            ElementPlus.ElMessageBox({
                title: formConfig.title || '表单',
                message: this._createFormHTML(formConfig.fields, formData),
                dangerouslyUseHTMLString: true,
                showCancelButton: true,
                confirmButtonText: '保存',
                cancelButtonText: '取消',
                beforeClose: (action, instance, done) => {
                    if (action === 'confirm') {
                        // 收集表单数据
                        const inputs = instance.$el.querySelectorAll('input, select, textarea');
                        inputs.forEach(input => {
                            formData[input.name] = input.value;
                        });
                        resolve(formData);
                    } else {
                        resolve(null);
                    }
                    done();
                }
            });
        });
    },

    _createFormHTML(fields, data) {
        let html = '<div style="padding: 10px;">';
        fields.forEach(field => {
            html += `<div style="margin-bottom: 15px;">`;
            html += `<label style="display: block; margin-bottom: 5px;">${field.label}:</label>`;
            
            if (field.type === 'select') {
                html += `<select name="${field.name}" style="width: 100%; padding: 8px;">`;
                field.options.forEach(opt => {
                    html += `<option value="${opt.value}" ${data[field.name] === opt.value ? 'selected' : ''}>${opt.label}</option>`;
                });
                html += `</select>`;
            } else if (field.type === 'textarea') {
                html += `<textarea name="${field.name}" style="width: 100%; padding: 8px; min-height: 60px;">${data[field.name] || ''}</textarea>`;
            } else {
                html += `<input type="${field.type || 'text'}" name="${field.name}" value="${data[field.name] || ''}" style="width: 100%; padding: 8px;" />`;
            }
            
            html += `</div>`;
        });
        html += '</div>';
        return html;
    }
};

// 导出通用功能
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CommonCRUD, FormValidator, DataFormatter, CommonDialog };
}

