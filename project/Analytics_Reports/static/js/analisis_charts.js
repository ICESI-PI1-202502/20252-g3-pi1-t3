// Configuración de colores para los gráficos
const colores = {
    primary: 'rgba(0, 123, 255, 0.8)',
    success: 'rgba(40, 167, 69, 0.8)',
    warning: 'rgba(255, 193, 7, 0.8)',
    danger: 'rgba(220, 53, 69, 0.8)',
    info: 'rgba(23, 162, 184, 0.8)',
    purple: 'rgba(111, 66, 193, 0.8)'
};

/**
 * Inicializa todos los gráficos de la página
 */
function initCharts(datosFrecuencia, datosRoles, datosFacultades, datosTiposActividad, datosReincidencia) {
    createFrecuenciaChart(datosFrecuencia);
    createReincidenciaChart(datosReincidencia);
    createRolesChart(datosRoles);
    createFacultadesChart(datosFacultades);
    createTiposActividadChart(datosTiposActividad);

    // === NUEVO: GRÁFICO DE DÍAS DE LA SEMANA ===
    if (datosDiasSemana && datosDiasSemana.length > 0) {
        const ctxDias = document.getElementById('chartDiasSemana');
        if (ctxDias) {
            // Colores según el día (días laborales azul, fin de semana verde)
            const coloresDias = [
                'rgba(54, 162, 235, 0.7)',  // Lunes
                'rgba(54, 162, 235, 0.7)',  // Martes
                'rgba(54, 162, 235, 0.7)',  // Miércoles
                'rgba(54, 162, 235, 0.7)',  // Jueves
                'rgba(54, 162, 235, 0.7)',  // Viernes
                'rgba(75, 192, 192, 0.7)',  // Sábado
                'rgba(255, 159, 64, 0.7)'   // Domingo
            ];
            
            const coloresBorde = [
                'rgba(54, 162, 235, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 159, 64, 1)'
            ];
            
            new Chart(ctxDias, {
                type: 'bar',
                data: {
                    labels: datosDiasSemana.map(d => d.label),
                    datasets: [{
                        label: 'Asistencias',
                        data: datosDiasSemana.map(d => d.value),
                        backgroundColor: coloresDias,
                        borderColor: coloresBorde,
                        borderWidth: 2,
                        borderRadius: 5,
                        barThickness: 'flex',
                        maxBarThickness: 60
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = datosDiasSemana.reduce((sum, d) => sum + d.value, 0);
                                    const porcentaje = total > 0 ? ((context.parsed.y / total) * 100).toFixed(1) : 0;
                                    return [
                                        `Asistencias: ${context.parsed.y}`,
                                        `Porcentaje: ${porcentaje}%`
                                    ];
                                }
                            },
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 14,
                                weight: 'bold'
                            },
                            bodyFont: {
                                size: 13
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0,
                                font: {
                                    size: 12
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    size: 12,
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    },
                    animation: {
                        duration: 1000,
                        easing: 'easeInOutQuart'
                    }
                }
            });
        }
    }
    
}

/**
 * Gráfico 1: Distribución por Frecuencia (Doughnut)
 */
function createFrecuenciaChart(datos) {
    new Chart(document.getElementById('chartFrecuencia'), {
        type: 'doughnut',
        data: {
            labels: datos.map(d => d.label),
            datasets: [{
                data: datos.map(d => d.value),
                backgroundColor: [colores.success, colores.warning, colores.danger],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Gráfico 2: Nuevos vs Reincidentes (Pie)
 */
function createReincidenciaChart(datos) {
    new Chart(document.getElementById('chartReincidencia'), {
        type: 'pie',
        data: {
            labels: datos.map(d => d.label),
            datasets: [{
                data: datos.map(d => d.value),
                backgroundColor: [colores.primary, colores.info],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { 
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Gráfico 3: Segmentación por Roles (Bar)
 */
function createRolesChart(datos) {
    new Chart(document.getElementById('chartRoles'), {
        type: 'bar',
        data: {
            labels: datos.map(d => d.label),
            datasets: [{
                label: 'Participantes',
                data: datos.map(d => d.value),
                backgroundColor: colores.primary,
                borderRadius: 6,
                borderWidth: 1,
                borderColor: 'rgba(0, 123, 255, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { 
                    beginAtZero: true,
                    ticks: { 
                        precision: 0,
                        font: { size: 11 }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: { size: 11 }
                    }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Participantes: ${context.parsed.y}`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Gráfico 4: Top Facultades (Bar Horizontal)
 */
function createFacultadesChart(datos) {
    if (datos && datos.length > 0) {
        new Chart(document.getElementById('chartFacultades'), {
            type: 'bar',
            data: {
                labels: datos.map(d => d.label),
                datasets: [{
                    label: 'Participantes',
                    data: datos.map(d => d.value),
                    backgroundColor: colores.success,
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: 'rgba(40, 167, 69, 1)'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { 
                        beginAtZero: true,
                        ticks: { 
                            precision: 0,
                            font: { size: 11 }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    y: {
                        ticks: {
                            font: { size: 10 }
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Participantes: ${context.parsed.x}`;
                            }
                        }
                    }
                }
            }
        });
    } else {
        document.getElementById('chartFacultades').parentElement.innerHTML = 
            '<div class="text-center text-muted py-5"><i class="fas fa-inbox" style="font-size:3rem;opacity:0.3"></i><p class="mt-3">Sin datos de facultades</p></div>';
    }
}

/**
 * Gráfico 5: Distribución por Tipo de Actividad (Bar)
 */
function createTiposActividadChart(datos) {
    if (datos && datos.length > 0) {
        new Chart(document.getElementById('chartTiposActividad'), {
            type: 'bar',
            data: {
                labels: datos.map(d => d.label),
                datasets: [{
                    label: 'Participaciones',
                    data: datos.map(d => d.value),
                    backgroundColor: colores.warning,
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: 'rgba(255, 193, 7, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: { 
                            precision: 0,
                            font: { size: 11 }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: { size: 11 },
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Participaciones: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            }
        });
    } else {
        document.getElementById('chartTiposActividad').parentElement.innerHTML = 
            '<div class="text-center text-muted py-5"><i class="fas fa-inbox" style="font-size:3rem;opacity:0.3"></i><p class="mt-3">Sin datos de tipos de actividad</p></div>';
    }
}