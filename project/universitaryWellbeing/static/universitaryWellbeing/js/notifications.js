// Manejo del dropdown de notificaciones
        document.addEventListener('DOMContentLoaded', function() {
            const notifBtn = document.getElementById('notificationsBtn');
            const notifMenu = document.getElementById('notificationsMenu');
            
            if (!notifBtn || !notifMenu) return; // Salir si no existen los elementos
            
            // Toggle del menú de notificaciones
            notifBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                notifMenu.classList.toggle('show');
            });
            
            // Cerrar al hacer click fuera
            document.addEventListener('click', function(e) {
                if (!notifMenu.contains(e.target) && !notifBtn.contains(e.target)) {
                    notifMenu.classList.remove('show');
                }
            });
            
            // Marcar como leída al hacer click
            document.querySelectorAll('.notification-item').forEach(item => {
                item.addEventListener('click', function() {
                    const notifId = this.dataset.notifId;
                    
                    // Solo marcar si es no leída
                    if (!this.classList.contains('unread')) return;
                    
                    // Marcar visualmente como leída
                    this.classList.remove('unread');
                    const dot = this.querySelector('.notification-unread-dot');
                    if (dot) dot.remove();
                    
                    // Llamada AJAX para marcar como leída en el backend
                    fetch(`/notificaciones/${notifId}/marcar-leida/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        }
                    }).then(response => {
                        if (response.ok) {
                            // Actualizar el contador del badge
                            const badge = document.querySelector('.notifications-badge');
                            if (badge) {
                                let count = parseInt(badge.textContent) - 1;
                                if (count > 0) {
                                    badge.textContent = count;
                                } else {
                                    badge.remove();
                                }
                            }
                        }
                    }).catch(error => {
                        console.error('Error al marcar notificación como leída:', error);
                    });
                });
            });
            
            // Función helper para obtener el CSRF token
            function getCookie(name) {
                let cookieValue = null;
                if (document.cookie && document.cookie !== '') {
                    const cookies = document.cookie.split(';');
                    for (let i = 0; i < cookies.length; i++) {
                        const cookie = cookies[i].trim();
                        if (cookie.substring(0, name.length + 1) === (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }
        });




document.addEventListener("DOMContentLoaded", function() {
    const notifBtn = document.getElementById("notificationsBtn");
    const notifMenu = document.getElementById("notificationsMenu");

    if (notifBtn && notifMenu) {
        notifBtn.addEventListener("click", function(e) {
            e.preventDefault(); // 
            notifMenu.classList.toggle("active");
        });
    }
});
