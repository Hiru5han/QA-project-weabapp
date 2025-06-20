document.addEventListener('DOMContentLoaded', function () {
  const backButton = document.getElementById('back-button');
  const allTicketsUrlElement = document.getElementById('allTicketsUrl');

  function goBack(event) {
    if (event) event.preventDefault();
    const previousPageUrl = sessionStorage.getItem('previousPageUrl');
    const fallbackUrl = allTicketsUrlElement ? allTicketsUrlElement.value : '/';
    if (previousPageUrl) {
      window.location.href = previousPageUrl;
    } else {
      window.location.href = fallbackUrl;
    }
  }

  if (backButton) {
    backButton.addEventListener('click', goBack);
  }

  if (!sessionStorage.getItem('previousPageUrl')) {
    sessionStorage.setItem('previousPageUrl', document.referrer);
  }

  const statusBadge = document.getElementById('status-badge');
  if (statusBadge) {
    statusBadge.addEventListener('click', function () {
      const myModal = new bootstrap.Modal(document.getElementById('statusModal'));
      myModal.show();
    });
  }

  const priorityBadge = document.getElementById('priority-badge');
  if (priorityBadge) {
    priorityBadge.addEventListener('click', function () {
      const myModal = new bootstrap.Modal(document.getElementById('priorityModal'));
      myModal.show();
    });
  }

  const assigneeBadge = document.getElementById('assignee-badge');
  if (assigneeBadge) {
    assigneeBadge.addEventListener('click', function () {
      const myModal = new bootstrap.Modal(document.getElementById('assigneeModal'));
      myModal.show();
    });
  }

  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
