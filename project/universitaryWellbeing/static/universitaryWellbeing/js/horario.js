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

  // 2) Formateador de fecha/hora
  const fmt = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

  // 3) Inicializar FullCalendar
  let showWeekends = true;
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'timeGridWeek',
    locale: 'es',
    expandRows: true,
    stickyHeaderDates: true,

    allDaySlot: false,
    slotMinTime: "00:00:00",
    slotMaxTime: "24:00:00",
    slotDuration: "00:30:00",
    slotLabelInterval: "01:00",
    eventOverlap: true,
    weekends: showWeekends,

    height: "auto",
    headerToolbar: false,
    nowIndicator: true,
    navLinks: true,
    dayMaxEvents: true,

    events: eventos,

    eventMouseEnter: function(info) {
      let tt = document.querySelector('.fc-tooltip');
      if (!tt) {
        tt = document.createElement('div');
        tt.className = 'fc-tooltip';
        document.body.appendChild(tt);
      }
      const start = info.event.start ? fmt.format(info.event.start) : '';
      const end   = info.event.end ? fmt.format(info.event.end) : '';
      tt.innerHTML = `
        <div><strong>${info.event.title}</strong></div>
        ${start && end ? `<div>${start} &rarr; ${end}</div>` : ``}
        ${info.event.extendedProps?.notas ? `<div>${info.event.extendedProps.notas}</div>` : ``}
      `;
      tt.style.display = 'block';
      const move = (e) => { tt.style.left = (e.pageX + 12) + 'px'; tt.style.top = (e.pageY + 12) + 'px'; };
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

    dateClick: function(arg) { openDayModal(arg.date); },
    moreLinkClick: function(arg) { openDayModal(arg.date); return 'popover'; }
  });

  calendar.render();

  // --- Controles ---
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  const btnToday = document.getElementById('btn-today');
  const btnMonth = document.getElementById('btn-month');
  const btnWeek  = document.getElementById('btn-week');
  const btnDay   = document.getElementById('btn-day');
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
  if (btnMonth) btnMonth.addEventListener('click', () => { calendar.changeView('dayGridMonth'); setActiveView(btnMonth); });
  if (btnWeek)  btnWeek .addEventListener('click', () => { calendar.changeView('timeGridWeek'); setActiveView(btnWeek);  });
  if (btnDay)   btnDay  .addEventListener('click', () => { calendar.changeView('timeGridDay');  setActiveView(btnDay);   });

  if (btnWeekends) btnWeekends.addEventListener('click', () => {
    showWeekends = !showWeekends;
    calendar.setOption('weekends', showWeekends);
    btnWeekends.classList.toggle('active', showWeekends);
  });

  if (btnGo) btnGo.addEventListener('click', () => {
    const val = goDateInput && goDateInput.value;
    if (val) calendar.gotoDate(val);
  });

  // Modal por día
  function openDayModal(dateObj) {
    const startOfDay = new Date(dateObj); startOfDay.setHours(0,0,0,0);
    const endOfDay   = new Date(dateObj); endOfDay.setHours(23,59,59,999);

    const dayEvents = calendar.getEvents().filter(ev => {
      const evStart = ev.start || ev.extendedProps.start;
      const evEnd   = ev.end   || ev.extendedProps.end   || evStart;
      return (evStart <= endOfDay) && (evEnd >= startOfDay);
    }).sort((a,b) => (a.start || 0) - (b.start || 0));

    const titleDate = new Intl.DateTimeFormat('es-CO', { dateStyle: 'full' }).format(startOfDay);
    const titleEl = document.getElementById('dayModalLabel');
    if (titleEl) titleEl.textContent = `Eventos del ${titleDate}`;

    const list = document.getElementById('day-events-list');
    if (!list) return;

    if (dayEvents.length === 0) {
      list.innerHTML = `<p class="text-muted mb-0">No hay eventos para este día.</p>`;
    } else {
      list.innerHTML = dayEvents.map(ev => {
        const start = ev.start ? fmt.format(ev.start) : '';
        const end   = ev.end ? fmt.format(ev.end) : '';
        const notas = ev.extendedProps?.notas ? `<div class="text-muted">${ev.extendedProps.notas}</div>` : '';
        return `
          <div class="p-2 mb-2" style="border:1px solid #eee; border-radius:10px;">
            <div style="font-weight:700;">${ev.title}</div>
            ${start && end ? `<div>${start} &rarr; ${end}</div>` : ``}
            ${notas}
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
});
