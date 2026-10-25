"use strict";
(() => {
  document.body.classList.add("has-js");
  const sidebar = document.getElementById("app-sidebar");
  const toggle = document.getElementById("nav-toggle");
  const overlay = document.querySelector(".sidebar-overlay");
  if (!sidebar || !toggle || !overlay) return;
  const mobile = window.matchMedia("(max-width: 991px)");
  const setOpen = (open, restoreFocus = false) => {
    document.body.classList.toggle("nav-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "收起导航" : "展开导航");
    overlay.hidden = !open;
    sidebar.inert = mobile.matches && !open;
    if (open) sidebar.querySelector("a")?.focus();
    else if (restoreFocus) toggle.focus();
  };
  toggle.addEventListener("click", () => setOpen(!document.body.classList.contains("nav-open")));
  overlay.addEventListener("click", () => setOpen(false, true));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && document.body.classList.contains("nav-open")) setOpen(false, true);
    if (event.key === "Tab" && mobile.matches && document.body.classList.contains("nav-open")) {
      const links = [...sidebar.querySelectorAll("a[href]")];
      if (event.shiftKey && document.activeElement === links[0]) {event.preventDefault(); links.at(-1).focus();}
      else if (!event.shiftKey && document.activeElement === links.at(-1)) {event.preventDefault(); links[0].focus();}
    }
  });
  sidebar.addEventListener("click", event => {if (event.target.closest("a") && mobile.matches) setOpen(false);});
  mobile.addEventListener("change", () => setOpen(false));
  setOpen(false);
})();
