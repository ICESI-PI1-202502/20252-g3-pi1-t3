document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.querySelector('.navbar-option img[src*="Menu.png"]');

  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");

  if (menuBtn && sidebar && overlay) {
    // Open the Menu
    menuBtn.addEventListener("click", (e) => {
      e.preventDefault();
      sidebar.classList.add("open");
      overlay.classList.add("show");
    });

    // close to clic in overlay
    overlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      overlay.classList.remove("show");
    });
  }
});
