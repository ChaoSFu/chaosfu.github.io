async function load() {
  const res = await fetch('./data/daily.json', {cache:'no-store'});
  const data = await res.json();

  document.getElementById('date').textContent = `数据日期：${data.date}`;
  const regime = data.market.advice;
  const text = regime==="OFFENSE" ? "进攻优先（小盘/成长）"
             : regime==="DEFENSE" ? "防守优先（大盘/稳健）"
             : "中性（观察）";
  document.getElementById('regime').textContent = `节奏：${text} / risk_on=${data.market.risk_on}`;

  // 板块列表
  const list = document.getElementById('board-list');
  list.innerHTML = '';
  data.boards.forEach((b, idx) => {
    const riskBadge = b.stance.includes('BUY') ? 'GREEN' : (b.stance==='WATCH' ? 'YELLOW' : 'RED');
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div class="grid">
        <div><b>${idx+1}. ${b.name}</b> <span class="badge ${riskBadge}">${b.stance}</span></div>
        <div>涨幅：${(b.ret*100).toFixed(2)}%</div>
        <div>人气：${b.pop.toFixed(2)}</div>
        <div>持续性：${b.persistence}</div>
        <div>分歧：${(b.dispersion ?? 0).toFixed(3)}</div>
      </div>
      <div>核心个股：${
        b.core_stocks.map(s=>`${s.name}(${s.code}) ${(s.ret*100).toFixed(1)}%`).join('， ')
      }</div>
    `;
    list.appendChild(div);
  });

  document.getElementById('disclaimer').textContent = data.disclaimer || '本页面仅为个人研究与技术演示，不构成投资建议。';

  // 宽基强弱图（仅显示当日点位，可扩展为历史）
  const chart = echarts.init(document.getElementById('broad'));
  chart.setOption({
    xAxis: {type:'category', data: ['HS300','CSI1000','SHCOMP']},
    yAxis: {type:'value', axisLabel:{formatter: v => (v*100).toFixed(1)+'%'}},
    series: [{type:'bar', data:[
      data.indices.hs300.ret,
      data.indices.csi1000.ret,
      data.indices.shcomp.ret
    ]}]
  });
}
load();
