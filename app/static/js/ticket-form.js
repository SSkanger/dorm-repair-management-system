"use strict";
(() => {
  const category = document.getElementById("category");
  const container = document.getElementById("category-detail-field");
  const input = document.getElementById("category_detail");
  if (!category || !container || !input) return;
  const update = (focus) => {
    const other = category.value === "其他";
    container.hidden = !other;
    input.disabled = !other;
    input.required = other;
    category.setAttribute("aria-expanded", String(other));
    if (other && focus) input.focus();
  };
  category.setAttribute("aria-controls", "category-detail-field");
  category.addEventListener("change", () => update(true));
  update(false);
})();
