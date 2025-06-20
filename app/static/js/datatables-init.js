document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('tickets-table')) {
    $('#tickets-table').DataTable({
      responsive: true,
      paging: true,
      ordering: true,
      info: true,
      searching: true,
      lengthMenu: [5, 10, 25, 50, 100],
      pageLength: 5,
      columnDefs: [{ targets: -1, width: '220px' }]
    });

    $('.dataTables_filter input')
      .attr('placeholder', 'Search across all categories...')
      .css({ color: 'grey', width: '250px' });
  }
});
