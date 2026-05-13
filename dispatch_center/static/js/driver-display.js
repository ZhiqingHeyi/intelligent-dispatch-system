class DriverDisplay {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.refreshInterval = 2000;
        this.matchContainer = document.getElementById('matchContainer');
        this.loadingState = document.getElementById('loadingState');
        this.emptyState = document.getElementById('emptyState');
        this.currentTimeEl = document.getElementById('currentTime');
        this.updateInfoEl = document.getElementById('updateInfo');
        this.init();
    }

    async init() {
        this.startClock();
        await this.fetchData();
        setInterval(() => this.fetchData(), this.refreshInterval);
    }

    startClock() {
        var self = this;
        var tick = function() {
            var now = new Date();
            var h = String(now.getHours()).padStart(2, '0');
            var m = String(now.getMinutes()).padStart(2, '0');
            var s = String(now.getSeconds()).padStart(2, '0');
            if (self.currentTimeEl) {
                self.currentTimeEl.textContent = h + ':' + m + ':' + s;
            }
        };
        tick();
        setInterval(tick, 1000);
    }

    async fetchData() {
        try {
            var response = await fetch(this.apiBaseUrl + '/api/status');
            if (!response.ok) throw new Error('HTTP ' + response.status);
            var data = await response.json();

            var activeTasks = [];
            if (data.active_tasks) {
                for (var i = 0; i < data.active_tasks.length; i++) {
                    var t = data.active_tasks[i];
                    if (t.status === 'assigned' || t.status === 'in_progress') {
                        activeTasks.push(t);
                    }
                }
            }

            this.renderMatches(activeTasks);
            this.updateStatusInfo(true);
        } catch (err) {
            console.error('[DriverDisplay] fetch error:', err);
            this.showError();
            this.updateStatusInfo(false);
        }
    }

    renderMatches(tasks) {
        if (this.loadingState) this.loadingState.style.display = 'none';

        var old = this.matchContainer.querySelectorAll('.match-card');
        for (var i = 0; i < old.length; i++) old[i].remove();

        if (!tasks || tasks.length === 0) {
            if (this.emptyState) this.emptyState.style.display = 'block';
            return;
        }

        if (this.emptyState) this.emptyState.style.display = 'none';

        for (var idx = 0; idx < tasks.length; idx++) {
            var card = this.createMatchCard(tasks[idx], idx);
            this.matchContainer.appendChild(card);
        }
    }

    createMatchCard(task, index) {
        var card = document.createElement('div');
        card.className = 'match-card';
        card.style.animationDelay = (index * 0.1) + 's';

        var vehicleName = task.vehicle_name || '--';
        var cableCarId = task.cable_car_id || '--';
        var gradeName = task.grade_name || '';

        var vehicleSide = document.createElement('div');
        vehicleSide.className = 'vehicle-info';
        vehicleSide.innerHTML =
            '<div class="vehicle-label">车 辆</div>' +
            '<div class="vehicle-name">' + vehicleName + '</div>' +
            (gradeName ? '<div class="vehicle-grade">' + gradeName + '</div>' : '');

        var arrow = document.createElement('div');
        arrow.className = 'match-arrow';
        arrow.innerHTML =
            '<div class="arrow-line"></div>' +
            '<div class="arrow-symbol">▸</div>';

        var cableSide = document.createElement('div');
        cableSide.className = 'cable-car-info';
        cableSide.innerHTML =
            '<div class="cable-car-label">目 标 缆 机</div>' +
            '<div class="cable-car-number">' + cableCarId + '号</div>' +
            (gradeName ? '<div class="cable-car-grade">' + gradeName + '</div>' : '');

        card.appendChild(vehicleSide);
        card.appendChild(arrow);
        card.appendChild(cableSide);

        return card;
    }

    showError() {
        if (this.loadingState) this.loadingState.style.display = 'none';
        if (this.emptyState) {
            this.emptyState.style.display = 'block';
            var t = this.emptyState.querySelector('.empty-title');
            var d = this.emptyState.querySelector('.empty-desc');
            var ic = this.emptyState.querySelector('.empty-icon');
            if (t) t.textContent = '连接失败';
            if (d) d.textContent = '无法连接服务器';
            if (ic) ic.textContent = '⚠';
        }
    }

    updateStatusInfo(success) {
        if (!this.updateInfoEl) return;
        var now = new Date();
        var h = String(now.getHours()).padStart(2, '0');
        var m = String(now.getMinutes()).padStart(2, '0');
        var s = String(now.getSeconds()).padStart(2, '0');
        var timeStr = h + ':' + m + ':' + s;
        if (success) {
            this.updateInfoEl.textContent = '已更新 ' + timeStr;
            this.updateInfoEl.style.color = '';
        } else {
            this.updateInfoEl.textContent = '更新失败 ' + timeStr;
            this.updateInfoEl.style.color = '#FF6B6B';
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.driverDisplay = new DriverDisplay();
});
