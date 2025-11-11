// ============================================
// A股板块热度分析系统 - 前端应用
// ============================================

let currentData = null;
let historyData = null;
let currentIndicesData = null; // 保存当前指数数据用于批量分析

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

      // 如果切换到历史趋势或近10日数据，加载历史数据
      if (targetTab === 'history' || targetTab === 'recent10') {
        if (!historyData) {
          loadHistoryData();
        } else {
          // 如果数据已加载，直接显示（确保近10日数据被渲染）
          displayHistoryData(historyData);
        }
      }
    });
  });
}

// ============================================
// 2. 从客户端获取东方财富实时数据（已禁用，使用GitHub Actions更新的本地数据）
// ============================================
// 注：以下函数已禁用，因为前端直接调用会遇到CORS限制
// 数据更新由GitHub Actions定期执行，前端只需读取daily.json
/*
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
  const url = 'https://push2.eastmoney.com/api/qt/clist/get';

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
  // 获取主要指数：中证100/沪深300/中证500/中证1000/中证2000/上证综指（已移除上证50）
  const indexConfigs = [
    { code: '000903', market: '1', name: 'CSI100' },   // 中证100
    { code: '000300', market: '1', name: 'HS300' },    // 沪深300
    { code: '000905', market: '1', name: 'CSI500' },   // 中证500
    { code: '000852', market: '1', name: 'CSI1000' },  // 中证1000
    { code: '932000', market: '1', name: 'CSI2000' },  // 中证2000
    { code: '000001', market: '1', name: 'SHCOMP' }    // 上证综指
  ];

  const url = 'https://push2.eastmoney.com/api/qt/stock/get';

  try {
    const results = await Promise.all(indexConfigs.map(async config => {
      const params = new URLSearchParams({
        secid: `${config.market}.${config.code}`,
        fields: 'f43,f44,f45,f46,f47,f48,f169,f170'
        // f43=name, f44=code, f45=current, f46=pct_chg, f47=chg
        // f48=volume, f169=成交额, f170=涨跌幅
      });

      const response = await fetch(`${url}?${params}`, {
        method: 'GET',
        mode: 'cors'
      });

      if (!response.ok) return null;
      const data = await response.json();
      return { ...data.data, indexName: config.name };
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

  // 处理指数数据 - 映射所有主要指数
  const processedIndices = {};
  indices.forEach(idx => {
    if (idx && idx.indexName) {
      processedIndices[idx.indexName] = {
        name: idx.f43 || '',
        code: idx.f44 || '',
        price: idx.f45 || 0,
        ret: (idx.f170 || 0) / 100,
        change: idx.f47 || 0,
        volume: idx.f48 || 0,
        turnover: idx.f169 || 0
      };
    }
  });

  // 兼容旧代码：保持原有的hs300/csi1000/shcomp结构
  if (!processedIndices.HS300) processedIndices.HS300 = { ret: 0 };
  if (!processedIndices.CSI1000) processedIndices.CSI1000 = { ret: 0 };
  if (!processedIndices.SHCOMP) processedIndices.SHCOMP = { ret: 0 };

  processedIndices.hs300 = processedIndices.HS300;
  processedIndices.csi1000 = processedIndices.CSI1000;
  processedIndices.shcomp = processedIndices.SHCOMP;

  // 计算市场节奏
  const broadStrength = processedIndices.HS300.ret - processedIndices.CSI1000.ret;
  const riskOn = processedIndices.CSI1000.ret > processedIndices.HS300.ret;

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
*/

// ============================================
// 3. 加载今日数据
// ============================================
async function loadTodayData() {
  try {
    // 直接加载本地数据（由GitHub Actions定期更新）
    // 注：前端直接调用东方财富API会遇到CORS跨域限制，因此使用后端更新的数据
    const res = await fetch('./data/daily.json', {cache:'no-store'});
    currentData = await res.json();

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
  if (!container) {
    console.error(`Container ${containerId} not found`);
    return;
  }

  container.innerHTML = '';

  if (!boards || boards.length === 0) {
    container.innerHTML = '<div class="card">暂无数据</div>';
    return;
  }

  boards.forEach((b, idx) => {
    // 购买推荐基于综合评分
    const stance = b.stance || 'WATCH';
    const riskBadge = stance.includes('BUY') ? 'GREEN' : (stance==='WATCH' ? 'YELLOW' : 'RED');
    const newBadge = b.is_new ? '<span class="badge" style="background: #ff9800; margin-left: 4px;">NEW</span>' : '';

    // 格式化综合评分
    const scoreText = b.score !== undefined ? b.score.toFixed(2) : 'N/A';

    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="grid">
        <div>
          <b>${idx+1}. ${b.name || '未知'}</b>
          <span class="badge ${riskBadge}" title="基于综合评分的推荐">${stance}</span>${newBadge}
        </div>
        <div>涨幅：${((b.ret || 0)*100).toFixed(2)}%</div>
        <div>综合评分：<strong>${scoreText}</strong></div>
        <div>人气：${(b.pop || 0).toFixed(2)}</div>
        <div>持续性：${b.persistence || 0}</div>
      </div>
      <div style="margin-top: 0.5rem;">
        <small style="color: #666;">分歧：${(b.dispersion ?? 0).toFixed(3)}</small> |
        <small style="color: #666;">核心个股：${
          b.core_stocks && b.core_stocks.length > 0
            ? b.core_stocks.map(s=>`${s.name}(${s.code}) ${((s.ret || 0)*100).toFixed(1)}%`).join('， ')
            : '暂无数据'
        }</small>
      </div>
    `;
    container.appendChild(div);
  });
}

function renderIndicesDashboard(indices) {
  const container = document.getElementById('indices-dashboard');
  if (!container) return;

  // 指数配置：名称、类型、特征描述（移除上证50）
  const indexConfigs = [
    {
      key: 'CSI100',
      name: '中证100',
      type: '超大盘',
      typeClass: 'type-ultra',
      characteristic: '权重、防守型，适合市场震荡或风险偏好下降阶段'
    },
    {
      key: 'HS300',
      name: '沪深300',
      type: '大盘',
      typeClass: 'type-large',
      characteristic: '稳健，适合市场中性阶段、机构配置主导'
    },
    {
      key: 'CSI500',
      name: '中证500',
      type: '中盘',
      typeClass: 'type-mid',
      characteristic: '成长/进攻型，适合牛市中期、风险偏好上升阶段'
    },
    {
      key: 'CSI1000',
      name: '中证1000',
      type: '小盘',
      typeClass: 'type-small',
      characteristic: '高Beta、投机性强，适合市场情绪高涨阶段'
    },
    {
      key: 'CSI2000',
      name: '中证2000',
      type: '微盘',
      typeClass: 'type-micro',
      characteristic: '超高波动，适合高频/题材性交易阶段，风险极高'
    }
  ];

  // 保存当前指数数据用于批量分析
  currentIndicesData = { indices, indexConfigs: [] };
  indexConfigs.forEach(config => {
    const indexData = indices[config.key];
    if (indexData) {
      currentIndicesData.indexConfigs.push({ ...config, data: indexData });
    }
  });

  // 渲染指数走势图表
  const chart = echarts.init(container);

  // 获取历史数据（如果已加载）
  let dates = [];
  let seriesData = {};

  if (historyData && historyData.indices_trend) {
    // 使用历史数据
    dates = historyData.dates || [];
    const indicesTrend = historyData.indices_trend;

    indexConfigs.forEach(config => {
      seriesData[config.key] = indicesTrend[config.key] || [];
    });
  } else {
    // 没有历史数据，只显示今日数据
    dates = [currentData?.date || '今日'];
    indexConfigs.forEach(config => {
      const indexData = indices[config.key];
      seriesData[config.key] = indexData ? [indexData.ret || 0] : [null];
    });
  }

  // 构建series数组
  const series = indexConfigs
    .filter(config => indices[config.key]) // 只显示有数据的指数
    .map(config => ({
      name: config.name,
      type: 'line',
      data: seriesData[config.key] || [],
      smooth: true,
      showSymbol: true, // 始终显示数据点
      symbol: 'circle',
      symbolSize: 6, // 数据点大小
      lineStyle: {
        width: 2.5 // 增加线条宽度
      },
      emphasis: {
        // 鼠标悬停时的效果
        symbolSize: 10,
        lineStyle: {
          width: 3.5
        }
      }
    }));

  const option = {
    title: {
      text: '主要指数走势对比',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 600 }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>';
        params.forEach(item => {
          if (item.data !== null && item.data !== undefined) {
            const value = item.data.toFixed(2);
            result += `${item.marker} ${item.seriesName}: <strong>${value}%</strong><br/>`;
          }
        });
        return result;
      }
    },
    legend: {
      data: indexConfigs
        .filter(config => indices[config.key])
        .map(config => config.name),
      bottom: 10,
      textStyle: { fontSize: 12 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        rotate: dates.length > 10 ? 45 : 0,
        fontSize: 11
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: v => v.toFixed(2) + '%',
        fontSize: 11
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e0e0e0' }
      }
    },
    series: series
  };

  chart.setOption(option);

  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize();
  });

  // 渲染量价关系图
  renderVolumePriceChart(indices, indexConfigs);
}

function renderVolumePriceChart(indices, indexConfigs) {
  const container = document.getElementById('volume-price-chart');
  if (!container) return;

  // 准备数据
  const data = indexConfigs
    .filter(config => indices[config.key])
    .map(config => {
      const indexData = indices[config.key];
      return {
        name: config.name,
        ret: indexData.ret || 0, // 后端已返回百分比形式，无需转换
        turnover: indexData.turnover || 0,
        type: config.type
      };
    });

  // 如果没有成交额数据，不渲染图表
  const hasTurnoverData = data.some(d => d.turnover > 0);
  if (!hasTurnoverData) {
    container.innerHTML = '<p style="text-align: center; color: #999; padding: 50px 0;">暂无成交额数据</p>';
    return;
  }

  const chart = echarts.init(container);

  // 准备散点数据：[成交额, 涨跌幅, 指数名称]
  const scatterData = data.map(d => ({
    value: [d.turnover / 100000000, d.ret, d.name], // 成交额转换为亿元
    name: d.name,
    itemStyle: {
      color: d.ret >= 0 ? '#ef5350' : '#26a69a'
    }
  }));

  const option = {
    title: {
      text: '成交额 vs 涨跌幅',
      subtext: '气泡大小代表指数市值体量',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 600 }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const turnover = params.value[0].toFixed(0);
        const ret = params.value[1].toFixed(2);
        const name = params.value[2];
        return `<strong>${name}</strong><br/>成交额: ${turnover}亿元<br/>涨跌幅: ${ret}%`;
      }
    },
    grid: {
      left: '10%',
      right: '10%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      name: '成交额（亿元）',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { fontSize: 12, fontWeight: 500 },
      type: 'value',
      axisLabel: {
        formatter: v => v.toFixed(0),
        fontSize: 11
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e0e0e0' }
      }
    },
    yAxis: {
      name: '涨跌幅（%）',
      nameLocation: 'middle',
      nameGap: 50,
      nameTextStyle: { fontSize: 12, fontWeight: 500 },
      type: 'value',
      axisLabel: {
        formatter: v => v.toFixed(2) + '%',
        fontSize: 11
      },
      splitLine: {
        lineStyle: { type: 'dashed', color: '#e0e0e0' }
      }
    },
    series: [{
      type: 'scatter',
      data: scatterData,
      symbolSize: function(data) {
        // 根据指数名称调整气泡大小
        const name = data[2];
        const sizeMap = {
          '中证100': 80,
          '沪深300': 70,
          '中证500': 60,
          '中证1000': 50,
          '中证2000': 40,
          '上证指数': 65
        };
        return sizeMap[name] || 50;
      },
      label: {
        show: true,
        formatter: params => params.value[2],
        fontSize: 11,
        fontWeight: 500,
        position: 'inside'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 13,
          fontWeight: 600
        },
        itemStyle: {
          borderColor: '#333',
          borderWidth: 2
        }
      }
    }]
  };

  chart.setOption(option);

  // 响应式调整
  window.addEventListener('resize', () => {
    chart.resize();
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

  // 显示指数看板
  if (data.indices) {
    renderIndicesDashboard(data.indices);
  }

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

    // 重新渲染主要指数看板，使用历史数据
    if (currentData && currentData.indices) {
      renderIndicesDashboard(currentData.indices);
    }
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

  // 5. 近10日详细数据
  displayRecent10Data(history);
}

function displayRecent10Data(history) {
  const dailyRecords = history.daily_records || [];

  if (dailyRecords.length === 0) {
    document.getElementById('recent10-list').innerHTML = '<p>暂无近期数据</p>';
    return;
  }

  const container = document.getElementById('recent10-list');
  container.innerHTML = '';

  dailyRecords.forEach(dayData => {
    const daySection = document.createElement('div');
    daySection.style.marginBottom = '2rem';
    daySection.style.paddingBottom = '1.5rem';
    daySection.style.borderBottom = '2px solid #e0e0e0';

    // 日期标题
    const dateHeader = document.createElement('h3');
    dateHeader.style.marginBottom = '1rem';
    dateHeader.style.color = '#333';

    // 添加市场节奏信息
    const market = dayData.market || {};
    const advice = market.advice || 'NEUTRAL';
    const adviceText = advice === 'OFFENSE' ? '进攻' : (advice === 'DEFENSE' ? '防守' : '中性');
    const adviceColor = advice === 'OFFENSE' ? '#ef5350' : (advice === 'DEFENSE' ? '#26a69a' : '#999');

    dateHeader.innerHTML = `
      📅 ${dayData.date}
      <span style="margin-left: 12px; font-size: 0.85em; color: ${adviceColor};">
        节奏: ${adviceText}
      </span>
    `;
    daySection.appendChild(dateHeader);

    // 指数表现
    const indices = dayData.indices || {};
    const indicesDiv = document.createElement('div');
    indicesDiv.style.marginBottom = '1rem';
    indicesDiv.style.padding = '8px 12px';
    indicesDiv.style.background = '#f5f5f5';
    indicesDiv.style.borderRadius = '4px';
    indicesDiv.style.fontSize = '0.875rem';

    const hs300Ret = ((indices.hs300?.ret || 0) * 100).toFixed(2);
    const csi1000Ret = ((indices.csi1000?.ret || 0) * 100).toFixed(2);
    const shcompRet = ((indices.shcomp?.ret || 0) * 100).toFixed(2);

    indicesDiv.innerHTML = `
      指数表现:
      沪深300 <strong style="color: ${indices.hs300?.ret >= 0 ? '#ef5350' : '#26a69a'}">${hs300Ret}%</strong> |
      中证1000 <strong style="color: ${indices.csi1000?.ret >= 0 ? '#ef5350' : '#26a69a'}">${csi1000Ret}%</strong> |
      上证综指 <strong style="color: ${indices.shcomp?.ret >= 0 ? '#ef5350' : '#26a69a'}">${shcompRet}%</strong>
    `;
    daySection.appendChild(indicesDiv);

    // 行业板块
    const industryTitle = document.createElement('h4');
    industryTitle.textContent = '行业板块 Top 10';
    industryTitle.style.marginTop = '1rem';
    industryTitle.style.marginBottom = '0.5rem';
    industryTitle.style.fontSize = '1rem';
    daySection.appendChild(industryTitle);

    const industryContainer = document.createElement('div');
    industryContainer.id = `industry-${dayData.date}`;
    daySection.appendChild(industryContainer);
    renderBoardListInline(dayData.industry_boards || [], industryContainer);

    // 概念板块
    const conceptTitle = document.createElement('h4');
    conceptTitle.textContent = '概念板块 Top 10';
    conceptTitle.style.marginTop = '1rem';
    conceptTitle.style.marginBottom = '0.5rem';
    conceptTitle.style.fontSize = '1rem';
    daySection.appendChild(conceptTitle);

    const conceptContainer = document.createElement('div');
    conceptContainer.id = `concept-${dayData.date}`;
    daySection.appendChild(conceptContainer);
    renderBoardListInline(
      dayData.concept_boards || [],
      conceptContainer,
      '暂无数据（历史数据未包含概念板块）'
    );

    container.appendChild(daySection);
  });
}

function renderBoardListInline(boards, container, emptyMessage = '暂无数据') {
  container.innerHTML = '';

  if (!boards || boards.length === 0) {
    container.innerHTML = `<p style="color: #999; font-size: 0.875rem;">${emptyMessage}</p>`;
    return;
  }

  boards.forEach((b, idx) => {
    // 购买推荐基于综合评分
    const riskBadge = b.stance?.includes('BUY') ? 'GREEN' : (b.stance==='WATCH' ? 'YELLOW' : 'RED');
    const newBadge = b.is_new ? '<span class="badge" style="background: #ff9800; margin-left: 4px;">NEW</span>' : '';

    // 格式化综合评分
    const scoreText = b.score !== undefined ? b.score.toFixed(2) : 'N/A';

    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="grid">
        <div>
          <b>${idx+1}. ${b.name}</b>
          <span class="badge ${riskBadge}" title="基于综合评分的推荐">${b.stance || 'N/A'}</span>${newBadge}
        </div>
        <div>涨幅：${((b.ret || 0)*100).toFixed(2)}%</div>
        <div>综合评分：<strong>${scoreText}</strong></div>
        <div>人气：${(b.pop || 0).toFixed(2)}</div>
        <div>持续性：${b.persistence || 0}</div>
      </div>
      <div style="margin-top: 0.5rem;">
        <small style="color: #666;">分歧：${((b.dispersion ?? 0)).toFixed(3)}</small> |
        <small style="color: #666;">核心个股：${
          b.core_stocks && b.core_stocks.length > 0
            ? b.core_stocks.map(s=>`${s.name}(${s.code}) ${((s.ret || 0)*100).toFixed(1)}%`).join('， ')
            : '暂无数据'
        }</small>
      </div>
    `;
    container.appendChild(div);
  });
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
// 5. AI分析功能
// ============================================

// 模型配置信息
const MODEL_INFO = {
  // GPT-5系列（最新）
  'gpt-5': {
    name: 'gpt-5',
    displayName: 'GPT-5',
    cost: '$0.002/次 (¥0.015)',
    inputPrice: '$1.25/1M tokens',
    outputPrice: '$10.00/1M tokens',
    speed: '快速（1-2秒）',
    description: '新一代旗舰模型，推理和生成能力全面提升',
    recommended: true,
    isNew: true
  },
  'gpt-5-mini': {
    name: 'gpt-5-mini',
    displayName: 'GPT-5 mini',
    cost: '$0.0002/次 (¥0.0015)',
    inputPrice: '$0.25/1M tokens',
    outputPrice: '$1.00/1M tokens',
    speed: '很快（1-2秒）',
    description: 'GPT-5轻量版，性价比极高',
    recommended: true,
    isNew: true
  },
  'gpt-5-nano': {
    name: 'gpt-5-nano',
    displayName: 'GPT-5 nano',
    cost: '$0.00005/次 (¥0.0004)',
    inputPrice: '$0.05/1M tokens',
    outputPrice: '$0.20/1M tokens',
    speed: '极快（<1秒）',
    description: '超轻量级，适合大规模批量调用',
    recommended: false,
    isNew: true
  },

  // o3系列推理模型
  'o3-mini': {
    name: 'o3-mini',
    displayName: 'o3-mini',
    cost: '$0.001/次 (¥0.007)',
    inputPrice: '$1.10/1M tokens',
    outputPrice: '$4.40/1M tokens',
    speed: '中等（2-3秒）',
    description: '新一代推理模型，平衡推理能力和成本',
    recommended: false,
    isNew: true
  },

  // o1系列推理模型
  'o1': {
    name: 'o1',
    displayName: 'o1',
    cost: '$0.015/次 (¥0.11)',
    inputPrice: '$15.00/1M tokens',
    outputPrice: '$60.00/1M tokens',
    speed: '较慢（深度推理）',
    description: '最强推理能力，适合复杂金融分析',
    recommended: false
  },
  'o1-mini': {
    name: 'o1-mini',
    displayName: 'o1-mini',
    cost: '$0.003/次 (¥0.02)',
    inputPrice: '$3.00/1M tokens',
    outputPrice: '$12.00/1M tokens',
    speed: '中等',
    description: '快速推理，性价比高',
    recommended: false
  },

  // GPT-4o系列
  'gpt-4o': {
    name: 'gpt-4o',
    displayName: 'GPT-4o',
    cost: '$0.002/次 (¥0.015)',
    inputPrice: '$2.50/1M tokens',
    outputPrice: '$10.00/1M tokens',
    speed: '快速（1-2秒）',
    description: '多模态旗舰模型，速度与能力兼具',
    recommended: true
  },
  'gpt-4o-mini': {
    name: 'gpt-4o-mini',
    displayName: 'GPT-4o-mini',
    cost: '$0.00015/次 (¥0.001)',
    inputPrice: '$0.15/1M tokens',
    outputPrice: '$0.60/1M tokens',
    speed: '很快（1-2秒）',
    description: '日常量价分析，性价比极高',
    recommended: true
  },

  // GPT-4系列
  'gpt-4.1': {
    name: 'gpt-4.1',
    displayName: 'GPT-4.1',
    cost: '$0.002/次 (¥0.015)',
    inputPrice: '$2.00/1M tokens',
    outputPrice: '$8.00/1M tokens',
    speed: '快速（2-3秒）',
    description: 'GPT-4升级版，优化的推理和生成',
    recommended: false,
    isNew: true
  },
  'gpt-4-turbo': {
    name: 'gpt-4-turbo',
    displayName: 'GPT-4 Turbo',
    cost: '$0.01/次 (¥0.07)',
    inputPrice: '$10.00/1M tokens',
    outputPrice: '$30.00/1M tokens',
    speed: '中等（2-3秒）',
    description: '长上下文，知识更新至2024年',
    recommended: false
  },
  'gpt-4': {
    name: 'gpt-4',
    displayName: 'GPT-4',
    cost: '$0.03/次 (¥0.22)',
    inputPrice: '$30.00/1M tokens',
    outputPrice: '$60.00/1M tokens',
    speed: '较慢（3-5秒）',
    description: '标准版，能力强大但成本较高',
    recommended: false
  },

  // GPT-3.5系列
  'gpt-3.5-turbo': {
    name: 'gpt-3.5-turbo',
    displayName: 'GPT-3.5 Turbo',
    cost: '$0.00005/次 (¥0.0004)',
    inputPrice: '$0.50/1M tokens',
    outputPrice: '$1.50/1M tokens',
    speed: '极快（<1秒）',
    description: '极致性价比，适合简单分析',
    recommended: false
  }
};

// 从localStorage获取OpenAI API密钥
function getOpenAIKey() {
  return localStorage.getItem('openai_api_key');
}

// 保存OpenAI API密钥到localStorage
function saveOpenAIKey(key) {
  if (key && key.trim()) {
    localStorage.setItem('openai_api_key', key.trim());
    return true;
  }
  return false;
}

// 获取当前选择的模型
function getCurrentModel() {
  return localStorage.getItem('openai_model') || 'gpt-4o-mini';
}

// 保存模型选择
function saveModel(model) {
  if (model && MODEL_INFO[model]) {
    localStorage.setItem('openai_model', model);
    return true;
  }
  return false;
}

// 更新顶部显示的当前模型
function updateModelDisplay() {
  const model = getCurrentModel();
  const modelInfo = MODEL_INFO[model];
  const modelDisplay = document.getElementById('current-model-display');
  const apiStatusDisplay = document.getElementById('api-status-display');

  if (modelDisplay && modelInfo) {
    modelDisplay.textContent = `当前模型：${modelInfo.displayName}`;
  }

  if (apiStatusDisplay) {
    const hasKey = !!getOpenAIKey();
    apiStatusDisplay.textContent = hasKey ? '✓ 已配置' : '未配置API密钥';
    apiStatusDisplay.style.color = hasKey ? 'rgba(82, 196, 26, 0.9)' : 'rgba(255,255,255,0.9)';
  }
}

// 更新模型信息卡片
function updateModelInfoCard(model) {
  const modelInfo = MODEL_INFO[model];
  if (!modelInfo) return;

  const infoCard = document.getElementById('model-info-card');
  if (!infoCard) return;

  const recommendedBadge = modelInfo.recommended
    ? '<span style="margin-left: 8px; padding: 2px 8px; background: #e6f7ff; color: #1677ff; border-radius: 4px; font-size: 11px;">推荐</span>'
    : '';

  const newBadge = modelInfo.isNew
    ? '<span style="margin-left: 8px; padding: 2px 8px; background: #fff3e0; color: #ff9800; border-radius: 4px; font-size: 11px;">NEW</span>'
    : '';

  // 如果有详细定价信息，显示input/output价格
  const pricingDetails = modelInfo.inputPrice && modelInfo.outputPrice
    ? `<div style="font-size: 12px; color: #999; margin-top: 4px;">
         Input: ${modelInfo.inputPrice} | Output: ${modelInfo.outputPrice}
       </div>`
    : '';

  infoCard.innerHTML = `
    <div style="display: flex; align-items: center; margin-bottom: 8px;">
      <span style="font-weight: 600; color: #333;">${modelInfo.displayName}</span>
      ${recommendedBadge}
      ${newBadge}
    </div>
    <div style="color: #666;">
      <div>💰 成本：约 ${modelInfo.cost}</div>
      ${pricingDetails}
      <div>⚡ 速度：${modelInfo.speed}</div>
      <div>🎯 适用：${modelInfo.description}</div>
    </div>
  `;
}

// 初始化AI设置模态框
function initAISettings() {
  const modal = document.getElementById('ai-settings-modal');
  const openBtn = document.getElementById('ai-settings-btn');
  const cancelBtn = document.getElementById('cancel-settings');
  const saveBtn = document.getElementById('save-api-key');
  const input = document.getElementById('openai-api-key');
  const modelSelect = document.getElementById('openai-model-select');

  if (!modal || !openBtn) return;

  // 打开设置
  openBtn.addEventListener('click', () => {
    const currentKey = getOpenAIKey();
    const currentModel = getCurrentModel();

    if (currentKey) {
      input.value = currentKey;
    }
    if (modelSelect) {
      modelSelect.value = currentModel;
      updateModelInfoCard(currentModel);
    }

    modal.style.display = 'flex';
  });

  // 模型选择变化时更新信息卡片
  if (modelSelect) {
    modelSelect.addEventListener('change', (e) => {
      updateModelInfoCard(e.target.value);
    });
  }

  // 取消
  cancelBtn.addEventListener('click', () => {
    modal.style.display = 'none';
    input.value = '';
  });

  // 保存
  saveBtn.addEventListener('click', () => {
    const key = input.value.trim();
    const selectedModel = modelSelect ? modelSelect.value : 'gpt-4o-mini';

    let success = true;
    let message = '';

    // 保存API密钥
    if (key) {
      if (saveOpenAIKey(key)) {
        message += 'API密钥已保存！\n';
      } else {
        success = false;
        message += 'API密钥格式错误\n';
      }
    }

    // 保存模型选择
    if (saveModel(selectedModel)) {
      message += `模型已设置为：${MODEL_INFO[selectedModel].displayName}`;
    }

    if (success || key) {
      alert(message);
      modal.style.display = 'none';
      input.value = '';
      updateModelDisplay(); // 更新顶部显示
    } else {
      alert('请输入有效的API密钥');
    }
  });

  // 点击模态框外部关闭
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
      input.value = '';
    }
  });

  // 初始化显示
  updateModelDisplay();
}

// 使用OpenAI API分析指数
async function analyzeIndexWithAI(indexKey, indexName, indexData, characteristic) {
  const apiKey = getOpenAIKey();
  const resultDiv = document.getElementById(`ai-result-${indexKey}`);

  if (!apiKey) {
    resultDiv.innerHTML = '<strong style="color: #ff4d4f;">⚠️ 请先配置OpenAI API密钥</strong><br>点击右上角"AI分析设置"按钮进行配置。';
    resultDiv.style.display = 'block';
    resultDiv.style.background = '#fff1f0';
    resultDiv.style.borderColor = '#ffa39e';
    return;
  }

  // 显示加载状态
  resultDiv.innerHTML = '<strong>🤔 AI分析中...</strong><br>请稍候，正在为您生成投资建议。';
  resultDiv.style.display = 'block';
  resultDiv.style.background = '#e6f7ff';
  resultDiv.style.borderColor = '#91d5ff';

  try {
    const ret = indexData.ret || 0;
    const retPct = (ret * 100).toFixed(2);
    const turnover = indexData.turnover || 0;
    const turnoverBillion = (turnover / 100000000).toFixed(0);

    // 构建提示词
    const prompt = `作为一名专业的股票市场分析师，请基于以下数据对${indexName}进行量价分析并给出投资建议：

指数特征：${characteristic}
当前涨跌幅：${retPct}%
成交额：${turnoverBillion}亿元

请提供：
1. 量价关系分析（结合成交额和涨跌幅的关系）
2. 当前市场阶段判断（根据指数特征）
3. 投资建议（2-3句话，简明扼要）

请用简洁专业的语言，控制在150字以内。`;

    // 获取用户选择的模型
    const selectedModel = getCurrentModel();

    // 调用OpenAI API
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: selectedModel,
        messages: [
          {
            role: 'system',
            content: '你是一位专业的A股市场分析师，擅长量价分析和投资策略建议。请用简洁专业的中文回答。'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 500,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const analysis = data.choices[0].message.content;

    // 显示分析结果
    resultDiv.innerHTML = `<strong>📊 AI分析结果</strong><br><br>${analysis.replace(/\n/g, '<br>')}`;
    resultDiv.style.background = '#f6ffed';
    resultDiv.style.borderColor = '#b7eb8f';

  } catch (error) {
    console.error('AI分析失败:', error);
    resultDiv.innerHTML = `<strong style="color: #ff4d4f;">❌ 分析失败</strong><br>${error.message}<br><br>请检查API密钥是否正确，或稍后再试。`;
    resultDiv.style.background = '#fff1f0';
    resultDiv.style.borderColor = '#ffa39e';
  }
}

// 渲染指数走势图
function renderIndexTrendChart(indexKey, indexName) {
  const chartDom = document.getElementById(`trend-chart-${indexKey}`);
  if (!chartDom) return;

  const chart = echarts.init(chartDom);

  // 从历史数据获取近10日数据（如果有）
  let dates = [];
  let retData = [];
  let turnoverData = [];

  if (historyData && historyData.dates) {
    dates = historyData.dates.slice(-10); // 最近10天

    // 尝试从indices_trend获取数据
    const indexKeyLower = indexKey.toLowerCase();
    if (historyData.indices_trend && historyData.indices_trend[indexKeyLower]) {
      retData = historyData.indices_trend[indexKeyLower].slice(-10).map(v => (v * 100).toFixed(2));
    }
  }

  // 如果没有历史数据，使用当前数据
  if (dates.length === 0 || retData.length === 0) {
    dates = ['近10日数据加载中...'];
    retData = [0];
    turnoverData = [0];
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['涨跌幅(%)', '成交额(亿)'],
      bottom: 0,
      textStyle: { fontSize: 11 }
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        fontSize: 10,
        rotate: 30
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '涨跌幅(%)',
        position: 'left',
        axisLabel: {
          fontSize: 10,
          formatter: '{value}%'
        },
        axisLine: {
          lineStyle: {
            color: '#5470c6'
          }
        }
      },
      {
        type: 'value',
        name: '成交额(亿)',
        position: 'right',
        axisLabel: {
          fontSize: 10,
          formatter: '{value}亿'
        },
        axisLine: {
          lineStyle: {
            color: '#91cc75'
          }
        }
      }
    ],
    series: [
      {
        name: '涨跌幅(%)',
        type: 'line',
        yAxisIndex: 0,
        data: retData,
        smooth: true,
        itemStyle: {
          color: '#5470c6'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
            { offset: 1, color: 'rgba(84, 112, 198, 0.05)' }
          ])
        }
      },
      {
        name: '成交额(亿)',
        type: 'bar',
        yAxisIndex: 1,
        data: turnoverData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(145, 204, 117, 0.8)' },
            { offset: 1, color: 'rgba(145, 204, 117, 0.3)' }
          ])
        }
      }
    ]
  };

  chart.setOption(option);

  // 响应式
  window.addEventListener('resize', () => {
    chart.resize();
  });
}

// 全市场AI分析（一次性分析所有指数）
async function analyzeAllIndicesWithAI() {
  const apiKey = getOpenAIKey();

  if (!apiKey) {
    alert('请先配置OpenAI API密钥！\n\n点击页面顶部的"⚙️ API配置"按钮进行配置。');
    return;
  }

  if (!currentIndicesData || !currentIndicesData.indexConfigs || currentIndicesData.indexConfigs.length === 0) {
    alert('暂无指数数据，请刷新页面后重试。');
    return;
  }

  const btn = document.getElementById('market-analyze-btn');
  const resultDiv = document.getElementById('market-analysis-result');
  const contentDiv = document.getElementById('market-analysis-content');

  if (!btn || !resultDiv || !contentDiv) return;

  // 禁用按钮，显示加载状态
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.style.opacity = '0.6';
  btn.style.cursor = 'not-allowed';
  btn.innerHTML = '🤔 AI分析中...';

  // 显示结果区域
  resultDiv.style.display = 'block';
  contentDiv.innerHTML = '<div style="text-align: center; color: #1677ff;">⏳ AI正在分析全市场指数数据，请稍候...</div>';

  try {
    const selectedModel = getCurrentModel();
    const configs = currentIndicesData.indexConfigs;

    // 构建包含所有指数信息的prompt
    let indicesInfo = configs.map(config => {
      const ret = config.data.ret || 0;
      const retPct = (ret * 100).toFixed(2);
      const turnover = config.data.turnover || 0;
      const turnoverBillion = (turnover / 100000000).toFixed(0);

      return `${config.name}(${config.type})：
  涨跌幅：${retPct}%
  成交额：${turnoverBillion}亿
  特征：${config.characteristic}`;
    }).join('\n\n');

    const prompt = `作为专业的A股市场分析师，请基于以下各个市值体量指数的量价数据，进行全市场分析：

${indicesInfo}

请提供：

1. **市场风格判断**（2-3句话）
   - 当前是大盘主导还是小盘主导？
   - 市场情绪是风险偏好上升还是下降？

2. **风险提示**
   - 明确指出哪些指数存在风险（列出具体指数名称）
   - 说明风险原因（例如：高位滞涨、成交萎缩、跌幅过大等）

3. **机会识别**
   - 明确指出哪些指数存在机会（列出具体指数名称）
   - 说明机会理由（例如：低位放量、强势突破、量价配合等）

4. **操作建议**（2-3句话）
   - 当前阶段应该关注哪类体量的指数？
   - 具体的配置建议

请用简洁专业的语言，控制在300字以内。使用markdown格式，风险部分用🔴标记，机会部分用🟢标记。`;

    // 调用OpenAI API
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: selectedModel,
        messages: [
          {
            role: 'system',
            content: '你是一位资深的A股市场分析师，擅长从多个市值体量指数的量价数据中，识别市场风格、发现风险和机会。请用简洁专业的中文回答，重点突出风险和机会的具体指数。'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 800,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const analysis = data.choices[0].message.content;

    // 显示分析结果（markdown转HTML简单处理）
    const htmlContent = analysis
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/🔴/g, '<span style="color: #ff4d4f;">🔴</span>')
      .replace(/🟢/g, '<span style="color: #52c41a;">🟢</span>');

    contentDiv.innerHTML = `<div style="line-height: 1.8; color: #333;"><p>${htmlContent}</p></div>`;

    btn.innerHTML = '✅ 分析完成';
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.disabled = false;
      btn.style.opacity = '1';
      btn.style.cursor = 'pointer';
    }, 3000);

  } catch (error) {
    console.error('全市场分析失败:', error);
    contentDiv.innerHTML = `<div style="color: #ff4d4f;">
      <strong>❌ 分析失败</strong><br>${error.message}<br><br>
      请检查API密钥是否正确，或稍后再试。
    </div>`;

    btn.innerHTML = originalText;
    btn.disabled = false;
    btn.style.opacity = '1';
    btn.style.cursor = 'pointer';
  }
}

// 批量分析所有指数（已废弃，改为全市场分析）
async function batchAnalyzeAllIndices() {
  const apiKey = getOpenAIKey();

  if (!apiKey) {
    alert('请先配置OpenAI API密钥！\n\n点击页面顶部的"⚙️ API配置"按钮进行配置。');
    return;
  }

  if (!currentIndicesData || !currentIndicesData.indexConfigs || currentIndicesData.indexConfigs.length === 0) {
    alert('暂无指数数据，请刷新页面后重试。');
    return;
  }

  const btn = document.getElementById('batch-analyze-btn');
  if (!btn) return;

  // 禁用按钮，显示进度
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.style.opacity = '0.6';
  btn.style.cursor = 'not-allowed';

  const configs = currentIndicesData.indexConfigs;
  let completed = 0;

  try {
    // 串行执行避免API速率限制
    for (const config of configs) {
      completed++;
      btn.innerHTML = `🤔 分析中 ${completed}/${configs.length}...`;

      await analyzeIndexWithAI(config.key, config.name, config.data, config.characteristic);

      // 每次请求之间等待1秒，避免速率限制
      if (completed < configs.length) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    btn.innerHTML = '✅ 分析完成';

    // 3秒后恢复按钮
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.disabled = false;
      btn.style.opacity = '1';
      btn.style.cursor = 'pointer';
    }, 3000);

  } catch (error) {
    console.error('批量分析失败:', error);
    alert(`批量分析出错：${error.message}`);

    btn.innerHTML = originalText;
    btn.disabled = false;
    btn.style.opacity = '1';
    btn.style.cursor = 'pointer';
  }
}

// ============================================
// 6. 初始化应用
// ============================================
async function init() {
  console.log('🚀 A股板块热度分析系统 - 启动中...');

  // 初始化标签切换
  initTabs();

  // 初始化AI设置
  initAISettings();

  // 初始化全市场分析按钮
  const marketBtn = document.getElementById('market-analyze-btn');
  if (marketBtn) {
    marketBtn.addEventListener('click', analyzeAllIndicesWithAI);
    // 添加hover效果
    marketBtn.addEventListener('mouseover', function() {
      this.style.transform = 'translateY(-2px)';
      this.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.6)';
    });
    marketBtn.addEventListener('mouseout', function() {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = '0 2px 6px rgba(102, 126, 234, 0.4)';
    });
  }

  // 初始化帮助按钮
  const metricsHelpBtn = document.getElementById('metrics-help-btn');
  if (metricsHelpBtn) {
    metricsHelpBtn.addEventListener('click', function() {
      const helpDiv = document.getElementById('metrics-help');
      if (helpDiv) {
        helpDiv.style.display = helpDiv.style.display === 'none' ? 'block' : 'none';
      }
    });
  }

  const indicesHelpBtn = document.getElementById('indices-help-btn');
  if (indicesHelpBtn) {
    indicesHelpBtn.addEventListener('click', function() {
      const helpDiv = document.getElementById('indices-help');
      if (helpDiv) {
        helpDiv.style.display = helpDiv.style.display === 'none' ? 'block' : 'none';
      }
    });
  }

  // 初始化AI设置按钮hover效果
  const aiSettingsBtn = document.getElementById('ai-settings-btn');
  if (aiSettingsBtn) {
    aiSettingsBtn.addEventListener('mouseover', function() {
      this.style.transform = 'translateY(-2px)';
      this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
    });
    aiSettingsBtn.addEventListener('mouseout', function() {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
    });
  }

  // 加载今日数据
  await loadTodayData();

  // 加载历史数据（用于主要指数看板的走势图）
  await loadHistoryData();

  console.log('✅ 系统初始化完成');
}

// 页面加载完成后启动
init();
