document.addEventListener("DOMContentLoaded", function () {
    const slides = document.querySelectorAll(".noticia-slide");
    const nextBtn = document.getElementById("nextNoticia");
    const prevBtn = document.getElementById("prevNoticia");
    const slider = document.getElementById("noticiaSlider");
    let currentIndex = 0;
    const duration = 7000;
    const transition = 500;
    let interval;

    // Función para centrar botones en la mitad del SLIDER COMPLETO
    function centerButtons() {
        const activeSlide = document.querySelector(".noticia-slide.active");
        if (activeSlide && slider) {
            const sliderHeight = activeSlide.offsetHeight;
            const centerPosition = sliderHeight / 2;
            
            nextBtn.style.top = `${centerPosition}px`;
            prevBtn.style.top = `${centerPosition}px`;
        }
    }

    function showSlide(index) {
        slides.forEach((s, i) => {
            const bar = s.querySelector(".progress-bar");
            bar.style.transition = "none";
            bar.style.width = "0%";

            if (i === index) {
                s.classList.add("active");
                s.style.zIndex = 2;
            } else {
                s.classList.remove("active");
                s.style.zIndex = 1;
            }
        });

        const active = slides[index];
        const bar = active.querySelector(".progress-bar");
        setTimeout(() => {
            bar.style.transition = `width ${duration - transition}ms linear`;
            bar.style.width = "100%";
        }, 100);

        setTimeout(centerButtons, 100);
    }

    function nextSlide() {
        currentIndex = (currentIndex + 1) % slides.length;
        showSlide(currentIndex);
    }

    function prevSlide() {
        currentIndex = (currentIndex - 1 + slides.length) % slides.length;
        showSlide(currentIndex);
    }

    function startAuto() {
        interval = setInterval(nextSlide, duration);
    }

    function resetAuto() {
        clearInterval(interval);
        startAuto();
    }

    nextBtn.addEventListener("click", () => { nextSlide(); resetAuto(); });
    prevBtn.addEventListener("click", () => { prevSlide(); resetAuto(); });

    if (slides.length > 0) {
        showSlide(currentIndex);
        startAuto();
        
        window.addEventListener('load', centerButtons);
        window.addEventListener('resize', centerButtons);
        
        slides.forEach(slide => {
            const img = slide.querySelector('img');
            if (img) {
                img.addEventListener('load', centerButtons);
            }
        });
    }
});

// --- MODAL DE NOTICIAS ---
document.addEventListener("DOMContentLoaded", function () {
    const modal = new bootstrap.Modal(document.getElementById('noticiaModal'));
    const modalTitulo = document.getElementById('modalTitulo');
    const modalEnunciado = document.getElementById('modalEnunciado');
    const modalDescripcion = document.getElementById('modalDescripcion');
    const modalImagen = document.getElementById('modalImagen');
    const modalFecha = document.getElementById('modalFecha');
    const modalAutor = document.getElementById('modalAutor');

    document.querySelectorAll('.ver-mas').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const slide = e.target.closest('.noticia-slide');
            
            // Rellenar modal con datos
            modalTitulo.textContent = slide.dataset.titulo;
            modalEnunciado.textContent = slide.dataset.enunciado;
            let descripcion = slide.dataset.descripcion || '';
            descripcion = descripcion.split('\n\n').map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
            modalDescripcion.innerHTML = descripcion;
            modalImagen.src = slide.dataset.imagen;
            
            // Formatear fecha y autor
            modalFecha.querySelector('span').textContent = slide.dataset.fecha;
            modalAutor.querySelector('span').textContent = slide.dataset.autor;
            
            modal.show();
        });
    });
});
