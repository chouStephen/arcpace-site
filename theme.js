// Appearance switch for the guides and calculator, as on the home page:
// Auto follows the system; Light and Dark are remembered on this browser.
(function () {
  var root = document.documentElement;
  var buttons = document.querySelectorAll('[data-theme-choice]');
  function current() { return root.dataset.theme || 'auto'; }
  function paint() {
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.themeChoice === current())); });
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      var choice = b.dataset.themeChoice;
      if (choice === 'auto') delete root.dataset.theme; else root.dataset.theme = choice;
      try {
        if (choice === 'auto') localStorage.removeItem('arcpace-theme');
        else localStorage.setItem('arcpace-theme', choice);
      } catch (e) {}
      paint();
    });
  });
  paint();
})();
