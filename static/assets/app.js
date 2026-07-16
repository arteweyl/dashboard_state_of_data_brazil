const tabs = [...document.querySelectorAll('[role="tab"]')];
const panels = [...document.querySelectorAll('[role="tabpanel"]')];

function activateTab(name, updateHash = true) {
  const selected = tabs.find((tab) => tab.dataset.tab === name) || tabs[0];
  tabs.forEach((tab) => {
    const active = tab === selected;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  panels.forEach((panel) => {
    const active = panel.id === `panel-${selected.dataset.tab}`;
    panel.hidden = !active;
    panel.classList.toggle("is-active", active);
  });
  if (updateHash) history.replaceState(null, "", `#${selected.dataset.tab}`);
  window.dispatchEvent(new Event("resize"));
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => activateTab(tab.dataset.tab));
  tab.addEventListener("keydown", (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const offset = event.key === 'ArrowRight' ? 1 : -1;
    const next = tabs[(index + offset + tabs.length) % tabs.length];
    activateTab(next.dataset.tab);
    next.focus();
  });
});

activateTab(location.hash.slice(1), false);
