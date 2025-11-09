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
            // Obtener altura total del slider
            const sliderHeight = activeSlide.offsetHeight;
            const centerPosition = sliderHeight / 2;
            
            nextBtn.style.top = `${centerPosition}px`;
            prevBtn.style.top = `${centerPosition}px`;
            
            console.log('Slider height:', sliderHeight, 'Center:', centerPosition);
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

        // Centrar botones después de que el slide esté visible
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
        
        // Recentrar al cargar imágenes y redimensionar
        window.addEventListener('load', centerButtons);
        window.addEventListener('resize', centerButtons);
        
        // Recentrar cuando todas las imágenes carguen
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
    const modalDescripcion = document.getElementById('modalDescripcion');
    const modalImagen = document.getElementById('modalImagen');
    const modalFecha = document.getElementById('modalFecha');
    const modalAutor = document.getElementById('modalAutor');

    document.querySelectorAll('.ver-mas').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const slide = e.target.closest('.noticia-slide');
            modalTitulo.textContent = slide.dataset.titulo;
            modalDescripcion.textContent = slide.dataset.descripcion;
            modalImagen.src = slide.dataset.imagen;
            modalFecha.textContent = `📅 Publicado el ${slide.dataset.fecha}`;
            modalAutor.textContent = `✍️ Autor: ${slide.dataset.autor}`;
            modal.show();
        });
    });
});
