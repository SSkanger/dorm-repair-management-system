"use strict";
(() => {
  const source = document.getElementById("ticket-statistics");
  const feedback = document.getElementById("chart-feedback");
  if (!source) return;
  const counts = JSON.parse(source.textContent);
  if (!counts.total) {
    feedback.textContent = "暂无匹配数据，图表留空；下方保留完整零计数。";
    return;
  }
  if (typeof Chart === "undefined") {
    feedback.textContent = "图表暂时无法加载，请使用下方数字表核对统计。";
    return;
  }
  const colors = ["#2563eb", "#0891b2", "#7c3aed", "#059669", "#d97706"];
  const options = {
    responsive: true, maintainAspectRatio: false,
    plugins: {legend: {position: "bottom"}},
  };
  try {
    new Chart(document.getElementById("category-chart"), {
      type: "bar",
      data: {
        labels: counts.category_order,
        datasets: [{label: "工单数量", data: counts.category_order.map(k => counts.by_category[k]), backgroundColor: colors}],
      },
      options: {...options, plugins: {legend: {display: false}}, scales: {y: {beginAtZero: true, ticks: {precision: 0}}}},
    });
    new Chart(document.getElementById("status-chart"), {
      type: "doughnut",
      data: {
        labels: counts.status_order.map(k => counts.status_labels[k]),
        datasets: [{label: "工单数量", data: counts.status_order.map(k => counts.by_status[k]), backgroundColor: colors.slice(0, 4)}],
      },
      options,
    });
    feedback.textContent = "图表与下方数字表使用相同的实时查询结果。";
  } catch (_error) {
    feedback.textContent = "图表暂时无法绘制，请使用下方数字表核对统计。";
  }
})();
