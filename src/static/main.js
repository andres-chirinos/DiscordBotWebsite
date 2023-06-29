 
ThemeSwitch(1);

function ThemeSwitch(a) {
    if (localStorage.getItem("Theme") == 'light' && a==null) {
        localStorage.setItem("Theme", 'dark')
    } else if (a==null) {
        localStorage.setItem("Theme", 'light')
    }
    document.documentElement.setAttribute('data-bs-theme', localStorage.getItem("Theme"))
}

function irArriba(){
  $('body').animate({ scrollTop:'0px' },1000);
}

console.log('loaded');