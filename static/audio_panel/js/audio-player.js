const STORAGE_KEY = "grandline.audio.preferences.v1";

export class AudioPanelController {
  constructor(root = document) {
    this.root = root;
    this.channels = Object.fromEntries(["music", "ambience", "effect"].map(name => [name, this.createChannel(name)]));
    this.activeChannel = "music";
    this.fadeTimers = {};
    this.preferences = this.loadPreferences();
    this.applyPreferences();
    this.bindControls(root);
    this.bindKeyboard();
    document.body.addEventListener("htmx:afterSwap", event => this.bindControls(event.detail.target));
    window.setInterval(() => this.render(), 500);
    this.render();
  }

  createChannel(name) {
    const audio = new Audio();
    audio.preload = "none";
    audio.dataset.channel = name;
    audio.addEventListener("ended", () => this.render());
    return {audio, asset: null, baseVolume: 1};
  }

  loadPreferences() {
    try { return {...{master: 1, panelOpen: true, volumes: {music: 1, ambience: 1, effect: 1}}, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}")}; }
    catch (_) { return {master: 1, panelOpen: true, volumes: {music: 1, ambience: 1, effect: 1}}; }
  }

  savePreferences() { localStorage.setItem(STORAGE_KEY, JSON.stringify(this.preferences)); }
  effectiveVolume(channel) { return this.preferences.master * (this.preferences.volumes[channel] ?? 1) * this.channels[channel].baseVolume; }
  applyPreferences() {
    Object.entries(this.channels).forEach(([name, value]) => value.audio.volume = this.effectiveVolume(name));
    const volume = document.querySelector("#audio-master-volume");
    if (volume) volume.value = this.preferences.master * 100;
    document.querySelector("#audio-panel")?.classList.toggle("collapsed", !this.preferences.panelOpen);
  }

  bindControls(container) {
    container.querySelectorAll(".audio-play:not([data-audio-bound])").forEach(button => {
      button.dataset.audioBound = "true"; button.addEventListener("click", () => this.play(button.dataset));
    });
    container.querySelectorAll(".audio-pause:not([data-audio-bound])").forEach(button => {
      button.dataset.audioBound = "true"; button.addEventListener("click", () => this.channels[button.dataset.audioChannel].audio.pause());
    });
    container.querySelectorAll(".audio-stop:not([data-audio-bound])").forEach(button => {
      button.dataset.audioBound = "true"; button.addEventListener("click", () => this.stop(button.dataset.audioChannel));
    });
    container.querySelectorAll("[data-audio-action]:not([data-audio-bound])").forEach(button => {
      button.dataset.audioBound = "true"; button.addEventListener("click", () => this.action(button.dataset));
    });
    const master = container.querySelector("#audio-master-volume:not([data-audio-bound])");
    if (master) { master.dataset.audioBound = "true"; master.addEventListener("input", () => { this.preferences.master = master.value / 100; this.applyPreferences(); this.savePreferences(); }); }
    const progress = container.querySelector("#audio-progress:not([data-audio-bound])");
    if (progress) { progress.dataset.audioBound = "true"; progress.addEventListener("input", () => { const audio = this.channels[this.activeChannel].audio; if (Number.isFinite(audio.duration)) audio.currentTime = audio.duration * progress.value / 100; }); }
    const toggle = container.querySelector("#audio-panel-toggle:not([data-audio-bound])");
    if (toggle) { toggle.dataset.audioBound = "true"; toggle.addEventListener("click", () => { this.preferences.panelOpen = !this.preferences.panelOpen; this.applyPreferences(); this.savePreferences(); toggle.setAttribute("aria-expanded", String(this.preferences.panelOpen)); }); }
  }

  async play(data) {
    const channel = data.audioChannel;
    if (!this.channels[channel]) return;
    this.cancelFade(channel);
    const state = this.channels[channel];
    if (!state.audio.paused && state.audio.src && channel !== "effect") await this.fade(channel, 500);
    state.audio.pause(); state.audio.src = data.audioUrl; state.audio.currentTime = 0;
    state.baseVolume = Math.max(0, Math.min(1, Number(data.audioVolume)));
    state.audio.loop = data.audioLoop === "true"; state.audio.volume = this.effectiveVolume(channel);
    state.asset = {id: data.audioId, title: data.audioTitle, category: data.audioCategory, registerUrl: data.registerUrl};
    this.activeChannel = channel;
    try {
      await state.audio.play(); this.register(data.registerUrl);
      localStorage.setItem("grandline.audio.lastAsset", JSON.stringify({id: data.audioId, title: data.audioTitle, channel}));
    } catch (_) { this.announce("O navegador bloqueou a reprodução. Clique novamente para tocar."); }
    this.render();
  }

  register(url) {
    fetch(url, {method: "POST", headers: {"X-CSRFToken": this.csrf(), "X-Requested-With": "XMLHttpRequest"}, keepalive: true}).catch(() => {});
  }
  csrf() { return document.cookie.split("; ").find(row => row.startsWith("csrftoken="))?.split("=")[1] || ""; }
  stop(channel) { this.cancelFade(channel); const audio = this.channels[channel].audio; audio.pause(); audio.currentTime = 0; this.render(); }
  stopAll() { Object.keys(this.channels).forEach(name => this.stop(name)); this.announce("Todos os áudios foram interrompidos."); }
  toggle() { const audio = this.channels[this.activeChannel].audio; if (!audio.src) return; audio.paused ? audio.play().catch(() => {}) : audio.pause(); this.render(); }
  action(data) { if (data.audioAction === "stop-all") this.stopAll(); else if (data.audioAction === "stop") this.stop(this.activeChannel); else if (data.audioAction === "toggle") this.toggle(); else if (data.audioAction === "fade") this.fade(this.activeChannel, Number(data.seconds) * 1000); }
  cancelFade(channel) { if (this.fadeTimers[channel]) window.clearInterval(this.fadeTimers[channel]); delete this.fadeTimers[channel]; this.channels[channel].audio.volume = this.effectiveVolume(channel); }
  fade(channel, duration = 5000) {
    return new Promise(resolve => { const state = this.channels[channel], start = state.audio.volume, started = performance.now(); this.cancelFade(channel);
      this.fadeTimers[channel] = window.setInterval(() => { const ratio = Math.max(0, 1 - (performance.now() - started) / duration); state.audio.volume = start * ratio; if (!ratio) { this.stop(channel); state.audio.volume = this.effectiveVolume(channel); resolve(); } }, 50);
    });
  }
  format(seconds) { if (!Number.isFinite(seconds)) return "0:00"; return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`; }
  announce(message) { const title = document.querySelector("#audio-current-title"); if (title) title.textContent = message; }
  render() {
    const state = this.channels[this.activeChannel], audio = state.audio;
    const title = document.querySelector("#audio-current-title"), meta = document.querySelector("#audio-current-meta"), time = document.querySelector("#audio-time"), progress = document.querySelector("#audio-progress");
    if (title) title.textContent = state.asset?.title || "Nada reproduzindo";
    if (meta) meta.textContent = state.asset ? `${state.asset.category} · ${this.activeChannel} · ${audio.paused ? "pausado" : "reproduzindo"}` : "";
    if (time) time.textContent = `${this.format(audio.currentTime)} / ${this.format(audio.duration)}`;
    if (progress) progress.value = Number.isFinite(audio.duration) && audio.duration ? audio.currentTime / audio.duration * 100 : 0;
  }
  bindKeyboard() {
    document.addEventListener("keydown", event => { if (["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName) || event.target.isContentEditable) return;
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "s") { event.preventDefault(); this.stopAll(); }
      else if (event.code === "Space") { event.preventDefault(); this.toggle(); }
    });
  }
}

window.audioPanelController = window.audioPanelController || new AudioPanelController(document);
