const scrollContent = document.querySelector('.scroll-content');
const leftBtn = document.querySelector('.left-btn');
const rightBtn = document.querySelector('.right-btn');

// Scroll amount (adjust as needed)
const scrollAmount = 300;

leftBtn.addEventListener('click', () => {
  scrollContent.scrollBy({
    left: -scrollAmount,
    behavior: 'smooth'
  });
});

rightBtn.addEventListener('click', () => {
  scrollContent.scrollBy({
    left: scrollAmount,
    behavior: 'smooth'
  });
});

// Optional: Disable buttons at scroll limits
scrollContent.addEventListener('scroll', () => {
  leftBtn.disabled = scrollContent.scrollLeft === 0;
  rightBtn.disabled = scrollContent.scrollLeft + scrollContent.clientWidth >= scrollContent.scrollWidth;
});