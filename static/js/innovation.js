  const video = document.getElementById('myVideo');
  const overlay = document.getElementById('overlay');

  overlay.addEventListener('click', () => {
    if (video.paused) {
      video.play();
      overlay.classList.add('paused');
    } else {
      video.pause();
      overlay.classList.remove('paused');
    }
  });