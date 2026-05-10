/**
 * 司机专用大屏幕显示 - 数据逻辑
 * 功能：获取匹配数据、渲染卡片、自动刷新、时间更新
 */

class DriverDisplay {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.refreshInterval = 2000; // 2秒刷新一次
        this.matchContainer = document.getElementById('matchContainer');
        this.loadingState = document.getElementById('loadingState');
        this.emptyState = document.getElementById('emptyState');
        this.currentTimeEl = document.getElementById('currentTime');
        this.updateInfoEl = document.getElementById('updateInfo');
        
        this.init();
    }

    async init() {
        console.log('[DriverDisplay] 初始化司机显示屏...');
        
        // 启动时钟
        this.startClock();
        
        // 首次加载数据
        await this.fetchData();
        
        // 设置定时刷新
        setInterval(() => this fetchData(), this.refreshInterval);
        
        console.log('[DriverDisplay] 初始化完成');
    }

    /**
     * 启动实时时钟
     */
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('zh-CN', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            if (this.currentTimeEl) {
                this.currentTimeEl.textContent = timeStr;
            }
        };
        
        updateClock();
        setInterval(updateClock, 1000); // 每秒更新
    }

    /**
     * 从API获取调度数据
     */
    async fetchData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/status`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('[DriverDisplay] 获取数据成功:', data);
            
            // 过滤出当前正在进行的匹配任务（status === 'assigned'）
            const activeTasks = data.active_tasks.filter(task => task.status === 'assigned');
            
            // 渲染匹配卡片
            this.renderMatches(activeTasks);
            
            // 更新状态信息
            this.updateStatusInfo(true);
            
        } catch (error) {
            console.error('[DriverDisplay] 获取数据失败:', error);
            this.showError();
            this.updateStatusInfo(false);
        }
    }

    /**
     * 渲染匹配卡片列表
     * @param {Array} tasks - 活跃的任务列表
     */
    renderMatches(tasks) {
        // 隐藏加载状态
        if (this.loadingState) {
            this.loadingState.style.display = 'none';
        }

        // 清空容器（保留loadingState元素）
        const existingCards = this.matchContainer.querySelectorAll('.match-card');
        existingCards.forEach(card => card.remove());

        // 如果没有活跃任务，显示空状态
        if (tasks.length === 0) {
            if (this.emptyState) {
                this.emptyState.style.display = 'block';
            }
            return;
        }

        // 隐藏空状态
        if (this.emptyState) {
            this.emptyState.style.display = 'none';
        }

        // 为每个任务创建匹配卡片
        tasks.forEach((task, index) => {
            const card = this.createMatchCard(task, index);
            this.matchContainer.appendChild(card);
        });

        console.log(`[DriverDisplay] 渲染了 ${tasks.length} 个匹配卡片`);
    }

    /**
     * 创建单个匹配卡片
     * @param {Object} task - 任务对象
     * @param {number} index - 索引（用于动画延迟）
     * @returns {HTMLElement} 卡片DOM元素
     */
    createMatchCard(task, index) {
        const card = document.createElement('div');
        card.className = 'match-card';
        card.style.animationDelay = `${index * 0.15}s`;

        // 缆机信息
        const cableCarInfo = document.createElement('div');
        cableCarInfo.className = 'cable-car-info';
        cableCarInfo.innerHTML = `
            <div class="cable-car-label">🏗️ 缆 机</div>
            <div class="cable-car-number">${task.cable_car_id}号</div>
            <div class="cable-car-grade">${task.grade_name || '未设置'}</div>
        `;

        // 中间箭头
        const arrowContainer = document.createElement('div');
        arrowContainer.className = 'match-arrow-container';
        arrowContainer.innerHTML = `
            <div class="arrow-line"></div>
            <div class="arrow-head">➜</div>
        `;

        // 车辆信息
        const vehicleInfo = document.createElement('div');
        vehicleInfo.className = 'vehicle-info';
        vehicleInfo.innerHTML = `
            <div class="vehicle-label">🚛 车 辆</div>
            <div class="vehicle-name">${task.vehicle_name}</div>
            <div class="vehicle-icon">🚛</div>
        `;

        // 组装卡片
        card.appendChild(cableCarInfo);
        card.appendChild(arrowContainer);
        card.appendChild(vehicleInfo);

        return card;
    }

    /**
     * 显示错误状态
     */
    showError() {
        if (this.loadingState) {
            this.loadingState.style.display = 'none';
        }
        
        if (this.emptyState) {
            this.emptyState.style.display = 'block';
            const emptyTitle = this.emptyState.querySelector('.empty-title');
            const emptyDesc = this.emptyState.querySelector('.empty-desc');
            const emptyIcon = this.emptyState.querySelector('.empty-icon');
            
            if (emptyTitle) emptyTitle.textContent = '⚠️ 连接失败';
            if (emptyDesc) emptyDesc.textContent = '无法连接到服务器，请检查网络...';
            if (emptyIcon) emptyIcon.textContent = '❌';
        }
    }

    /**
     * 更新底部状态信息
     * @param {boolean} success - 是否成功
     */
    updateStatusInfo(success) {
        if (!this.updateInfoEl) return;

        const now = new Date();
        const timeStr = now.toLocaleTimeString('zh-CN', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        if (success) {
            this.updateInfoEl.textContent = `✓ 更新于 ${timeStr}`;
            this.updateInfoEl.style.color = '#00FF41';
        } else {
            this.updateInfoEl.textContent = `✗ 更新失败 ${timeStr}`;
            this.updateInfoEl.style.color = '#FF6B6B';
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.driverDisplay = new DriverDisplay();
});
