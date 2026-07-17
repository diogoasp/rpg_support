document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.detail.target.id === "modal-content") {
    bootstrap.Modal.getOrCreateInstance(document.querySelector("#quickModal")).show();
  }
});
