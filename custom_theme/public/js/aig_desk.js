function recolor_desktop_icons() {
  document.querySelectorAll('img.app-icon, .sidebar-header img, .desktop-icon img').forEach(function(img) {
    var match = img.src.match(/\/assets\/(frappe|erpnext|hrms)\/icons\/desktop_icons\/solid\/(.+\.svg)/);
    if (match) {
      img.src = img.src.replace(match[0], '/assets/custom_theme/icons/desktop_icons/solid/' + match[2]);
    }
  });
}
recolor_desktop_icons();
const aig_icon_observer = new MutationObserver(recolor_desktop_icons);
aig_icon_observer.observe(document.body, { childList: true, subtree: true });
