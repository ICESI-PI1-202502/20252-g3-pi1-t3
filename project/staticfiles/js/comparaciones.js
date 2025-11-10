// Funciones globales para eventos inline
function actualizarFiltros() {
  const tipo = document.getElementById('tipo').value;
  document.getElementById('filtros-periodos-semestrales').style.display = tipo === 'periodos_semestrales' ? 'block' : 'none';
  document.getElementById('filtros-periodos-personalizados').style.display = tipo === 'periodos_personalizados' ? 'block' : 'none';
}

function aplicarFiltroAnios() {
  // Obtener el formulario
  const form = document.getElementById('form-comparaciones');
  
  // Desmarcar todos los checkboxes de periodos para evitar errores
  const checkboxes = document.querySelectorAll('input[name="periodos_semestrales[]"]');
  checkboxes.forEach(cb => cb.checked = false);
  
  // Enviar el formulario para recargar con el nuevo filtro de años
  form.submit();
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos pasados desde Django
    const data = window.comparacionesData;
    
    // Solo crear el gráfico si hay datos para mostrar
    if (data.ejecutarConsulta) {
        crearGraficaComparacion(data);
    }
});

// Función para crear la gráfica comparativa
function crearGraficaComparacion(data) {
    const ctx = document.getElementById('grafica-comparacion');
    
    if (!ctx) {
        console.warn('Canvas grafica-comparacion no encontrado');
        return;
    }
    
    const datosGrafica = data.datosGrafica;
    const agrupacion = data.agrupacion;
    const metrica = data.metrica;
    const tipoGrafica = data.tipoGrafica;
    
    // Mapear tipo de gráfica
    let chartType = 'bar';
    if (tipoGrafica === 'area') {
        chartType = 'line'; // Area usa line con fill:true
    }
    
    new Chart(ctx, {
        type: chartType,
        data: datosGrafica,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2.5,
            plugins: {
                title: {
                    display: true,
                    text: 'Comparación: ' + metrica.charAt(0).toUpperCase() + metrica.slice(1) + 
                          (agrupacion !== 'ninguna' ? ' por ' + agrupacion.replace('_', ' ') : ''),
                    font: { size: 18, weight: 'bold' }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y;
                            
                            // Calcular porcentaje del total
                            const datasetData = context.dataset.data;
                            const total = datasetData.reduce((a, b) => a + b, 0);
                            if (total > 0) {
                                const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                                label += ' (' + percentage + '%)';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: metrica.charAt(0).toUpperCase() + metrica.slice(1)
                    }
                },
                x: {
                    title: {
                        display: agrupacion !== 'ninguna',
                        text: agrupacion !== 'ninguna' ? agrupacion.replace('_', ' ').charAt(0).toUpperCase() + agrupacion.replace('_', ' ').slice(1) : ''
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.4 // Líneas curvas suaves para gráfica de área
                },
                point: {
                    radius: tipoGrafica === 'area' ? 4 : 0,
                    hoverRadius: 6
                }
            }
        }
    });
}