document.addEventListener("DOMContentLoaded", () => {
  const menuBtn = document.getElementById("menu-btn");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");

  if (menuBtn && sidebar && overlay) {
    // Abrir menú
    menuBtn.addEventListener("click", (e) => {
      e.preventDefault();
      sidebar.classList.toggle("open");
      overlay.classList.toggle("show");
    });

    // Cerrar al hacer clic fuera
    overlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      overlay.classList.remove("show");
    });
  }
});
