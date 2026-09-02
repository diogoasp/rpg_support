document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail.target.id === "modal-content") {
    const modalElement = document.querySelector("#quickModal");
    modalElement?.classList.toggle("op-mobile-sheet-modal", Boolean(event.detail.target.querySelector(".op-mobile-action-form")));
    bootstrap.Modal.getOrCreateInstance(modalElement).show();
  }
  initializeTechniqueForms(event.detail.target);
});

document.body.addEventListener("modal:close", () => {
  const modalElement = document.querySelector("#quickModal");
  const modal = bootstrap.Modal.getInstance(modalElement);
  if (modal) {
    modal.hide();
  }
});

document.body.addEventListener("htmx:beforeRequest", (event) => {
  const button = event.detail.elt;
  if (!button?.classList?.contains("op-use-button")) return;
  button.disabled = true;
  button.dataset.originalText = button.textContent;
  button.textContent = "Usando";
});

document.body.addEventListener("htmx:afterSettle", () => {
  const toast = document.querySelector("#op-play-toast:not(:empty)");
  if (!toast) return;
  window.clearTimeout(window.opPlayToastTimer);
  window.opPlayToastTimer = window.setTimeout(() => {
    toast.innerHTML = "";
    toast.classList.remove("is-error");
  }, 6000);
});

document.querySelector("#quickModal")?.addEventListener("hidden.bs.modal", () => {
  const modalContent = document.querySelector("#modal-content");
  if (modalContent) {
    modalContent.innerHTML = "";
  }
  document.querySelector("#quickModal")?.classList.remove("op-mobile-sheet-modal");
});

function initializeTechniqueForms(root = document) {
  root.querySelectorAll?.("[data-technique-form], [data-entry]").forEach((container) => {
    const select = container.querySelector("[data-technique-usage-mode]");
    if (!select || select.dataset.usageReady) return;
    select.dataset.usageReady = "true";
    const sync = () => {
      const mode = select.value;
      container.querySelectorAll("[data-continuous-fields]").forEach((element) => { element.hidden = mode !== "continuous"; });
      container.querySelectorAll("[data-graded-fields]").forEach((element) => { element.hidden = mode !== "graded"; });
      container.querySelectorAll(".op-technique-cost-field, [data-technique-cost]").forEach((element) => { element.hidden = mode === "graded"; });
    };
    select.addEventListener("change", sync);
    sync();
  });
}

initializeTechniqueForms();

document.body.addEventListener("click", (event) => {
  if (event.target.closest("[data-open-reference-sheet]")) {
    document.body.classList.add("op-reference-open");
    document.querySelector("#player-reference-sheet")?.scrollIntoView({ block: "start" });
  }
  if (event.target.closest("[data-close-reference-sheet]")) {
    document.body.classList.remove("op-reference-open");
    document.querySelector(".op-mobile-play-shell")?.scrollIntoView({ block: "start" });
  }
});

document.querySelector("[data-map-fullscreen]")?.addEventListener("click", () => {
  const viewer = document.querySelector("[data-map-viewer]");
  if (!viewer) return;
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else {
    viewer.requestFullscreen();
  }
});
