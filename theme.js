// Apply dark/light theme based on localStorage
function applyTheme(mode){
    if(mode==='dark'){
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
  
  // Load theme from localStorage
  let savedTheme = localStorage.getItem('theme') || 'light';
  applyTheme(savedTheme);
  
  // Optional toggle button (dashboard only)
  document.addEventListener('click', e=>{
    if(e.target && e.target.id==='themeToggle'){
      savedTheme = savedTheme==='light'?'dark':'light';
      localStorage.setItem('theme', savedTheme);
      applyTheme(savedTheme);
      e.target.innerText = savedTheme==='dark'?'🌙 Dark':'☀️ Light';
    }
  });
  