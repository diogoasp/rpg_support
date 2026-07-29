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
