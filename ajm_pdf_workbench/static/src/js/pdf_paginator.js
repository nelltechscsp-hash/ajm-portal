/** @odoo-module **/

// Paginador automático para cartas con cabecera y pie fijos
// Divide el contenido en páginas A4, repitiendo header y footer en cada una

document.addEventListener('DOMContentLoaded', function() {
    function paginateLetter() {
        const pageHeight = 1122; // px, aprox. 297mm @ 96dpi
        const header = document.querySelector('.ajm-pdf-header-fixed');
        const footer = document.querySelector('.ajm-pdf-footer-fixed');
        const content = document.querySelector('.ajm-pdf-content');
        if (!header || !footer || !content) return;

        // Unwrap all pages if already paginated
        const container = content.parentElement.parentElement;
        let pages = container.querySelectorAll('.ajm-pdf-page');
        if (pages.length > 1) {
            // Solo dejar la primera, limpiar las demás
            for (let i = 1; i < pages.length; i++) {
                pages[i].remove();
            }
        }

        // Clonar header/footer para nuevas páginas
        const headerHTML = header.outerHTML;
        const footerHTML = footer.outerHTML;

        // Extraer el contenido a paginar
        const contentHTML = content.innerHTML;
        content.innerHTML = '';

        // Crear un div temporal para medir
        const tempDiv = document.createElement('div');
        tempDiv.style.position = 'absolute';
        tempDiv.style.visibility = 'hidden';
        tempDiv.style.width = 'calc(210mm - 20mm)';
        tempDiv.innerHTML = contentHTML;
        document.body.appendChild(tempDiv);

        // Fragmentar el contenido en páginas
        let currentPage, currentContent;
        let childNodes = Array.from(tempDiv.childNodes);
        let i = 0;
        while (i < childNodes.length) {
            // Crear nueva página
            currentPage = document.createElement('div');
            currentPage.className = 'ajm-pdf-page';
            currentPage.innerHTML = headerHTML + '<div class="ajm-pdf-content"></div>' + footerHTML;
            currentContent = currentPage.querySelector('.ajm-pdf-content');
            container.appendChild(currentPage);

            // Llenar la página hasta el límite
            let pageContentHeight = 0;
            while (i < childNodes.length) {
                currentContent.appendChild(childNodes[i].cloneNode(true));
                pageContentHeight = currentContent.offsetHeight;
                if (pageContentHeight > (pageHeight - header.offsetHeight - footer.offsetHeight - 40)) {
                    // Si se pasa, quitar el último y pasar a la siguiente página
                    currentContent.removeChild(currentContent.lastChild);
                    break;
                }
                i++;
            }
        }
        tempDiv.remove();
        // Ocultar la página original
        pages = container.querySelectorAll('.ajm-pdf-page');
        if (pages.length > 1) {
            pages[0].style.display = 'none';
        }
    }

    // Ejecutar al cargar y al agregar contenido dinámico
    setTimeout(paginateLetter, 500);
    document.addEventListener('input', paginateLetter);
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'add-driver-btn' || e.target.id === 'add-commodity-btn' || e.target.id === 'add-unit-btn')) {
            setTimeout(paginateLetter, 300);
        }
    });
});
