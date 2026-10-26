"use strict";
(() => {
  const source = document.getElementById("ticket-statistics");
  const feedback = document.getElementById("chart-feedback");
  if (!source) return;
  const counts = JSON.parse(source.textContent);
  if (!counts.total) {
    return;
  }
  if (typeof Chart === "undefined") {
    feedback.hidden = false;
    feedback.textContent = "图表加载失败，请查看下方数据。";
    return;
  }
  const options = {
    responsive: true, maintainAspectRatio: false,
    // Render final geometry even in a background tab or reduced-motion mode.
    animation: false,
    plugins: {legend: {position: "bottom", labels: {usePointStyle: true, boxWidth: 7, padding: 16, font: {size: 11}}}},
  };
  const countLabels = {
    id: "countLabels",
    afterDatasetsDraw(chart) {
      const ctx = chart.ctx;
      ctx.save(); ctx.fillStyle = "#64748b"; ctx.font = '11px "Segoe UI", "Microsoft YaHei", sans-serif';
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      chart.getDatasetMeta(0).data.forEach((bar, i) => ctx.fillText(String(chart.data.datasets[0].data[i]), bar.x + 8, bar.y));
      ctx.restore();
    },
  };
  const centerTotal = {
    id: "centerTotal",
    afterDraw(chart) {
      const {left, right, top, bottom} = chart.chartArea;
      const ctx = chart.ctx; const x = (left + right) / 2; const y = (top + bottom) / 2;
      ctx.save(); ctx.textAlign = "center"; ctx.fillStyle = "#172b4d";
      ctx.font = '600 26px "Segoe UI", sans-serif'; ctx.fillText(String(counts.total), x, y + 2);
      ctx.font = '11px "Microsoft YaHei", sans-serif'; ctx.fillStyle = "#64748b";
      ctx.fillText("匹配工单", x, y + 22); ctx.restore();
    },
  };
  try {
    const categoryCanvas = document.getElementById("category-chart");
    categoryCanvas.parentElement.style.height = `${Math.max(260, counts.category_order.length * 28 + 48)}px`;
    new Chart(categoryCanvas, {
      type: "bar",
      data: {
        labels: counts.category_order,
        datasets: [{label: "工单数量", data: counts.category_order.map(k => counts.by_category[k]), backgroundColor: "#2563eb", borderRadius: 5, maxBarThickness: 40}],
      },
      plugins: [countLabels],
      options: {...options, indexAxis: "y", layout: {padding: {right: 28}}, plugins: {legend: {display: false}}, scales: {y: {grid: {display: false}, ticks: {autoSkip: false, color: "#64748b", font: {size: 11}}}, x: {beginAtZero: true, grace: "15%", border: {display: false}, grid: {color: "#edf1f7"}, ticks: {precision: 0, color: "#64748b", font: {size: 10}}}}},
    });
    new Chart(document.getElementById("status-chart"), {
      type: "doughnut",
      data: {
        labels: counts.status_order.map(k => counts.status_labels[k]),
        datasets: [{label: "工单数量", data: counts.status_order.map(k => counts.by_status[k]), backgroundColor: ["#d97706", "#2563eb", "#0891b2", "#16a34a"], borderWidth: 3, borderColor: "#fff", hoverOffset: 4}],
      },
      plugins: [centerTotal],
      options: {...options, cutout: "74%"},
    });
  } catch (_error) {
    feedback.hidden = false;
    feedback.textContent = "图表加载失败，请查看下方数据。";
  }
})();
