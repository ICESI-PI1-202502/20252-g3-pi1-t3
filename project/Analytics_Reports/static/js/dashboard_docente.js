// static/js/dashboard_docente.js

document.addEventListener('DOMContentLoaded', function() {
    // ========== GRÁFICO: Actividades Populares ==========
    const ctxActividades = document.getElementById('chartMisActividades');
    
    if (ctxActividades && window.docenteData.datosActividades.length > 0) {
        new Chart(ctxActividades, {
            type: 'bar',
            data: {
                labels: window.docenteData.datosActividades.map(item => item.label),
                datasets: [{
                    label: 'Estudiantes Inscritos',
                    data: window.docenteData.datosActividades.map(item => item.value),
                    backgroundColor: 'rgba(40, 167, 69, 0.6)',
                    borderColor: '#28a745',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + ' estudiantes';
                            }
                        }
                    }
                },
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

    // ========== GRÁFICO: Asistencia por Día de la Semana ==========
    const ctxDias = document.getElementById('chartAsistenciaPorDia');
    
    if (ctxDias && window.docenteData.datosAsistenciaPorDia) {
        const datosDias = window.docenteData.datosAsistenciaPorDia;
        
        new Chart(ctxDias, {
            type: 'bar',
            data: {
                labels: datosDias.map(item => item.label),
                datasets: [{
                    label: 'Promedio de Asistentes',
                    data: datosDias.map(item => item.value),
                    backgroundColor: datosDias.map(item => {
                        if (item.value >= 15) return 'rgba(40, 167, 69, 0.6)'; // Verde
                        if (item.value >= 10) return 'rgba(255, 193, 7, 0.6)'; // Amarillo
                        return 'rgba(220, 53, 69, 0.6)'; // Rojo
                    }),
                    borderColor: datosDias.map(item => {
                        if (item.value >= 15) return '#28a745';
                        if (item.value >= 10) return '#ffc107';
                        return '#dc3545';
                    }),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const dato = datosDias[index];
                                return [
                                    `Promedio: ${dato.value} estudiantes`,
                                    `Total asistencias: ${dato.total_asistencias}`,
                                    `Sesiones: ${dato.sesiones}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 2
                        },
                        title: {
                            display: true,
                            text: 'Promedio de Asistentes por Sesión'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Día de la Semana'
                        }
                    }
                }
            }
        });
    }
});