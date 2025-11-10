document.addEventListener('DOMContentLoaded', function() {
    // ========== ACTUALIZACIÓN EN TIEMPO REAL DE LA VISTA PREVIA ==========
    
    // Mapeo de inputs a elementos de preview
    const previews = {
        'asistencias_reconocimiento': { elem: 'preview-reconocimiento', suffix: ' asistencias' },
        'margen_proximo_reconocimiento': { elem: 'preview-margen', suffix: '' },
        'asistencias_destacado': { elem: 'preview-destacado', prefix: '≥ ', suffix: '' },
        'umbral_baja_asistencia': { elem: 'preview-baja', prefix: '< ', suffix: '' },
        'umbral_riesgo_critico': { elem: 'preview-riesgo', prefix: '≤ ', suffix: '' },
        'dias_inactividad': { elem: 'preview-inactivo', suffix: ' días' },
        'asistencias_minimas_encuesta': { elem: 'preview-encuesta-min', suffix: '' },
        'dias_despues_cierre_encuesta': { elem: 'preview-encuesta-dias', suffix: ' días' }
    };
    
    // Actualizar preview cuando cambia un input
    Object.keys(previews).forEach(inputId => {
        const input = document.getElementById(inputId);
        const config = previews[inputId];
        
        if (input) {
            input.addEventListener('input', function() {
                const previewElem = document.getElementById(config.elem);
                if (previewElem) {
                    const prefix = config.prefix || '';
                    const suffix = config.suffix || '';
                    previewElem.textContent = prefix + this.value + suffix;
                }
            });
        }
    });
    
    // ========== VALIDACIÓN DE FORMULARIO ==========
    const form = document.getElementById('configForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            const reconocimiento = parseInt(document.getElementById('asistencias_reconocimiento').value);
            const destacado = parseInt(document.getElementById('asistencias_destacado').value);
            const riesgo = parseInt(document.getElementById('umbral_riesgo_critico').value);
            const baja = parseInt(document.getElementById('umbral_baja_asistencia').value);
            
            // El umbral de destacado debe ser mayor al de reconocimiento
            if (destacado <= reconocimiento) {
                e.preventDefault();
                alert('⚠️ El umbral de destacado (' + destacado + ') debe ser mayor al de reconocimiento principal (' + reconocimiento + ')');
                return false;
            }
            
            // El umbral de baja asistencia debe ser mayor al de riesgo crítico
            if (baja <= riesgo) {
                e.preventDefault();
                alert('⚠️ El umbral de baja asistencia (' + baja + ') debe ser mayor al de riesgo crítico (' + riesgo + ')');
                return false;
            }
            
            // Todo OK - continuar con el submit
            return true;
        });
    }
});