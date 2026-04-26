let appState = {
    cableCars: [],
    vehicles: [],
    grades: [],
    activeTasks: [],
    recentTasks: [],
    selectedCableCar: null,
    selectedVehicle: null,
    gradeFilter: 'all',
    gradeModalTarget: null,
    gradeModalType: null,
    stateModalTarget: null,
    prevCableCars: [],
    prevVehicles: [],
    prevActiveTasks: [],
    prevRecentTasks: [],
    prevStats: {},
    initialized: false
};

const GRADE_MAP = {
    1: { name: '二级配', color: '#00d4ff' },
    2: { name: '三级配', color: '#00ff88' },
    3: { name: '四级配', color: '#ff6b6b' },
    4: { name: '三级配PVA纤维', color: '#ffd93d' },
    5: { name: '三级富浆', color: '#c084fc' }
};

// 统一状态定义（6种状态）
const STATE_CONFIG = {
    // 手动设置的3种状态
    normal: { label: '正常运行', color: '#00ff88', type: 'manual' },
    rest: { label: '休息中', color: '#c084fc', type: 'manual' },
    other: { label: '打杂中', color: '#888888', type: 'manual' },
    // 自动检测的4种状态
    loading: { label: '990平台接料', color: '#ffd93d', type: 'auto' },
    delivering: { label: '送料途中', color: '#00d4ff', type: 'auto' },
    unloading: { label: '基坑卸料', color: '#ff6b6b', type: 'auto' },
    returning: { label: '返程途中', color: '#00ff88', type: 'auto' }
};

// 兼容旧代码的映射
const DIRECTION_LABELS = { returning: '返程', going: '送料', stopped: '停止', idle: '待命', assigned: '已调度' };
const STATE_LABELS = {
    loading: '990平台接料',
    delivering: '送料途中',
    unloading: '基坑卸料',
    returning: '返程途中',
    normal: '正常运行',
    rest: '休息中',
    other: '打杂中'
};
const STATE_COLORS = {
    loading: '#ffd93d',
    delivering: '#00d4ff',
    unloading: '#ff6b6b',
    returning: '#00ff88',
    normal: '#00ff88',
    rest: '#c084fc',
    other: '#888888'
};

function init() {
    updateClock();
    setInterval(updateClock, 1000);

    // Hide loading screen after initial render
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
        }
    }, 1800);

    fetchData();
    setInterval(fetchData, 3000);
}

function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) + ' ' + now.toLocaleTimeString('zh-CN', { hour12: false });
}

async function fetchData() {
    try {
        const resp = await fetch('/api/status');
        const data = await resp.json();
        // 使用深拷贝保存前一个状态，避免引用问题
        appState.prevCableCars = JSON.parse(JSON.stringify(appState.cableCars));
        appState.prevVehicles = JSON.parse(JSON.stringify(appState.vehicles));
        appState.prevActiveTasks = JSON.parse(JSON.stringify(appState.activeTasks));
        appState.prevRecentTasks = JSON.parse(JSON.stringify(appState.recentTasks));
        appState.cableCars = data.cable_cars || [];
        appState.vehicles = data.vehicles || [];
        appState.grades = data.grades || [];
        appState.activeTasks = data.active_tasks || [];
        appState.recentTasks = data.recent_tasks || [];
        smartRender();
        document.getElementById('sync-status').innerHTML = '<span class="sync-dot"></span>智能匹配中';
        document.getElementById('sync-status').className = 'sync-status online';
    } catch (e) {
        document.getElementById('sync-status').innerHTML = '<span class="sync-dot err"></span>同步异常';
        document.getElementById('sync-status').className = 'sync-status offline';
    }
}

function smartRender() {
    updateStats();
    updateCableCars();
    updateVehicles();
    updateMatchCenter();
    updateTasks();
    if (!appState.initialized) {
        renderGradeFilter();
        appState.initialized = true;
    }
}

function updateStats() {
    const returning = appState.cableCars.filter(c => c.direction === 'returning' || c.state === 'returning').length;
    const going = appState.vehicles.filter(v => v.direction === 'going').length;
    const active = appState.activeTasks.length;
    const completed = appState.recentTasks.filter(t => t.status === 'completed').length;

    setVal('stat-returning', returning, 'trend-returning', 'monitor');
    setVal('stat-going', going, 'trend-going', 'monitor');
    setVal('stat-active', active, 'trend-active', 'monitor');
    setVal('stat-completed', completed, 'trend-completed', 'monitor');
}

function setVal(id, val, trendId, type = 'stat') {
    const el = document.getElementById(id);
    if (!el) return;
    const old = parseInt(el.textContent) || 0;
    if (old !== val) {
        el.textContent = val;
        el.classList.add('value-flash');
        el.classList.add('rolling');
        setTimeout(() => {
            el.classList.remove('value-flash');
            el.classList.remove('rolling');
        }, 600);

        // Update trend indicator
        if (trendId) {
            const trendEl = document.getElementById(trendId);
            if (trendEl) {
                const trendClass = type === 'monitor' ? 'monitor-trend' : 'stat-trend';
                if (val > old) {
                    trendEl.textContent = '▲';
                    trendEl.className = `${trendClass} up`;
                } else if (val < old) {
                    trendEl.textContent = '▼';
                    trendEl.className = `${trendClass} down`;
                } else {
                    trendEl.className = trendClass;
                }
                // Clear trend after 3 seconds
                setTimeout(() => {
                    if (trendEl) trendEl.className = trendClass;
                }, 3000);
            }
        }
    }
}

function carKey(c) { return 'cc-' + c.id; }

function updateCableCars() {
    const container = document.getElementById('cable-car-list');
    const prevMap = {};
    (appState.prevCableCars || []).forEach(c => prevMap[c.id] = c);

    appState.cableCars.forEach(car => {
        const key = carKey(car);
        let card = document.getElementById(key);
        const prev = prevMap[car.id];
        
        // 计算最终显示的状态（6种状态之一）
        // 优先级：manual_state > auto_state
        const manualState = car.manual_state;
        const autoState = car.state || car.direction;
        
        let displayState, displayLabel, displayColor, stateClass;
        
        if (manualState && manualState !== 'normal' && STATE_CONFIG[manualState]) {
            // 手动状态优先（休息中/打杂中）
            displayState = manualState;
            displayLabel = STATE_CONFIG[manualState].label;
            displayColor = STATE_CONFIG[manualState].color;
            stateClass = manualState;
        } else if (autoState && STATE_CONFIG[autoState]) {
            // 自动检测状态（990平台接料/送料途中/基坑卸料/返程途中）
            displayState = autoState;
            displayLabel = STATE_CONFIG[autoState].label;
            displayColor = STATE_CONFIG[autoState].color;
            stateClass = autoState;
        } else {
            // 兜底：返程途中
            displayState = 'returning';
            displayLabel = STATE_CONFIG.returning.label;
            displayColor = STATE_CONFIG.returning.color;
            stateClass = 'returning';
        }
        
        const isAssigned = car.status === 'assigned';
        const isSelected = appState.selectedCableCar === car.id;
        const grade = GRADE_MAP[car.grade_id];

        const needRebuild = !card || !prev ||
            prev.state !== car.state || prev.status !== car.status ||
            prev.grade_id !== car.grade_id || prev.xspeed !== car.xspeed ||
            prev.manual_state !== car.manual_state;

        if (needRebuild) {
            if (!card) {
                card = document.createElement('div');
                card.id = key;
                container.appendChild(card);
            }
            card.className = `cable-car-card ${stateClass} ${isAssigned ? 'assigned' : ''} ${isSelected ? 'selected' : ''}`;
            card.onclick = () => selectCableCar(car.id);
            
            // 处理名称中的特殊字符
            const safeName = car.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
            const safeManualState = (car.manual_state || 'normal').replace(/'/g, "\\'");
            
            // 统一的状态指示器（右上角和底部显示一致）
            const stateIndicator = `<span class="cc-state-indicator ${stateClass}" style="background:${displayColor}18;color:${displayColor};border:1px solid ${displayColor}44">${displayLabel}</span>`;
            
            card.innerHTML = `
                <div class="card-glow-border"></div>
                <div class="cc-top">
                    <div class="cc-name-row"><span class="cc-id-badge">${car.id}</span><span class="cc-name">${car.name}</span></div>
                    <span class="cc-direction ${stateClass}" style="background:${displayColor}18;color:${displayColor};border:1px solid ${displayColor}44">${displayLabel}</span>
                </div>
                <div class="cc-info">
                    <div class="cc-info-item"><span class="label">位置区域</span><span class="value" data-field="loc">${car.location || '-'}</span></div>
                    <div class="cc-info-item"><span class="label">X坐标</span><span class="value" data-field="lat">${car.latitude?.toFixed(1) || '-'}</span></div>
                    <div class="cc-info-item"><span class="label">Y坐标</span><span class="value" data-field="lon">${car.longitude?.toFixed(1) || '-'}</span></div>
                    <div class="cc-info-item"><span class="label">X速度</span><span class="value ${car.xspeed < 0 ? 'neg' : ''}" data-field="xs">${car.xspeed?.toFixed(2) || '0.00'}</span></div>
                </div>
                <div class="cc-grade">
                    <span class="cc-grade-label">级配:</span>
                    <span class="cc-grade-badge ${grade ? '' : 'no-grade'}" style="${grade ? `background:${grade.color}18;color:${grade.color};border:1px solid ${grade.color}44` : ''}" onclick="event.stopPropagation(); openGradeModal('cable_car', ${car.id}, '${safeName}', ${car.grade_id || 0})">${grade ? grade.name : '点击设置'}</span>
                    <div style="flex:1"></div>
                    ${stateIndicator}
                    <span class="cc-grade-badge" style="background:rgba(100,100,100,0.1);color:#888;border:1px solid rgba(100,100,100,0.3);margin-left:4px;" onclick="event.stopPropagation(); openStateModal(${car.id}, '${safeName}', '${safeManualState}')">设置状态</span>
                </div>
            `;
        } else {
            // 只更新动态字段
            const locEl = card.querySelector('[data-field="loc"]');
            if (locEl) locEl.textContent = car.location || '-';
            card.querySelector('[data-field="lat"]').textContent = car.latitude?.toFixed(1) || '-';
            card.querySelector('[data-field="lon"]').textContent = car.longitude?.toFixed(1) || '-';
            const xsEl = card.querySelector('[data-field="xs"]');
            xsEl.textContent = car.xspeed?.toFixed(2) || '0.00';
            xsEl.className = `value ${car.xspeed < 0 ? 'neg' : ''}`;
            
            // 更新状态样式类
            const selClass = isSelected ? ' selected' : '';
            const assignedClass = isAssigned ? ' assigned' : '';
            card.className = `cable-car-card ${stateClass}${assignedClass}${selClass}`;
            
            // 更新状态标签
            const dirEl = card.querySelector('.cc-direction');
            if (dirEl) {
                dirEl.textContent = stateLabel;
                dirEl.style.background = `${stateColor}18`;
                dirEl.style.color = stateColor;
                dirEl.style.border = `1px solid ${stateColor}44`;
            }
        }
    });
}

function renderGradeFilter() {
    const container = document.getElementById('grade-filter');
    let html = '<div class="grade-btn active" onclick="setGradeFilter(\'all\')">全部</div>';
    Object.entries(GRADE_MAP).forEach(([id, grade]) => {
        html += `<div class="grade-btn" data-gf="${grade.name}" onclick="setGradeFilter('${grade.name}')"><span class="gb-dot" style="background:${grade.color}"></span>${grade.name}</div>`;
    });
    html += '<div class="grade-btn" data-gf="unassigned" onclick="setGradeFilter(\'unassigned\')">未分配</div>';
    container.innerHTML = html;
}

function setGradeFilter(f) {
    appState.gradeFilter = f;
    document.querySelectorAll('.grade-btn').forEach(b => {
        const bf = b.getAttribute('data-gf') || 'all';
        b.classList.toggle('active', bf === f || (!b.getAttribute('data-gf') && f === 'all'));
    });
    rebuildVehicles();
}

function rebuildVehicles() {
    const container = document.getElementById('vehicle-groups');
    container.innerHTML = '';

    let vehicles = [...appState.vehicles];
    if (appState.gradeFilter !== 'all') {
        if (appState.gradeFilter === 'unassigned') {
            vehicles = vehicles.filter(v => !v.grade_id || v.grade_id === 0);
        } else {
            const ge = Object.entries(GRADE_MAP).find(([, g]) => g.name === appState.gradeFilter);
            if (ge) vehicles = vehicles.filter(v => v.grade_id === parseInt(ge[0]));
        }
    }

    const groups = {};
    Object.entries(GRADE_MAP).forEach(([id, grade]) => {
        const gv = vehicles.filter(v => v.grade_id === parseInt(id));
        if (gv.length > 0) groups[id] = { grade, vehicles: gv };
    });
    const unassigned = vehicles.filter(v => !v.grade_id || v.grade_id === 0);
    if (unassigned.length > 0) groups['unassigned'] = { grade: { name: '未分配级配', color: '#5a6380' }, vehicles: unassigned };

    if (Object.keys(groups).length === 0) { container.innerHTML = '<div class="empty-hint">暂无车辆数据</div>'; return; }

    Object.entries(groups).forEach(([key, group]) => {
        const g = document.createElement('div');
        g.className = 'vehicle-group';
        let grid = '';
        group.vehicles.forEach(v => {
            const isAssigned = v.status === 'assigned';
            const isGoing = v.direction === 'going';
            const isReturning = v.direction === 'returning';
            const grade = GRADE_MAP[v.grade_id];
            const sc = isAssigned ? 'assigned' : isGoing ? 'going' : isReturning ? 'returning' : '';
            const dl = DIRECTION_LABELS[v.direction] || DIRECTION_LABELS[v.status] || '待命';
            const dc = isAssigned ? 'assigned' : isGoing ? 'going' : isReturning ? 'returning' : 'stopped';
            grid += `<div class="vehicle-card ${sc}" id="vc-${v.id}" onclick="selectVehicle(${v.id})">
                <div class="v-top"><span class="v-name">${v.name}</span><span class="v-status ${dc}">${dl}</span></div>
                <div class="v-bottom"><span class="v-grade-badge ${grade ? '' : 'no-grade'}" style="${grade ? `background:${grade.color}18;color:${grade.color};border:1px solid ${grade.color}44` : 'border:1px dashed #5a6380;color:#5a6380'}" onclick="event.stopPropagation(); openGradeModal('vehicle', ${v.id}, '${v.name}', ${v.grade_id || 0})">${grade ? grade.name : '设置级配'}</span></div>
            </div>`;
        });
        g.innerHTML = `<div class="vehicle-group-header"><div class="vehicle-group-dot" style="background:${group.grade.color}"></div><span class="vehicle-group-name">${group.grade.name}</span><span class="vehicle-group-count">${group.vehicles.length}台</span></div><div class="vehicle-grid">${grid}</div>`;
        container.appendChild(g);
    });
}

function updateVehicles() {
    const prevMap = {};
    (appState.prevVehicles || []).forEach(v => prevMap[v.id] = v);
    let needRebuild = false;
    for (const v of appState.vehicles) {
        const prev = prevMap[v.id];
        if (!prev || prev.direction !== v.direction || prev.status !== v.status || prev.grade_id !== v.grade_id) {
            needRebuild = true;
            break;
        }
    }
    if (needRebuild || !appState.initialized) {
        rebuildVehicles();
    }
}

function selectCableCar(carId) {
    appState.selectedCableCar = appState.selectedCableCar === carId ? null : carId;
    appState.cableCars.forEach(car => {
        const card = document.getElementById(carKey(car));
        if (card) card.classList.toggle('selected', appState.selectedCableCar === car.id);
    });
    updateMatchCenter();
}

function selectVehicle(vehicleId) {
    const vehicle = appState.vehicles.find(v => v.id === vehicleId);
    if (!vehicle || vehicle.status === 'assigned') return;
    appState.selectedVehicle = appState.selectedVehicle === vehicleId ? null : vehicleId;
    document.querySelectorAll('.vehicle-card').forEach(c => c.classList.remove('selected'));
    const card = document.getElementById('vc-' + vehicleId);
    if (card && appState.selectedVehicle === vehicleId) card.classList.add('selected');
    updateMatchCenter();
}

function updateMatchCenter() {
    const container = document.getElementById('match-area');
    const returningCars = appState.cableCars.filter(c => c.direction === 'returning' && c.status === 'returning');
    const goingVehicles = appState.vehicles.filter(v => v.direction === 'going' && v.status === 'going');
    const assignedTasks = appState.activeTasks.filter(t => t.status === 'assigned');
    const waitingCars = returningCars.filter(c => c.grade_id > 0);
    const ungradedCars = returningCars.filter(c => !c.grade_id || c.grade_id === 0);

    let html = '<div class="match-center-content"><div class="mc-title">智能匹配状态</div>';

    if (assignedTasks.length > 0) {
        html += '<div class="mc-section"><div class="mc-section-title"><span class="mc-dot green"></span>当前匹配中</div>';
        assignedTasks.forEach(t => {
            const grade = GRADE_MAP[t.grade_id];
            html += `<div class="mc-match-card matched">
                <div class="mc-match-row">
                    <div class="mc-entity"><span class="mc-entity-icon car-icon">${t.cable_car_id}</span><span class="mc-entity-name">${t.cable_car_name}</span></div>
                    <div class="mc-match-arrow"><div class="mc-arrow-line matched"><div class="mc-arrow-particle"></div></div><span class="mc-arrow-label" style="${grade ? `color:${grade.color}` : ''}">${grade ? grade.name : ''}</span></div>
                    <div class="mc-entity"><span class="mc-entity-icon vehicle-icon">🚛</span><span class="mc-entity-name">${t.vehicle_name}</span></div>
                </div>
                <div class="mc-match-status">车辆送料中，等待返程自动完成...</div>
            </div>`;
        });
        html += '</div>';
    }

    if (waitingCars.length > 0) {
        html += '<div class="mc-section"><div class="mc-section-title"><span class="mc-dot yellow"></span>等待匹配车辆</div>';
        waitingCars.forEach(car => {
            const grade = GRADE_MAP[car.grade_id];
            const mv = goingVehicles.filter(v => v.grade_id === car.grade_id && v.status !== 'assigned');
            html += `<div class="mc-match-card waiting">
                <div class="mc-match-row">
                    <div class="mc-entity"><span class="mc-entity-icon car-icon">${car.id}</span><span class="mc-entity-name">${car.name}</span></div>
                    <div class="mc-match-info"><span class="mc-grade-tag" style="${grade ? `background:${grade.color}18;color:${grade.color};border:1px solid ${grade.color}44` : ''}">${grade ? grade.name : ''}</span><span class="mc-wait-text">等待同级配车辆送料</span></div>
                </div>
                <div class="mc-match-sub">匹配车辆: ${mv.length > 0 ? mv.map(v => v.name).join(', ') : '暂无'}</div>
            </div>`;
        });
        html += '</div>';
    }

    if (ungradedCars.length > 0) {
        html += '<div class="mc-section"><div class="mc-section-title"><span class="mc-dot gray"></span>待设置级配</div>';
        ungradedCars.forEach(car => {
            html += `<div class="mc-match-card ungraded"><div class="mc-match-row"><div class="mc-entity"><span class="mc-entity-icon car-icon">${car.id}</span><span class="mc-entity-name">${car.name}</span></div><div class="mc-match-info"><span class="mc-wait-text">返程中，请设置级配</span></div></div></div>`;
        });
        html += '</div>';
    }

    if (assignedTasks.length === 0 && waitingCars.length === 0 && ungradedCars.length === 0) {
        html += '<div class="mc-empty"><div class="mc-empty-icon">📡</div><p>系统正在实时监测中</p><p class="mc-empty-sub">识别到缆机返程且设置级配后，将自动匹配送料车辆</p></div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

function updateTasks() {
    const ac = document.getElementById('active-task-list');
    const hc = document.getElementById('history-task-list');

    const activeSig = appState.activeTasks.map(t => t.id + ':' + t.status).join(',');
    const prevActiveSig = (appState.prevActiveTasks || []).map(t => t.id + ':' + t.status).join(',');
    if (activeSig !== prevActiveSig || !appState.initialized) {
        if (appState.activeTasks.length === 0) {
            ac.innerHTML = '<div class="empty-hint">暂无进行中的任务</div>';
        } else {
            ac.innerHTML = appState.activeTasks.map(t => `<div class="task-card active"><div class="task-grade-dot" style="background:${t.grade_color || '#5a6380'}"></div><div class="task-info"><div class="task-title">${t.cable_car_name} ← ${t.vehicle_name}</div><div class="task-meta">${t.grade_name || ''} · ${t.created_at || ''}</div></div><div class="task-actions"><button class="task-btn task-btn-complete" onclick="completeTask(${t.id})">完成</button><button class="task-btn task-btn-cancel" onclick="cancelTask(${t.id})">取消</button></div></div>`).join('');
        }
    }

    const histSig = appState.recentTasks.map(t => t.id).join(',');
    const prevHistSig = (appState.prevRecentTasks || []).map(t => t.id).join(',');
    if (histSig !== prevHistSig || !appState.initialized) {
        if (appState.recentTasks.length === 0) {
            hc.innerHTML = '<div class="empty-hint">暂无历史记录</div>';
        } else {
            hc.innerHTML = appState.recentTasks.map(t => `<div class="task-card done"><div class="task-grade-dot" style="background:${t.grade_color || '#5a6380'}"></div><div class="task-info"><div class="task-title">${t.cable_car_name} ← ${t.vehicle_name}</div><div class="task-meta">${t.grade_name || ''} · ${t.status === 'completed' ? '已完成' : '已取消'}</div></div></div>`).join('');
        }
    }
}

async function completeTask(taskId) { try { await fetch(`/api/dispatch/${taskId}/complete`, { method: 'PUT' }); fetchData(); } catch(e) { alert('操作失败'); } }
async function cancelTask(taskId) { if (!confirm('确认取消？')) return; try { await fetch(`/api/dispatch/${taskId}/cancel`, { method: 'PUT' }); fetchData(); } catch(e) { alert('操作失败'); } }

function openGradeModal(type, id, name, currentGradeId) {
    appState.gradeModalTarget = { type, id, name };
    const modal = document.getElementById('grade-modal');
    document.getElementById('grade-modal-title').textContent = `设置级配 - ${name}`;
    let html = '';
    Object.entries(GRADE_MAP).forEach(([gid, grade]) => {
        html += `<div class="grade-option ${currentGradeId === parseInt(gid) ? 'selected' : ''}" onclick="selectGrade(${gid})" style="--gc:${grade.color}"><div class="grade-option-dot" style="background:${grade.color}"></div><span class="grade-option-name">${grade.name}</span>${currentGradeId === parseInt(gid) ? '<span class="grade-option-check">✓</span>' : ''}</div>`;
    });
    html += '<div class="grade-option-clear" onclick="selectGrade(0)"><span>✕</span><span>清除级配</span></div>';
    document.getElementById('grade-modal-body').innerHTML = html;
    modal.style.display = 'flex';
}

function closeGradeModal() { document.getElementById('grade-modal').style.display = 'none'; appState.gradeModalTarget = null; }

// ===== State Modal Functions =====
function openStateModal(carId, carName, currentState) {
    appState.stateModalTarget = { carId, carName };
    const modal = document.getElementById('state-modal');
    document.getElementById('state-modal-title').textContent = `设置状态 - ${carName}`;
    
    // 只显示手动设置的3种状态
    const stateOptions = [
        { id: 'normal', name: '正常运行', color: '#00ff88', desc: '恢复自动状态检测' },
        { id: 'rest', name: '休息中', color: '#c084fc', desc: '缆机暂停工作，休息中' },
        { id: 'other', name: '打杂中', color: '#888888', desc: '缆机执行其他任务' }
    ];
    
    let html = '';
    stateOptions.forEach(opt => {
        const isSelected = currentState === opt.id;
        html += `
            <div class="state-option ${isSelected ? 'selected' : ''}" onclick="selectState('${opt.id}')" style="--sc:${opt.color}">
                <div class="state-option-dot" style="background:${opt.color};box-shadow:0 0 8px ${opt.color}"></div>
                <div class="state-option-info">
                    <span class="state-option-name">${opt.name}</span>
                    <span class="state-option-desc">${opt.desc}</span>
                </div>
                ${isSelected ? '<span class="state-option-check">✓</span>' : ''}
            </div>
        `;
    });
    
    document.getElementById('state-modal-body').innerHTML = html;
    modal.style.display = 'flex';
}

function closeStateModal() { 
    document.getElementById('state-modal').style.display = 'none'; 
    appState.stateModalTarget = null; 
}

async function selectState(stateId) {
    const target = appState.stateModalTarget;
    if (!target) {
        console.error('selectState: no target found');
        alert('错误：未找到目标缆机');
        return;
    }
    
    console.log('Setting state for car:', target.carId, 'to:', stateId);
    
    // 乐观更新：立即更新本地数据
    const carIndex = appState.cableCars.findIndex(c => c.id === target.carId);
    if (carIndex !== -1) {
        // 保存当前状态用于回滚
        const prevCars = JSON.parse(JSON.stringify(appState.cableCars));
        appState.prevCableCars = prevCars;
        
        // 立即更新本地状态
        appState.cableCars[carIndex].manual_state = stateId;
        
        // 立即重新渲染
        updateCableCars();
        closeStateModal();
        showToast('状态设置成功');
    }
    
    try {
        const resp = await fetch(`/api/cable-car/${target.carId}/state`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ manual_state: stateId })
        });
        
        if (!resp.ok) {
            // 如果服务器更新失败，回滚本地更改
            console.error('Server update failed, rolling back');
            fetchData(); // 重新获取服务器数据
            alert('服务器更新失败，已恢复原始状态');
        }
    } catch(e) {
        console.error('Exception:', e);
        // 网络错误时也回滚
        fetchData();
        alert('网络错误，已恢复原始状态');
    }
}

// 显示提示信息
function showToast(message) {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 255, 136, 0.9);
        color: #000;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 10000;
        animation: fadeInDown 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'fadeOutUp 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

async function selectGrade(gradeId) {
    const target = appState.gradeModalTarget;
    if (!target) return;
    const url = target.type === 'cable_car' ? `/api/cable-car/${target.id}/grade` : `/api/vehicle/${target.id}/grade`;
    try { await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ grade_id: gradeId }) }); closeGradeModal(); fetchData(); } catch(e) { alert('设置失败'); }
}

// ===== Heartbeat Animation =====
function updateHeartbeatEffects() {
    // Cable cars - add active-pulse to returning cars
    appState.cableCars.forEach(car => {
        const card = document.getElementById(carKey(car));
        if (!card) return;
        
        const isReturning = car.direction === 'returning';
        const hasDataFlow = Math.abs(car.xspeed || 0) > 0.01;
        
        // Active pulse for returning cars
        if (isReturning) {
            card.classList.add('active-pulse');
        } else {
            card.classList.remove('active-pulse');
        }
        
        // Data flow indicator
        let dataFlow = card.querySelector('.data-flow-indicator');
        if (hasDataFlow && isReturning) {
            if (!dataFlow) {
                dataFlow = document.createElement('div');
                dataFlow.className = 'data-flow-indicator';
                card.appendChild(dataFlow);
            }
        } else if (dataFlow) {
            dataFlow.remove();
        }
        
        // Pulse ring
        let pulseRing = card.querySelector('.pulse-ring');
        if (isReturning && !pulseRing) {
            pulseRing = document.createElement('div');
            pulseRing.className = 'pulse-ring';
            card.appendChild(pulseRing);
        } else if (!isReturning && pulseRing) {
            pulseRing.remove();
        }
    });
    
    // Vehicles - add going-pulse to going vehicles
    appState.vehicles.forEach(v => {
        const card = document.getElementById('vc-' + v.id);
        if (!card) return;
        
        const isGoing = v.direction === 'going';
        
        if (isGoing) {
            card.classList.add('going-pulse');
        } else {
            card.classList.remove('going-pulse');
        }
    });
}

// Override smartRender to include new effects
const originalSmartRender = smartRender;
smartRender = function() {
    originalSmartRender();
    updateHeartbeatEffects();
};

// Initialize on load
const originalInit = init;
init = function() {
    originalInit();
};

document.addEventListener('DOMContentLoaded', init);
