(() => {
  let settings = {};
  try { settings = JSON.parse(localStorage.getItem('whatif-settings') || '{}') || {}; } catch (_) { /* Use system defaults when storage is unavailable. */ }
  const theme = ['light', 'dark'].includes(settings.theme) ? settings.theme : (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
  document.documentElement.dataset.motion = settings.motion || 'system';
  document.documentElement.dataset.readability = settings.readability || 'normal';
  window.whatifSettings = settings;
})();
