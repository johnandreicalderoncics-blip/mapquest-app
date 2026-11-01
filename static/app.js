// Directions Finder - progressive enhancement only.
// The form works without JavaScript; this just shows feedback while
// the server round-trip is in flight.

(function () {
  "use strict";

  var form = document.getElementById("route-form");
  var button = document.getElementById("find-button");

  if (!form || !button) {
    return;
  }

  form.addEventListener("submit", function () {
    button.disabled = true;
    button.textContent = "Searching...";
  });
})();
