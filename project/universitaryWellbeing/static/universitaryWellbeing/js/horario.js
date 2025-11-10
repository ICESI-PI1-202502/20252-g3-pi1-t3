document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');

  // 1) Leer eventos desde el <script type="application/json">
  const eventsScript = document.getElementById('events-data');
  let eventos = [];
  if (eventsScript) {
    try {
      eventos = JSON.parse(eventsScript.textContent);
    } catch (e) {
      console.error('Eventos JSON inválido:', e);
    }
  }

  // 2) Formateadores de fecha/hora
  const fmtDate = new Intl.DateTimeFormat('es-CO', { 
    dateStyle: 'full'
  });
  const fmtTime = new Intl.DateTimeFormat('es-CO', { 
    timeStyle: 'short' 
  });
  const fmtDateTime = new Intl.DateTimeFormat('es-CO', { 
    dateStyle: 'medium', 
    timeStyle: 'short' 
  });

  // 3) Variable para evento seleccionado
  let selectedEvent = null;

  // 4) Inicializar FullCalendar
  let showWeekends = true;
  let initialView = window.innerWidth < 576 ? "timeGridDay" : "timeGridWeek";
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: initialView,
    locale: 'es',
    expandRows: true,
    stickyHeaderDates: true,

    allDaySlot: false,
    slotMinTime: "06:00:00",
    slotMaxTime: "22:00:00",
    slotDuration: "00:30:00",
    slotLabelInterval: "01:00",
    eventOverlap: true,
    weekends: showWeekends,

    height: "auto",
    headerToolbar: false,
    nowIndicator: true,
    navLinks: true,
    dayMaxEvents: 3,
    eventMaxStack: 3,

    events: eventos,

    // Tooltip al pasar el mouse
    eventMouseEnter: function(info) {
      let tt = document.querySelector('.fc-tooltip');
      if (!tt) {
        tt = document.createElement('div');
        tt.className = 'fc-tooltip';
        document.body.appendChild(tt);
      }
      
      const start = info.event.start ? fmtDateTime.format(info.event.start) : '';
      const end = info.event.end ? fmtTime.format(info.event.end) : '';
      const notas = info.event.extendedProps?.notas || '';
      const fuente = info.event.extendedProps?.fuente || '';
      
      tt.innerHTML = `
        <div><strong>${info.event.title}</strong></div>
        ${start ? `<div> ${start}${end ? ` - ${end}` : ''}</div>` : ''}
        ${fuente ? `<div> ${fuente}</div>` : ''}
        ${notas ? `<div style="margin-top: 6px; font-size: 0.85rem;">${notas}</div>` : ''}
        <div style="margin-top: 8px; font-size: 0.8rem; opacity: 0.8;">Click para ver detalles</div>
      `;
      tt.style.display = 'block';
      
      const move = (e) => { 
        tt.style.left = (e.pageX + 12) + 'px'; 
        tt.style.top = (e.pageY + 12) + 'px'; 
      };
      info.el.addEventListener('mousemove', move);
      info.el._moveHandler = move;
    },

    eventMouseLeave: function(info) {
      const tt = document.querySelector('.fc-tooltip');
      if (tt) tt.style.display = 'none';
      if (info.el._moveHandler) {
        info.el.removeEventListener('mousemove', info.el._moveHandler);
        delete info.el._moveHandler;
      }
    },

    // Click en evento - mostrar modal de detalles
    eventClick: function(info) {
      selectedEvent = info.event;
      openEventModal(info.event);
    },

    // Click en día - mostrar eventos del día
    dateClick: function(arg) { 
      openDayModal(arg.date); 
    },

    // Click en "más eventos"
    moreLinkClick: function(arg) { 
      openDayModal(arg.date); 
      return 'popover'; 
    }
  });

  calendar.render();

  window.addEventListener("resize", () => {
    if (window.innerWidth < 576 && calendar.view.type !== "timeGridDay") {
      calendar.changeView("timeGridDay");
    }
  });

  // --- Controles de navegación ---
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnToday = document.getElementById('btn-today');
  const btnMonth = document.getElementById('btn-month');
  const btnWeek = document.getElementById('btn-week');
  const btnDay = document.getElementById('btn-day');
  const btnWeekends = document.getElementById('btn-weekends');
  const goDateInput = document.getElementById('go-date');
  const btnGo = document.getElementById('btn-go');

  if (btnPrev) btnPrev.addEventListener('click', () => calendar.prev());
  if (btnNext) btnNext.addEventListener('click', () => calendar.next());
  if (btnToday) btnToday.addEventListener('click', () => calendar.today());

  function setActiveView(btn) {
    [btnMonth, btnWeek, btnDay].forEach(b => b && b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }

  if (btnMonth) btnMonth.addEventListener('click', () => { 
    calendar.changeView('dayGridMonth'); 
    setActiveView(btnMonth); 
  });
  
  if (btnWeek) btnWeek.addEventListener('click', () => { 
    calendar.changeView('timeGridWeek'); 
    setActiveView(btnWeek); 
  });
  
  if (btnDay) btnDay.addEventListener('click', () => { 
    calendar.changeView('timeGridDay'); 
    setActiveView(btnDay); 
  });

  if (btnWeekends) btnWeekends.addEventListener('click', () => {
    showWeekends = !showWeekends;
    calendar.setOption('weekends', showWeekends);
    btnWeekends.classList.toggle('active', showWeekends);
  });

  if (btnGo) btnGo.addEventListener('click', () => {
    const val = goDateInput && goDateInput.value;
    if (val) calendar.gotoDate(val);
  });

  // --- Modal de detalles del evento ---
  function openEventModal(event) {
    const modalEl = document.getElementById('eventModal');
    const detailsEl = document.getElementById('event-details');
    const deleteBtn = document.getElementById('btn-delete-event');
    
    if (!modalEl || !detailsEl) return;

    const start = event.start ? fmtDateTime.format(event.start) : 'No especificado';
    const end = event.end ? fmtDateTime.format(event.end) : 'No especificado';
    const notas = event.extendedProps?.notas || 'Sin notas';
    const fuente = event.extendedProps?.fuente || 'Desconocida';
    const tipo = event.extendedProps?.tipo || 'otro';
    const puedeEliminar = event.extendedProps?.puede_eliminar || false;

    // Iconos por tipo
    const tipoIcons = {
      'actividad': '',
      'cita': '',
      'partido': '',
      'otro': ''
    };

    const tipoLabels = {
      'actividad': 'Actividad',
      'cita': 'Cita',
      'partido': 'Partido',
      'otro': 'Otro'
    };

    detailsEl.innerHTML = `
      <div class="event-detail-item">
        <div class="event-detail-label">Título</div>
        <div class="event-detail-value">
          <strong>${tipoIcons[tipo]} ${event.title}</strong>
        </div>
      </div>
      
      <div class="event-detail-item">
        <div class="event-detail-label">Tipo de evento</div>
        <div class="event-detail-value">
          <span class="badge bg-primary">${tipoLabels[tipo]}</span>
        </div>
      </div>
      
      <div class="event-detail-item">
        <div class="event-detail-label">Fecha y hora de inicio</div>
        <div class="event-detail-value"> ${start}</div>
      </div>
      
      <div class="event-detail-item">
        <div class="event-detail-label">Fecha y hora de fin</div>
        <div class="event-detail-value"> ${end}</div>
      </div>
      
      <div class="event-detail-item">
        <div class="event-detail-label">Fuente</div>
        <div class="event-detail-value">
          <span class="event-badge ${fuente === 'Manual' ? 'badge-manual' : 'badge-automatica'}">
            ${fuente === 'Manual' ? 'Creado manualmente' : 'Creado automáticamente'}
          </span>
        </div>
      </div>
      
      ${notas !== 'Sin notas' ? `
        <div class="event-detail-item">
          <div class="event-detail-label">Notas</div>
          <div class="event-detail-value">${notas}</div>
        </div>
      ` : ''}
    `;

    // Mostrar/ocultar botón de eliminar
    if (puedeEliminar) {
      deleteBtn.style.display = 'inline-block';
    } else {
      deleteBtn.style.display = 'none';
    }

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  // --- Eliminar evento ---
  const btnDeleteEvent = document.getElementById('btn-delete-event');
  if (btnDeleteEvent) {
    btnDeleteEvent.addEventListener('click', function() {
      if (!selectedEvent) return;
      
      // Cerrar modal de detalles
      const eventModal = bootstrap.Modal.getInstance(document.getElementById('eventModal'));
      if (eventModal) eventModal.hide();
      
      // Abrir modal de confirmación
      openConfirmDeleteModal(selectedEvent);
    });
  }

  // --- Modal de confirmación de eliminación ---
  function openConfirmDeleteModal(event) {
    const modalEl = document.getElementById('confirmDeleteModal');
    const detailsEl = document.getElementById('confirm-delete-details');
    
    if (!modalEl || !detailsEl) return;

    const start = event.start ? fmtDateTime.format(event.start) : '';
    
    detailsEl.innerHTML = `
      <div class="card">
        <div class="card-body">
          <h6 class="card-title mb-2">${event.title}</h6>
          <p class="card-text mb-0"><small class="text-muted">${start}</small></p>
        </div>
      </div>
    `;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }

  // --- Confirmar eliminación ---
  const btnConfirmDelete = document.getElementById('btn-confirm-delete');
  if (btnConfirmDelete) {
    btnConfirmDelete.addEventListener('click', async function() {
      if (!selectedEvent) return;

      const eventId = selectedEvent.id;
      
      try {
        btnConfirmDelete.disabled = true;
        btnConfirmDelete.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Eliminando...';

        const response = await fetch(`/horario/eliminar/${eventId}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();

        if (data.success) {
          // Eliminar evento del calendario
          selectedEvent.remove();
          
          // Cerrar modal de confirmación
          const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmDeleteModal'));
          if (confirmModal) confirmModal.hide();
          
          // Mostrar mensaje de éxito
          showToast('success', data.message || 'Evento eliminado correctamente');
          
          selectedEvent = null;
        } else {
          showToast('error', data.message || 'Error al eliminar el evento');
        }
      } catch (error) {
        console.error('Error:', error);
        showToast('error', 'Error de conexión al eliminar el evento');
      } finally {
        btnConfirmDelete.disabled = false;
        btnConfirmDelete.innerHTML = '<i class="bi bi-trash"></i> Sí, Eliminar';
      }
    });
  }

  // --- Modal de eventos del día ---
  function openDayModal(dateObj) {
    const startOfDay = new Date(dateObj); 
    startOfDay.setHours(0,0,0,0);
    const endOfDay = new Date(dateObj); 
    endOfDay.setHours(23,59,59,999);

    const dayEvents = calendar.getEvents().filter(ev => {
      const evStart = ev.start || ev.extendedProps.start;
      const evEnd = ev.end || ev.extendedProps.end || evStart;
      return (evStart <= endOfDay) && (evEnd >= startOfDay);
    }).sort((a,b) => (a.start || 0) - (b.start || 0));

    const titleDate = fmtDate.format(startOfDay);
    const titleEl = document.getElementById('dayModalLabel');
    if (titleEl) titleEl.textContent = `Eventos del ${titleDate}`;

    const list = document.getElementById('day-events-list');
    if (!list) return;

    if (dayEvents.length === 0) {
      list.innerHTML = `
        <div class="text-center py-4">
          <i class="bi bi-calendar-x" style="font-size: 3rem; color: #dee2e6;"></i>
          <p class="text-muted mt-3 mb-0">No hay eventos para este día.</p>
        </div>
      `;
    } else {
      list.innerHTML = dayEvents.map(ev => {
        const start = ev.start ? fmtTime.format(ev.start) : '';
        const end = ev.end ? fmtTime.format(ev.end) : '';
        const notas = ev.extendedProps?.notas || '';
        const tipo = ev.extendedProps?.tipo || 'otro';
        
        const tipoIcons = {
          'actividad': '',
          'cita': '',
          'partido': '',
          'otro': ''
        };

        return `
          <div class="card mb-3 border-start border-4" style="border-color: ${ev.backgroundColor} !important; cursor: pointer;" 
               onclick="calendar.getEventById('${ev.id}').click()">
            <div class="card-body">
              <h6 class="card-title mb-2">
                ${tipoIcons[tipo]} ${ev.title}
              </h6>
              ${start && end ? `
                <p class="card-text mb-1">
                  <small class="text-muted">
                    <i class="bi bi-clock"></i> ${start} - ${end}
                  </small>
                </p>
              ` : ''}
              ${notas ? `
                <p class="card-text mb-0">
                  <small>${notas}</small>
                </p>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    const modalEl = document.getElementById('dayModal');
    if (modalEl && window.bootstrap?.Modal) {
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    }
  }

  // --- Sistema de notificaciones toast ---
  function showToast(type, message) {
    // Crear contenedor si no existe
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
      toastContainer.style.zIndex = '9999';
      document.body.appendChild(toastContainer);
    }

    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';

    const toastHTML = `
      <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert">
        <div class="d-flex">
          <div class="toast-body">
            <i class="bi ${icon} me-2"></i>${message}
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();

    // Eliminar del DOM después de ocultarse
    toastEl.addEventListener('hidden.bs.toast', () => {
      toastEl.remove();
    });
  }
});