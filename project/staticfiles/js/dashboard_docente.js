document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos pasados desde Django
    const data = window.docenteData;
    
    // Solo crear el gráfico si hay actividades
    if (data.totalActividades > 0) {
        const chartElement = document.getElementById('chartMisActividades');
        
        if (chartElement) {
            new Chart(chartElement, {
                type: 'bar',
                data: {
                    labels: data.datosActividades.map(a => a.label),
                    datasets: [{
                        label: 'Estudiantes Inscritos',
                        data: data.datosActividades.map(a => a.value),
                        backgroundColor: 'rgba(40, 167, 69, 0.8)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: { 
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: data.totalActividades > 1
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return 'Estudiantes: ' + context.parsed.y;
                                }
                            }
                        }
                    }
                }
            });
        }
    }
});