document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');

  // 1) Cargar eventos (reglas semanales) desde el script JSON embebido
  let EVENTS = [];
  try {
    const raw = document.getElementById('events-data')?.textContent || '[]';
    EVENTS = JSON.parse(raw);
  } catch (e) {
    console.error('Eventos JSON inválido:', e);
  }

  // 2) Formateador para tooltips y modal
  const fmt = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

  // 3) Inicializar calendario
  let showWeekends = true;
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'timeGridWeek',
    locale: 'es',
    firstDay: 1,                 // Lunes
    height: 'auto',
    headerToolbar: false,
    expandRows: true,
    stickyHeaderDates: true,
    allDaySlot: false,
    slotMinTime: '06:00:00',
    slotMaxTime: '22:30:00',
    slotDuration: '00:30:00',
    slotLabelInterval: '01:00',
    weekends: showWeekends,
    nowIndicator: true,
    navLinks: true,
    dayMaxEvents: true,

    // Eventos con reglas semanales (daysOfWeek, startTime, endTime)
    events: EVENTS,

    // Tooltip al pasar el mouse
    eventMouseEnter: function(info) {
      let tt = document.querySelector('.fc-tooltip');
      if (!tt) {
        tt = document.createElement('div');
        tt.className = 'fc-tooltip';
        document.body.appendChild(tt);
      }

      // Para eventos recurrentes, FullCalendar materializa start/end en la semana visible
      const start = info.event.start ? fmt.format(info.event.start) : '';
      const end   = info.event.end   ? fmt.format(info.event.end)   : '';
      const p     = info.event.extendedProps || {};

      tt.innerHTML = `
        <div><strong>${info.event.title}</strong></div>
        ${start && end ? `<div>${start} &rarr; ${end}</div>` : ``}
        ${p.tipo     ? `<div><b>Tipo:</b> ${p.tipo}</div>` : ``}
        ${p.profesor ? `<div><b>Profesor:</b> ${p.profesor}</div>` : ``}
        ${p.espacio  ? `<div><b>Espacio:</b> ${p.espacio}</div>` : ``}
        ${p.descripcion ? `<div class="text-muted">${p.descripcion}</div>` : ``}
      `;
      tt.style.position = 'absolute';
      tt.style.zIndex = '9999';
      tt.style.pointerEvents = 'none';
      tt.style.display = 'block';

      const move = (e) => {
        tt.style.left = (e.pageX + 12) + 'px';
        tt.style.top  = (e.pageY + 12) + 'px';
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

    // Click en un evento: llenamos el modal con detalle de ese evento
    eventClick: function(info) {
      const e = info.event;
      const p = e.extendedProps || {};
      const start = e.start ? fmt.format(e.start) : '';
      const end   = e.end   ? fmt.format(e.end)   : '';

      const html = `
        <div class="p-2">
          <div class="fc-modal-row" style="font-weight:700;">${e.title}</div>
          ${start && end ? `<div class="fc-modal-row">${start} &rarr; ${end}</div>` : ''}
          ${p.tipo ? `<div class="fc-modal-row"><b>Tipo:</b> ${p.tipo}</div>` : ''}
          ${p.profesor ? `<div class="fc-modal-row"><b>Profesor:</b> ${p.profesor}</div>` : ''}
          ${p.espacio ? `<div class="fc-modal-row"><b>Espacio:</b> ${p.espacio}</div>` : ''}
          ${p.descripcion ? `<div class="fc-modal-row"><b>Descripción:</b> ${p.descripcion}</div>` : ''}
        </div>
      `;
      const list = document.getElementById('day-events-list');
      if (list) list.innerHTML = html;
      const modalEl = document.getElementById('dayModal');
      if (modalEl && window.bootstrap?.Modal) {
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
      }
    },

    // Click en celda de día/hora: abrimos modal con todos los eventos de ese día
    dateClick: function(arg) { openDayModal(arg.date); },
    moreLinkClick: function(arg) { openDayModal(arg.date); return 'popover'; }
  });

  calendar.render();

  // --- Controles de navegación y vistas ---
  const btnPrev   = document.getElementById('btn-prev');
  const btnNext   = document.getElementById('btn-next');
  const btnToday  = document.getElementById('btn-today');
  const btnMonth  = document.getElementById('btn-month');
  const btnWeek   = document.getElementById('btn-week');
  const btnDay    = document.getElementById('btn-day');
  const btnWknds  = document.getElementById('btn-weekends');
  const goDateInp = document.getElementById('go-date');
  const btnGo     = document.getElementById('btn-go');

  if (btnPrev)  btnPrev .addEventListener('click', () => calendar.prev());
  if (btnNext)  btnNext .addEventListener('click', () => calendar.next());
  if (btnToday) btnToday.addEventListener('click', () => calendar.today());

  function setActiveView(btn) {
    [btnMonth, btnWeek, btnDay].forEach(b => b && b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }
  if (btnMonth) btnMonth.addEventListener('click', () => { calendar.changeView('dayGridMonth'); setActiveView(btnMonth); });
  if (btnWeek)  btnWeek .addEventListener('click', () => { calendar.changeView('timeGridWeek'); setActiveView(btnWeek);  });
  if (btnDay)   btnDay  .addEventListener('click', () => { calendar.changeView('timeGridDay');  setActiveView(btnDay);   });

  if (btnWknds) btnWknds.addEventListener('click', () => {
    showWeekends = !showWeekends;
    calendar.setOption('weekends', showWeekends);
    btnWknds.classList.toggle('active', showWeekends);
  });

  if (btnGo) btnGo.addEventListener('click', () => {
    const val = goDateInp && goDateInp.value;
    if (val) calendar.gotoDate(val);
  });

  // --- Modal por día (lista todos los eventos de esa fecha) ---
  function openDayModal(dateObj) {
    const startOfDay = new Date(dateObj); startOfDay.setHours(0,0,0,0);
    const endOfDay   = new Date(dateObj); endOfDay.setHours(23,59,59,999);

    const dayEvents = calendar.getEvents()
      .filter(ev => {
        const evStart = ev.start || ev.extendedProps.start;
        const evEnd   = ev.end   || ev.extendedProps.end || evStart;
        return (evStart && evEnd && evStart <= endOfDay && evEnd >= startOfDay);
      })
      .sort((a,b) => (a.start || 0) - (b.start || 0));

    const titleDate = new Intl.DateTimeFormat('es-CO', { dateStyle: 'full' }).format(startOfDay);
    const titleEl = document.getElementById('dayModalLabel');
    if (titleEl) titleEl.textContent = `Eventos del ${titleDate}`;

    const list = document.getElementById('day-events-list');
    if (!list) return;

    if (dayEvents.length === 0) {
      list.innerHTML = `<p class="text-muted mb-0">No hay eventos para este día.</p>`;
    } else {
      list.innerHTML = dayEvents.map(ev => {
        const p = ev.extendedProps || {};
        const start = ev.start ? fmt.format(ev.start) : '';
        const end   = ev.end   ? fmt.format(ev.end)   : '';
        return `
          <div class="p-2 mb-2" style="border:1px solid #eee; border-radius:10px;">
            <div style="font-weight:700;">${ev.title}</div>
            ${start && end ? `<div>${start} &rarr; ${end}</div>` : ``}
            ${p.tipo ? `<div><b>Tipo:</b> ${p.tipo}</div>` : ``}
            ${p.profesor ? `<div><b>Profesor:</b> ${p.profesor}</div>` : ``}
            ${p.espacio ? `<div><b>Espacio:</b> ${p.espacio}</div>` : ``}
            ${p.descripcion ? `<div class="text-muted">${p.descripcion}</div>` : ``}
          </div>
        `;
      }).join('');
    }

    const modalEl = document.getElementById('dayModal');
    if (modalEl && window.bootstrap?.Modal) {
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
  }
});