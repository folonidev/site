document.addEventListener("DOMContentLoaded", function() {
  const el = document.querySelector('.animated-letters');
  const text = 'Desenvolvedor Backend Pleno';
  let i = 0;
  el.textContent = '';
  function type() {
    if (i < text.length) {
      el.textContent += text.charAt(i);
      i++;
      setTimeout(type, 80);
    }
  }
  type();
});