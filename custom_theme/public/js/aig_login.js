// AIG login page branding: swap the card logo for the AIG logo.
// Pure asset swap - no core templates are modified.

(function () {
  const AIG_LOGO = "/assets/custom_theme/images/aig_logo.png";

  function applyAigBrand() {
    // www auth pages (login, forgot password, update password) all use img.app-logo
    document.querySelectorAll("img.app-logo").forEach(function (img) {
      if (img.getAttribute("src") !== AIG_LOGO) {
        img.setAttribute("src", AIG_LOGO);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyAigBrand);
  } else {
    applyAigBrand();
  }
})();
