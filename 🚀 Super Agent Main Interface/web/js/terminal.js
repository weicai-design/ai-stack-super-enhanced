/**
 * 终端命令执行功能
 * 在聊天框中执行终端命令
 */

const API_BASE = '/api/super-agent';

class TerminalManager {
    constructor() {
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentDirectory = '/';
        this.init();
    }

    init() {
        const terminalBtn = document.getElementById('terminal-btn');
        const terminalClose = document.getElementById('terminal-close');
        const terminalInput = document.getElementById('terminal-input');
        const terminalExecute = document.getElementById('terminal-execute');
        const terminalHistoryBtn = document.getElementById('terminal-history-btn');
        const terminalClearBtn = document.getElementById('terminal-clear-btn');
        const terminalInfoBtn = document.getElementById('terminal-info-btn');

        // 打开/关闭终端
        terminalBtn.addEventListener('click', () => this.toggleTerminal());
        terminalClose.addEventListener('click', () => this.closeTerminal());

        // 执行命令
        terminalExecute.addEventListener('click', () => this.executeCommand());
        terminalInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeCommand();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.navigateHistory(-1);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.navigateHistory(1);
            }
        });

        // 工具栏按钮
        terminalHistoryBtn.addEventListener('click', () => this.showHistory());
        terminalClearBtn.addEventListener('click', () => this.clearOutput());
        terminalInfoBtn.addEventListener('click', () => this.showSystemInfo());

        // 初始化系统信息
        this.loadSystemInfo();
    }

    toggleTerminal() {
        const terminalArea = document.getElementById('terminal-area');
        const fileUploadArea = document.getElementById('file-upload-area');
        
        if (terminalArea.style.display === 'none') {
            terminalArea.style.display = 'block';
            fileUploadArea.style.display = 'none';
            document.getElementById('terminal-input').focus();
            this.loadSystemInfo();
        } else {
            terminalArea.style.display = 'none';
        }
    }

    closeTerminal() {
        document.getElementById('terminal-area').style.display = 'none';
    }

    async executeCommand() {
        const input = document.getElementById('terminal-input');
        const command = input.value.trim();
        
        if (!command) return;

        // 特殊命令处理
        if (command === 'exit' || command === 'quit') {
            this.closeTerminal();
            return;
        }

        if (command === 'clear') {
            this.clearOutput();
            input.value = '';
            return;
        }

        if (command.startsWith('cd ')) {
            const path = command.substring(3).trim();
            await this.changeDirectory(path);
            input.value = '';
            return;
        }

        // 显示命令
        this.addOutputLine(`$ ${command}`, 'command');

        // 添加到历史
        this.commandHistory.push(command);
        this.historyIndex = this.commandHistory.length;

        // 执行命令
        try {
            const response = await fetch(`${API_BASE}/terminal/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    command: command,
                    timeout: 30,
                    cwd: this.currentDirectory
                })
            });

            const result = await response.json();

            if (result.success) {
                // 显示输出
                if (result.stdout) {
                    this.addOutputLine(result.stdout, 'output');
                }
                if (result.stderr) {
                    this.addOutputLine(result.stderr, 'error');
                }
                
                // 更新工作目录（如果是cd命令）
                if (result.work_directory) {
                    this.currentDirectory = result.work_directory;
                    document.getElementById('terminal-cwd').textContent = this.currentDirectory;
                }
            } else {
                this.addOutputLine(`错误: ${result.error || '命令执行失败'}`, 'error');
            }
        } catch (error) {
            this.addOutputLine(`错误: ${error.message}`, 'error');
        }

        input.value = '';
        this.scrollToBottom();
    }

    addOutputLine(text, type = 'output') {
        const output = document.getElementById('terminal-output');
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = text;
        output.appendChild(line);
    }

    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;

        this.historyIndex += direction;
        
        if (this.historyIndex < 0) {
            this.historyIndex = 0;
        } else if (this.historyIndex >= this.commandHistory.length) {
            this.historyIndex = this.commandHistory.length;
            document.getElementById('terminal-input').value = '';
            return;
        }

        document.getElementById('terminal-input').value = this.commandHistory[this.historyIndex];
    }

    async showHistory() {
        try {
            const response = await fetch(`${API_BASE}/terminal/history?limit=20`);
            const result = await response.json();
            
            if (result.history && result.history.length > 0) {
                this.addOutputLine('\n=== 命令历史 ===', 'output');
                result.history.forEach((item, index) => {
                    this.addOutputLine(`${index + 1}. ${item.command}`, 'output');
                });
                this.addOutputLine('', 'output');
            } else {
                this.addOutputLine('暂无命令历史', 'output');
            }
        } catch (error) {
            this.addOutputLine(`获取历史失败: ${error.message}`, 'error');
        }
    }

    clearOutput() {
        const output = document.getElementById('terminal-output');
        output.innerHTML = `
            <div class="terminal-welcome">
                <p>欢迎使用终端命令执行器</p>
                <p>输入命令后按回车执行，输入 'exit' 退出</p>
                <p>当前目录: <span id="terminal-cwd">${this.currentDirectory}</span></p>
            </div>
        `;
    }

    async showSystemInfo() {
        try {
            const response = await fetch(`${API_BASE}/terminal/system-info`);
            const info = await response.json();
            
            this.addOutputLine('\n=== 系统信息 ===', 'output');
            this.addOutputLine(`平台: ${info.platform} ${info.platform_version}`, 'output');
            this.addOutputLine(`架构: ${info.architecture}`, 'output');
            this.addOutputLine(`Python版本: ${info.python_version}`, 'output');
            this.addOutputLine(`当前目录: ${info.current_directory}`, 'output');
            this.addOutputLine(`用户目录: ${info.home_directory}`, 'output');
            this.addOutputLine('', 'output');
        } catch (error) {
            this.addOutputLine(`获取系统信息失败: ${error.message}`, 'error');
        }
    }

    async loadSystemInfo() {
        try {
            const response = await fetch(`${API_BASE}/terminal/system-info`);
            const info = await response.json();
            this.currentDirectory = info.current_directory || '/';
            document.getElementById('terminal-cwd').textContent = this.currentDirectory;
        } catch (error) {
            console.error('加载系统信息失败:', error);
        }
    }

    async changeDirectory(path) {
        try {
            const response = await fetch(`${API_BASE}/terminal/cd`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: path })
            });

            const result = await response.json();

            if (result.success) {
                this.currentDirectory = result.new_directory;
                document.getElementById('terminal-cwd').textContent = this.currentDirectory;
                this.addOutputLine(`已切换到: ${this.currentDirectory}`, 'success');
            } else {
                this.addOutputLine(`切换目录失败: ${result.error}`, 'error');
            }
        } catch (error) {
            this.addOutputLine(`切换目录失败: ${error.message}`, 'error');
        }
    }

    scrollToBottom() {
        const output = document.getElementById('terminal-output');
        output.scrollTop = output.scrollHeight;
    }
}

// 初始化终端管理器
const terminalManager = new TerminalManager();


