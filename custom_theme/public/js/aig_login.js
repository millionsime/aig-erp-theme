// AIG login page branding: swap the card logo for the AIG logo and add the
// "Adama Investment Group" wordmark above the card.
// Pure DOM injection / asset swap - no core templates are modified.

(function () {
  const AIG_LOGO = "/assets/custom_theme/images/aig_logo.png";
  const WORDMARK_ID = "aig-wordmark";

  function applyAigBrand() {
    // www auth pages (login, forgot password, update password) all use img.app-logo
    document.querySelectorAll("img.app-logo").forEach(function (img) {
      if (img.getAttribute("src") !== AIG_LOGO) {
        img.setAttribute("src", AIG_LOGO);
      }
    });

    injectWordmark();
  }

  function injectWordmark() {
    if (document.getElementById(WORDMARK_ID)) return;
    var card = document.querySelector(".login-content.page-card");
    if (!card || !card.parentNode) return;

    var wrap = document.createElement("div");
    wrap.id = WORDMARK_ID;
    wrap.className = "aig-wordmark";

    var title = document.createElement("h1");
    title.className = "aig-wordmark-title";
    title.textContent = "Adama Investment Group";

    var rule = document.createElement("div");
    rule.className = "aig-wordmark-rule";

    wrap.appendChild(title);
    wrap.appendChild(rule);
    card.parentNode.insertBefore(wrap, card);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyAigBrand);
  } else {
    applyAigBrand();
  }
})();
