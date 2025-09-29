// Obtener variables desde el HTML
const container = document.getElementById('asistencia-data');
const gestionAsistenciaUrl = container.dataset.url;
const fechaEsHoy = container.dataset.fechaEsHoy === 'true';

// Función para editar asistencia
function editarAsistencia(asistenciaId) {
    alert('Funcionalidad de edición - ID: ' + asistenciaId);
}

// Event listener para todos los botones de editar
document.querySelectorAll('.btn-editar-asistencia').forEach(btn => {
    btn.addEventListener('click', function() {
        const asistenciaId = this.dataset.id;
        editarAsistencia(asistenciaId);
    });
});

// Función para exportar asistencias
function exportarAsistencias() {
    const params = new URLSearchParams(window.location.search);
    params.set('export', 'csv');
    window.location.href = gestionAsistenciaUrl + '?' + params.toString();
}

// Auto-refresh cada 30 segundos si es la fecha actual
if (fechaEsHoy) {
    setTimeout(function() {
        location.reload();
    }, 30000);
}



 