document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos pasados desde Django
    const data = window.dashboardData;
    
    // Configuración común de gráficos
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    };
    
    // Gráfico de distribución de alertas
    const alertasCtx = document.getElementById('chartAlertas');
    if (alertasCtx) {
        new Chart(alertasCtx, {
            type: 'doughnut',
            data: {
                labels: ['Riesgo Crítico', 'Baja Asistencia', 'Inactivos', 'Activos'],
                datasets: [{
                    data: [
                        data.alertasRiesgo,
                        data.pocaAsistencia,
                        data.estudiantesInactivos,
                        data.estudiantesActivos
                    ],
                    backgroundColor: [
                        '#dc3545',
                        '#ffc107',
                        '#17a2b8',
                        '#28a745'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                ...commonOptions,
                plugins: {
                    ...commonOptions.plugins,
                    title: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Gráfico de reconocimientos y destacados
    const reconocimientosCtx = document.getElementById('chartReconocimientos');
    if (reconocimientosCtx) {
        new Chart(reconocimientosCtx, {
            type: 'bar',
            data: {
                labels: ['Próximos a Reconocimiento', 'Destacados'],
                datasets: [{
                    label: 'Estudiantes',
                    data: [
                        data.proximosReconocimientos,
                        data.estudiantesDestacados
                    ],
                    backgroundColor: [
                        'rgba(40, 167, 69, 0.7)',
                        'rgba(40, 167, 69, 0.9)'
                    ],
                    borderColor: '#28a745',
                    borderWidth: 2
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    // Toggle detalles colapsables
    document.querySelectorAll('.collapsible-header').forEach(header => {
        header.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const icon = this.querySelector('.toggle-icon');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            } else {
                content.style.display = 'none';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        });
    });
});