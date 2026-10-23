/* Load the browser interface after checking how the document was opened. */
'use strict';
(() => {
  const main = document.querySelector('main');
  if (location.protocol === 'file:') {
    main.replaceChildren(document.querySelector('#local-startup').content.cloneNode(true));
    document.querySelector('nav').hidden = true;
    document.querySelector('#audio-toggle').hidden = true;
    document.querySelector('#theme').hidden = true;
    document.querySelector('.audio-dock').hidden = true;
    return;
  }
  function load(path) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = path; script.onload = resolve;
      script.onerror = () => reject(new Error('A game file could not load. Extract the complete project and use the included launcher.'));
      document.head.append(script);
    });
  }
  load('static/js/audio.js').then(() => load('static/js/app.js')).catch(error => {
    main.replaceChildren();
    const message = document.createElement('p'); message.textContent = error.message;
    main.append(message);
  });
})();
