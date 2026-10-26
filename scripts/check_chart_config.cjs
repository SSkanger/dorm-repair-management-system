// Configuration regression only: this is not a browser/rendering test.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const labels = ['照明','水管','门锁','网络','本体类','电类','电梯类','道路景观类','给排水类','空调类','开水饮水类','门窗五金类','暖气类','洗浴热水类','消防设施类','其他'];
const counts = {total:2, category_order:labels,
  by_category:Object.fromEntries(labels.map(k=>[k,['空调类','其他'].includes(k)?1:0])),
  status_order:['PENDING','ACCEPTED','IN_PROGRESS','COMPLETED'],
  by_status:{PENDING:1,ACCEPTED:0,IN_PROGRESS:0,COMPLETED:1},
  status_labels:{PENDING:'待处理',ACCEPTED:'已接单',IN_PROGRESS:'维修中',COMPLETED:'已完成'}};
const feedback = {textContent:'',hidden:true};
const category = {parentElement:{style:{}}};
const charts=[];
const context={document:{getElementById(id){return ({'ticket-statistics':{textContent:JSON.stringify(counts)},'chart-feedback':feedback,'category-chart':category,'status-chart':{}})[id];}},
  Chart:function(canvas,config){charts.push(config);}};
vm.runInNewContext(fs.readFileSync('app/static/js/charts.js','utf8'),context);
assert.equal(charts.length,2);
assert.equal(charts[0].options.indexAxis,'y');
assert.equal(charts[0].options.scales.y.ticks.autoSkip,false);
assert.equal(category.parentElement.style.height,'496px');
for (const chart of charts) assert.equal(chart.options.animation,false);
assert.deepEqual(Array.from(charts[0].data.datasets[0].data),[0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1]);
assert.deepEqual(Array.from(charts[1].data.datasets[0].data),[1,0,0,1]);
assert.equal(charts[0].data.datasets[0].data.reduce((a,b)=>a+b,0),2);
assert.equal(feedback.textContent,'');
assert.equal(feedback.hidden,true);
console.log('PASS: horizontal 16-category chart, stable final frame, unchanged counts; visual rendering NOT verified by this script.');
