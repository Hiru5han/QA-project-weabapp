
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.confirm-delete-form').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!confirm('Are you sure you want to delete this ticket?')) {
        event.preventDefault();
      }
    });
  });
});
