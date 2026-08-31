document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail.target.id === "modal-content") {
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#quickModal")).show();
  }
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
