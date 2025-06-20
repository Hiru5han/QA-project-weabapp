function displayFileName() {
  const input = document.getElementById('profile_image');
  const fileName = input.files.length > 0 ? input.files[0].name : 'No file selected';
  document.getElementById('file-name').textContent = fileName;
}

document.addEventListener('DOMContentLoaded', function () {
  const profileInput = document.getElementById('profile_image');
  const chooseFileButton = document.getElementById('chooseFile');
  if (profileInput) {
    profileInput.addEventListener('change', displayFileName);
  }
  if (chooseFileButton && profileInput) {
    chooseFileButton.addEventListener('click', function () {
      profileInput.click();
    });
  }

  const passwordInput = document.getElementById('password');
  const lengthCriteria = document.getElementById('length');
  const numberCriteria = document.getElementById('number');
  const uppercaseCriteria = document.getElementById('uppercase');
  const lowercaseCriteria = document.getElementById('lowercase');
  const specialCriteria = document.getElementById('special');
  const togglePassword = document.getElementById('togglePassword');

  if (passwordInput) {
    passwordInput.addEventListener('input', function () {
      const password = passwordInput.value;

      if (password.length >= 8) {
        lengthCriteria.classList.add('valid');
        lengthCriteria.classList.remove('invalid');
        lengthCriteria.innerHTML = '✓ 8 characters minimum';
      } else {
        lengthCriteria.classList.add('invalid');
        lengthCriteria.classList.remove('valid');
        lengthCriteria.innerHTML = '✗ 8 characters minimum';
      }

      if (/\d/.test(password)) {
        numberCriteria.classList.add('valid');
        numberCriteria.classList.remove('invalid');
        numberCriteria.innerHTML = '✓ One number';
      } else {
        numberCriteria.classList.add('invalid');
        numberCriteria.classList.remove('valid');
        numberCriteria.innerHTML = '✗ One number';
      }

      if (/[A-Z]/.test(password)) {
        uppercaseCriteria.classList.add('valid');
        uppercaseCriteria.classList.remove('invalid');
        uppercaseCriteria.innerHTML = '✓ One uppercase letter';
      } else {
        uppercaseCriteria.classList.add('invalid');
        uppercaseCriteria.classList.remove('valid');
        uppercaseCriteria.innerHTML = '✗ One uppercase letter';
      }

      if (/[a-z]/.test(password)) {
        lowercaseCriteria.classList.add('valid');
        lowercaseCriteria.classList.remove('invalid');
        lowercaseCriteria.innerHTML = '✓ One lowercase letter';
      } else {
        lowercaseCriteria.classList.add('invalid');
        lowercaseCriteria.classList.remove('valid');
        lowercaseCriteria.innerHTML = '✗ One lowercase letter';
      }

      if (/[!@#$%^&*()_+\-=[\]{}|;:,.<>?/]/.test(password)) {
        specialCriteria.classList.add('valid');
        specialCriteria.classList.remove('invalid');
        specialCriteria.innerHTML = '✓ One special character !@#$%^&*()_+-=[]{}|;:,.<>?/';
      } else {
        specialCriteria.classList.add('invalid');
        specialCriteria.classList.remove('valid');
        specialCriteria.innerHTML = '✗ One special character !@#$%^&*()_+-=[]{}|;:,.<>?/';
      }
    });
  }

  if (togglePassword) {
    togglePassword.addEventListener('click', function () {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      this.textContent = type === 'password' ? 'Show' : 'Hide';
    });
  }
});
