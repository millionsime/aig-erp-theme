// AIG theme: swap default ERP desktop icons with the themed black/yellow copies.
// No core code is touched - we only rewrite asset URLs at runtime.

const AIG_ICON_BASE = "/assets/custom_theme/icons/desktop_icons";
const AIG_LOGO = "/assets/custom_theme/images/aig_logo.png";

// Matches icon URLs from frappe, erpnext or hrms, in any variant (solid, subtle, ...)
const CORE_ICON_RE =
  /\/assets\/(frappe|erpnext|hrms)\/icons\/desktop_icons\/([^/]+)\/([^/]+\.svg)/;

// App brand logos rendered on the desk (Framework, Frappe HR tiles)
const CORE_LOGO_RE = /\/assets\/(frappe|erpnext|hrms)\/images\/([^/]+\.svg)/;

function remap_icon(img) {
  const src = img.getAttribute("src") || "";
  let themed = null;
  const icon_match = src.match(CORE_ICON_RE);
  if (icon_match) {
    themed = `${AIG_ICON_BASE}/${icon_match[2]}/${icon_match[3]}`;
  } else {
    const logo_match = src.match(CORE_LOGO_RE);
    // Only swap logos we actually ship a themed copy for.
    if (logo_match) {
      const themed_logo = `/assets/custom_theme/images/${logo_match[2]}`;
      img.setAttribute("data-aig-themed-logo", themed_logo);
      themed = themed_logo;
    }
  }
  if (themed && img.getAttribute("src") !== themed) {
    img.setAttribute("src", themed);
  }
}

// Header brand logo (desk navbar) and the boot splash image.
// Server-side these come from Navbar Settings / Website Settings, but the
// desktop page is also cached in localStorage client-side, so keep a
// runtime swap as a fallback for stale caches.
function swap_brand_logos() {
  document
    .querySelectorAll("#brand-logo, .navbar-home img, .splash img")
    .forEach((img) => {
      if (img.getAttribute("src") !== AIG_LOGO) {
        img.setAttribute("src", AIG_LOGO);
      }
    });
}

function recolor_desktop_icons() {
  document
    .querySelectorAll('img[src*="/icons/desktop_icons/"], img[src*="-logo.svg"]')
    .forEach(remap_icon);
  swap_brand_logos();
}

recolor_desktop_icons();

// The sidebar/workspace icons render after boot and re-render on navigation;
// re-apply whenever the DOM changes. Remapped URLs no longer match the regex,
// so this is a no-op for already-themed icons (no loop).
const aig_icon_observer = new MutationObserver(recolor_desktop_icons);
aig_icon_observer.observe(document.body, { childList: true, subtree: true });
