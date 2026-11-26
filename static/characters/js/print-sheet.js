(() => {
  const sheet = document.querySelector("[data-print-character]");
  const edit = document.querySelector("#edit-print-order");
  const reset = document.querySelector("#reset-print-order");
  const status = document.querySelector("#print-order-status");
  const storageKey = `rpg:print-order:v1:${sheet.dataset.printUser}:${sheet.dataset.printCharacter}`;
  const cards = (group) => Array.from(group.querySelectorAll("[data-print-card]"));
  const groups = Array.from(sheet.querySelectorAll("[data-card-group]"))
    .filter((group) => cards(group).length > 1);
  const defaults = new Map(groups.map((group) => [group, cards(group)]));
  let dragged = null;
  let target = null;
  let editing = false;

  document.querySelector("#print-sheet").addEventListener("click", () => window.print());
  if (!groups.length) return;

  try {
    const saved = JSON.parse(localStorage.getItem(storageKey)) || {};
    for (const group of groups) {
      const order = saved[group.dataset.cardGroup];
      if (!Array.isArray(order)) continue;
      const remaining = new Map(cards(group).map((card) => [card.dataset.printCard, card]));
      for (const key of order) {
        const card = remaining.get(key);
        if (!card) continue;
        group.append(card);
        remaining.delete(key);
      }
      for (const card of remaining.values()) group.append(card);
    }
  } catch {
    // The default order also works with storage disabled or unavailable.
  }

  function save() {
    const order = Object.fromEntries(groups.map((group) => [
      group.dataset.cardGroup, cards(group).map((card) => card.dataset.printCard),
    ]));
    try {
      localStorage.setItem(storageKey, JSON.stringify(order));
      return true;
    } catch {
      return false;
    }
  }

  function updateControls(group) {
    const ordered = cards(group);
    ordered.forEach((card, index) => {
      card.draggable = editing;
      card.querySelector(".card-order-controls").hidden = !editing;
      card.querySelector("[data-move='earlier']").disabled = index === 0;
      card.querySelector("[data-move='later']").disabled = index === ordered.length - 1;
    });
  }

  function move(card, destination) {
    const group = card.parentElement;
    const ordered = cards(group);
    if (ordered.indexOf(card) < ordered.indexOf(destination)) destination.after(card);
    else destination.before(card);
    updateControls(group);
    const title = card.querySelector("h3").textContent.trim();
    status.textContent = `${title} movido. ${save() ? "Ordem salva neste navegador." : "Ordem disponível nesta sessão."}`;
  }

  function markTarget(card) {
    target?.classList.remove("drop-target");
    target = card;
    target?.classList.add("drop-target");
  }

  for (const group of groups) {
    for (const card of cards(group)) {
      const title = card.querySelector("h3").textContent.trim();
      const controls = document.createElement("div");
      controls.className = "no-print card-order-controls";
      controls.hidden = true;
      for (const [direction, label] of [["earlier", "Antecipar"], ["later", "Adiar"]]) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.dataset.move = direction;
        button.setAttribute("aria-label", `${label} ${title}`);
        button.addEventListener("click", () => {
          const neighbor = direction === "earlier" ? card.previousElementSibling : card.nextElementSibling;
          if (!neighbor?.hasAttribute("data-print-card")) return;
          move(card, neighbor);
          const focus = button.disabled ? controls.querySelector("button:not(:disabled)") : button;
          focus?.focus();
        });
        controls.append(button);
      }
      card.append(controls);
    }

    group.addEventListener("dragstart", (event) => {
      if (!editing || event.target.parentElement !== group || !event.target.hasAttribute("data-print-card")) return;
      dragged = event.target;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", dragged.dataset.printCard);
    });
    group.addEventListener("dragover", (event) => {
      const card = event.target.closest("[data-print-card]");
      if (!dragged || dragged.parentElement !== group || !card || card === dragged) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      markTarget(card);
    });
    group.addEventListener("drop", (event) => {
      const card = event.target.closest("[data-print-card]");
      if (!dragged || dragged.parentElement !== group || !card || card === dragged) return;
      event.preventDefault();
      move(dragged, card);
      markTarget(null);
      dragged = null;
    });
    group.addEventListener("dragend", () => {
      markTarget(null);
      dragged = null;
    });
  }

  edit.hidden = false;
  edit.addEventListener("click", () => {
    editing = !editing;
    edit.setAttribute("aria-pressed", String(editing));
    edit.textContent = editing ? "Concluir personalização" : "Personalizar ordem";
    reset.hidden = !editing;
    for (const group of groups) updateControls(group);
    status.textContent = editing ? "Arraste os cards ou use Antecipar e Adiar dentro de cada seção." : "";
  });
  reset.addEventListener("click", () => {
    for (const [group, original] of defaults) {
      group.append(...original);
      updateControls(group);
    }
    status.textContent = save() ? "Ordem padrão restaurada." : "Ordem padrão restaurada nesta sessão.";
  });
})();
