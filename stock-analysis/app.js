// ============================================
// A股板块热度分析系统 - 前端应用
// ============================================

let currentData = null;
let historyData = null;

// ============================================
// 1. 标签切换功能
// ============================================
function initTabs() {
  const tabs = document.querySelectorAll('.tab');
  const tabContents = document.querySelectorAll('.tab-content');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');

      // 移除所有激活状态
      tabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(tc => tc.classList.remove('active'));

      // 激活当前标签
      tab.classList.add('active');
      const targetContent = document.getElementById(`tab-${targetTab}`);
      if (targetContent) {
        targetContent.classList.add('active');
      }

      // 如果切换到历史趋势，加载历史数据
      if (targetTab === 'history' && !historyData) {
        loadHistoryData();
      }
    });
  });
}

// ============================================
// 2. 从客户端获取东方财富实时数据
// ============================================
async function fetchRealtimeData() {
  try {
    console.log('🔄 正在从东方财富获取实时数据...');

    // 获取行业板块和概念板块数据
    const [industryBoards, conceptBoards] = await Promise.all([
      fetchEastmoneyBoards('industry'),
      fetchEastmoneyBoards('concept')
    ]);

    if (!industryBoards && !conceptBoards) {
      throw new Error('板块数据获取失败');
    }

    // 获取指数数据
    const indicesData = await fetchEastmoneyIndices();
    if (!indicesData) {
      throw new Error('指数数据获取失败');
    }

    // 处理和计算数据
    const processedData = processData(industryBoards || [], conceptBoards || [], indicesData);

    console.log('✅ 实时数据获取成功');
    return processedData;

  } catch (error) {
    console.error('❌ 实时数据获取失败:', error);
    console.log('⚠️  回退使用本地数据');
    return null;
  }
}

async function fetchEastmoneyBoards(boardType = 'industry') {
  const url = 'http://push2.eastmoney.com/api/qt/clist/get';

  // t:2=行业板块, t:3=概念板块
  const fsType = boardType === 'industry' ? 'm:90+t:2' : 'm:90+t:3';

  const params = new URLSearchParams({
    fid: 'f3',
    po: '1',
    pz: '20',
    pn: '1',
    np: '1',
    fltt: '2',
    invt: '2',
    fs: fsType,
    fields: 'f12,f14,f2,f3,f5,f6,f104,f105,f138'
  });

  try {
    const response = await fetch(`${url}?${params}`, {
      method: 'GET',
      mode: 'cors'
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    if (data.rc !== 0 || !data.data) return null;

    return data.data.diff || [];
  } catch (error) {
    console.warn(`${boardType === 'industry' ? '行业' : '概念'}板块数据获取失败 (CORS限制):`, error.message);
    return null;
  }
}

async function fetchEastmoneyIndices() {
  // 获取三大指数：沪深300, 中证1000, 上证综指
  const codes = ['000300', '000852', '000001'];
  const url = 'http://push2.eastmoney.com/api/qt/stock/get';

  try {
    const results = await Promise.all(codes.map(async code => {
      const params = new URLSearchParams({
        secid: `1.${code}`,
        fields: 'f43,f44,f45,f46,f47,f48,f169,f170'
      });

      const response = await fetch(`${url}?${params}`, {
        method: 'GET',
        mode: 'cors'
      });

      if (!response.ok) return null;
      const data = await response.json();
      return data.data;
    }));

    return results;
  } catch (error) {
    console.warn('指数数据获取失败 (CORS限制):', error.message);
    return null;
  }
}

function processData(industryBoards, conceptBoards, indices) {
  const today = new Date().toISOString().split('T')[0];

  // 处理板块数据的通用函数
  const processBoardList = (boards, topN = 10) => {
    return boards.slice(0, topN).map(b => {
      const ret = (b.f3 || 0) / 100;
      const turnover = b.f6 || 0;
      const upCount = b.f104 || 0;

      return {
        code: b.f12,
        name: b.f14,
        ret: ret,
        pop: turnover / 100000000, // 转换为亿
        persistence: 3, // 默认值
        dispersion: 0,
        breadth: upCount > 0 ? 1.0 : 0.0,
        score: ret * 10,
        stance: ret > 0.02 ? 'BUY' : ret > 0 ? 'WATCH' : 'HOLD',
        core_stocks: [] // 需要额外请求
      };
    });
  };

  // 处理指数数据
  const [hs300, csi1000, shcomp] = indices;
  const processedIndices = {
    hs300: { ret: hs300 ? (hs300.f170 || 0) / 100 : 0 },
    csi1000: { ret: csi1000 ? (csi1000.f170 || 0) / 100 : 0 },
    shcomp: { ret: shcomp ? (shcomp.f170 || 0) / 100 : 0 }
  };

  // 计算市场节奏
  const broadStrength = processedIndices.hs300.ret - processedIndices.csi1000.ret;
  const riskOn = processedIndices.csi1000.ret > processedIndices.hs300.ret;

  return {
    date: today,
    market: {
      risk_on: riskOn,
      broad_strength: broadStrength,
      advice: riskOn ? 'OFFENSE' : 'DEFENSE'
    },
    industry_boards: processBoardList(industryBoards, 10),
    concept_boards: processBoardList(conceptBoards, 10),
    indices: processedIndices,
    disclaimer: '本页面仅为个人研究与技术演示，不构成投资建议。'
  };
}

// ============================================
// 3. 加载今日数据
// ============================================
async function loadTodayData() {
  try {
    // 优先尝试获取实时数据
    const realtimeData = await fetchRealtimeData();

    if (realtimeData) {
      currentData = realtimeData;
    } else {
      // 回退到本地数据
      const res = await fetch('./data/daily.json', {cache:'no-store'});
      currentData = await res.json();
    }

    displayTodayData(currentData);

  } catch (error) {
    console.error('数据加载失败:', error);
    const errorMsg = '<div class="card">数据加载失败，请刷新页面重试</div>';
    document.getElementById('industry-board-list').innerHTML = errorMsg;
    document.getElementById('concept-board-list').innerHTML = errorMsg;
  }
}

function renderBoardList(boards, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  boards.forEach((b, idx) => {
    const riskBadge = b.stance.includes('BUY') ? 'GREEN' : (b.stance==='WATCH' ? 'YELLOW' : 'RED');
    const newBadge = b.is_new ? '<span class="badge" style="background: #ff9800; margin-left: 4px;">NEW</span>' : '';
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="grid">
        <div><b>${idx+1}. ${b.name}</b> <span class="badge ${riskBadge}">${b.stance}</span>${newBadge}</div>
        <div>涨幅：${(b.ret*100).toFixed(2)}%</div>
        <div>人气：${b.pop.toFixed(2)}</div>
        <div>持续性：${b.persistence}</div>
        <div>分歧：${(b.dispersion ?? 0).toFixed(3)}</div>
      </div>
      <div>核心个股：${
        b.core_stocks && b.core_stocks.length > 0
          ? b.core_stocks.map(s=>`${s.name}(${s.code}) ${(s.ret*100).toFixed(1)}%`).join('， ')
          : '暂无数据'
      }</div>
    `;
    container.appendChild(div);
  });
}

function displayTodayData(data) {
  // 更新日期
  document.getElementById('date').textContent = data.date;

  // 显示行业板块和概念板块列表
  if (data.industry_boards && data.concept_boards) {
    // 新格式：分别显示行业板块和概念板块
    renderBoardList(data.industry_boards, 'industry-board-list');
    renderBoardList(data.concept_boards, 'concept-board-list');
  } else if (data.boards) {
    // 旧格式兼容：显示在行业板块位置
    renderBoardList(data.boards, 'industry-board-list');
    document.getElementById('concept-board-list').innerHTML = '<p>暂无概念板块数据</p>';
  }

  // 显示宽基强弱图
  const chart = echarts.init(document.getElementById('broad'));
  chart.setOption({
    title: { text: '宽基指数涨跌幅对比', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: {type:'category', data: ['沪深300','中证1000','上证综指']},
    yAxis: {type:'value', axisLabel:{formatter: v => (v*100).toFixed(2)+'%'}},
    series: [{
      type:'bar',
      data:[
        data.indices.hs300.ret,
        data.indices.csi1000.ret,
        data.indices.shcomp.ret
      ],
      itemStyle: {
        color: function(params) {
          return params.data >= 0 ? '#ef5350' : '#26a69a';
        }
      }
    }]
  });

  // 显示免责声明
  document.getElementById('disclaimer').textContent = data.disclaimer || '本页面仅为个人研究与技术演示，不构成投资建议。';
}

// ============================================
// 4. 加载历史数据
// ============================================
async function loadHistoryData() {
  try {
    const res = await fetch('./data/history.json', {cache:'no-store'});
    historyData = await res.json();
    displayHistoryData(historyData);
  } catch (error) {
    console.error('历史数据加载失败:', error);
    document.getElementById('indices-trend').innerHTML = '<p>历史数据加载失败</p>';
  }
}

function displayHistoryData(history) {
  // 1. 指数7日走势
  displayIndicesTrend(history);

  // 2. 市场节奏变化
  displayMarketTrend(history);

  // 3. 热门板块（连续上榜）
  displayHotBoards(history);

  // 4. 板块轮动热力图
  displayBoardRotation(history);
}

function displayIndicesTrend(history) {
  // 兼容 indices_history 和 indices_trend 字段名
  const indicesTrend = history.indices_history || history.indices_trend;

  if (!indicesTrend) {
    document.getElementById('indices-trend').innerHTML = '<p>暂无指数历史数据</p>';
    return;
  }

  const chart = echarts.init(document.getElementById('indices-trend'));
  const dates = history.dates || [];

  chart.setOption({
    title: { text: '指数走势对比', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>';
        params.forEach(item => {
          const value = (item.data * 100).toFixed(2);
          result += `${item.marker} ${item.seriesName}: ${value}%<br/>`;
        });
        return result;
      }
    },
    legend: { data: ['沪深300', '中证1000', '上证综指'], bottom: 0 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', axisLabel: { formatter: v => (v*100).toFixed(1)+'%' } },
    series: [
      { name: '沪深300', type: 'line', data: indicesTrend.hs300 || [] },
      { name: '中证1000', type: 'line', data: indicesTrend.csi1000 || [] },
      { name: '上证综指', type: 'line', data: indicesTrend.shcomp || [] }
    ]
  });
}

function displayMarketTrend(history) {
  const chart = echarts.init(document.getElementById('market-trend'));
  const dates = history.market_trend.map(m => m.date);
  const adviceData = history.market_trend.map(m => m.advice === 'OFFENSE' ? 1 : -1);

  chart.setOption({
    title: { text: '市场节奏（进攻/防守）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const date = params[0].axisValue;
        const val = params[0].data;
        return `${date}<br/>${val > 0 ? '进攻' : '防守'}`;
      }
    },
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: v => v > 0 ? '进攻' : v < 0 ? '防守' : ''
      }
    },
    series: [{
      type: 'bar',
      data: adviceData,
      itemStyle: {
        color: function(params) {
          return params.data > 0 ? '#ef5350' : '#26a69a';
        }
      }
    }]
  });
}

function displayHotBoards(history) {
  if (!history.hot_boards || history.hot_boards.length === 0) {
    document.getElementById('hot-boards').innerHTML = '<p>暂无热门板块数据</p>';
    return;
  }

  const container = document.getElementById('hot-boards');
  container.innerHTML = '';

  history.hot_boards.slice(0, 10).forEach((board, idx) => {
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div><b>${idx+1}. ${board.name}</b></div>
      <div>连续上榜：${board.days_on_list || board.count || 0} 天</div>
      <div>平均涨幅：${((board.avg_ret || 0) * 100).toFixed(2)}%</div>
    `;
    container.appendChild(div);
  });
}

function displayBoardRotation(history) {
  if (!history.board_rotation) {
    document.getElementById('board-rotation').innerHTML = '<p>暂无板块轮动数据</p>';
    return;
  }

  const chart = echarts.init(document.getElementById('board-rotation'));
  const rotation = history.board_rotation;

  // 如果数据已经是处理好的格式（有 dates, boards, data 字段）
  if (rotation.dates && rotation.boards && rotation.data) {
    chart.setOption({
      title: { text: '板块轮动热力图', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { position: 'top' },
      grid: { height: '70%', top: '10%' },
      xAxis: { type: 'category', data: rotation.dates },
      yAxis: { type: 'category', data: rotation.boards },
      visualMap: {
        min: -5,
        max: 5,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: {
          color: ['#26a69a', '#ffffff', '#ef5350']
        }
      },
      series: [{
        type: 'heatmap',
        data: rotation.data,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    });
    return;
  }

  // 如果数据是对象格式（需要转换）
  const dates = Object.keys(rotation).sort();
  const allBoards = new Set();
  dates.forEach(date => {
    rotation[date].forEach(board => allBoards.add(board));
  });
  const boards = Array.from(allBoards);

  // 转换为热力图数据格式 [dateIndex, boardIndex, ranking]
  const heatmapData = [];
  dates.forEach((date, dateIdx) => {
    rotation[date].forEach((board, rank) => {
      const boardIdx = boards.indexOf(board);
      if (boardIdx >= 0) {
        // 排名越靠前，值越大（10 - rank）
        heatmapData.push([dateIdx, boardIdx, 10 - rank]);
      }
    });
  });

  chart.setOption({
    title: { text: '板块轮动热力图（排名）', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      position: 'top',
      formatter: function(params) {
        const date = dates[params.data[0]];
        const board = boards[params.data[1]];
        const rank = 10 - params.data[2] + 1;
        return `${date}<br/>${board}<br/>排名: ${rank}`;
      }
    },
    grid: { height: '60%', top: '15%' },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 45 } },
    yAxis: { type: 'category', data: boards },
    visualMap: {
      min: 0,
      max: 10,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#eeeeee', '#ef5350']
      }
    },
    series: [{
      type: 'heatmap',
      data: heatmapData,
      label: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  });
}

// ============================================
// 5. 初始化应用
// ============================================
async function init() {
  console.log('🚀 A股板块热度分析系统 - 启动中...');

  // 初始化标签切换
  initTabs();

  // 加载今日数据
  await loadTodayData();

  console.log('✅ 系统初始化完成');
}

// 页面加载完成后启动
init();
