function applyFilters() {
  
  const category = document.getElementById('category').value;
  const onlyAvailable = document.getElementById('onlyAvailable').checked;

  console.log('Aplicando filtros:', { category, onlyAvailable });

  const modal = bootstrap.Modal.getInstance(document.getElementById('filterModal'));
  modal.hide();

  document.getElementById('search-results').innerHTML = `
    <div class="alert alert-info mt-3">Filtros aplicados: Categoría = ${category}, Solo disponibles = ${onlyAvailable}</div>
  `;
}
