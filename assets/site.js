/* Progressive enhancement: content and links work without JavaScript. */
(() => {
  'use strict';
  document.querySelector('[data-print]')?.addEventListener('click', () => window.print());
  document.querySelectorAll('img[data-fallback]').forEach(img => {
    const recover = () => {
      if (img.dataset.fallback && !img.dataset.fallbackUsed) {
        img.dataset.fallbackUsed = 'true'; img.src = img.dataset.fallback;
      }
    };
    img.addEventListener('error', recover);
    if (img.complete && img.naturalWidth === 0) recover();
  });
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches;
  const globalButton = document.querySelector('[data-toggle-animations]');
  const clips = Array.from(document.querySelectorAll('img[data-animation]')).map(img => {
    const button = img.closest('figure')?.querySelector('[data-toggle-clip]');
    const state = {img, button, poster: img.getAttribute('src'), ready: false, visible: false, playing: false, failed: false, userPaused: false};
    const render = () => {
      const playing = state.ready && state.visible && !paused && !state.userPaused;
      if (playing === state.playing) return;
      state.playing = playing;
      img.src = playing ? img.dataset.animation : state.poster;
      if (button) {button.textContent = playing ? 'Pause demo' : 'Play demo'; button.setAttribute('aria-pressed', String(playing));}
    };
    state.render = render;
    button?.addEventListener('click', () => {
      if (state.playing) state.userPaused = true;
      else {state.userPaused = false; paused = false; updateGlobal();}
      render();
    });
    state.load = () => {
      if (state.ready || state.failed || state.loading) return;
      state.loading = true;
      const test = new Image();
      test.onload = () => {state.ready = true; state.loading = false; if (button) button.hidden = false; render();};
      test.onerror = () => {state.failed = true; state.loading = false; if (button) button.hidden = true;};
      test.src = img.dataset.animation;
    };
    return state;
  });
  function updateGlobal() {
    if (!globalButton) return;
    globalButton.hidden = clips.length === 0;
    globalButton.textContent = paused ? 'Play animations' : 'Pause animations';
    globalButton.setAttribute('aria-pressed', String(!paused));
  }
  globalButton?.addEventListener('click', () => {
    paused = !paused;
    if (!paused) clips.forEach(s => {s.userPaused = false;});
    updateGlobal(); clips.forEach(s => s.render());
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      const state = clips.find(s => s.img === entry.target);
      if (!state) return;
      state.visible = entry.isIntersecting;
      if (entry.isIntersecting) state.load();
      state.render();
    }), {rootMargin: '80px', threshold: 0.01});
    clips.forEach(s => observer.observe(s.img));
  } else clips.forEach(s => {s.visible = true; s.load();});
  reduced.addEventListener('change', event => {paused = event.matches; updateGlobal(); clips.forEach(s => s.render());});
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) clips.forEach(s => {s.wasVisible = s.visible; s.visible = false; s.render();});
    else clips.forEach(s => {s.visible = s.wasVisible ?? s.visible; s.render();});
  });
  updateGlobal();
})();

// Keep a usable project link when a remotely hosted legacy thumbnail is unavailable.
(() => {
  document.querySelectorAll('img[data-remote-media]').forEach(img => {
    const placeholder = img.closest('figure')?.querySelector('[data-media-placeholder]');
    const recover = () => { if (placeholder) { img.hidden = true; placeholder.hidden = false; } };
    img.addEventListener('error', recover);
    if (img.complete && img.naturalWidth === 0) recover();
  });
})();
