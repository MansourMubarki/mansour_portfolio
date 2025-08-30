(function(){
  // Show admin button when user presses Shift + A
  let visible = false;
  document.addEventListener('keydown', function(e){
    if(e.shiftKey && (e.key === 'A' || e.key === 'a')){
      visible = !visible;
      const b = document.getElementById('adminBtn');
      if(b) b.style.display = visible ? 'inline-block' : 'none';
    }
  });
})();
