function reserver(k) {
k.parentElement.parentElement.parentElement.submit();

}


function submit() {
form = $(form)[0];
for(var i=0; i < form.elements.length; i++){
	      if(form.elements[i].value === '' && form.elements[i].hasAttribute('required')){
			form.elements[i].style.border = "2px solid #f00";
		        return false;
	      } else {
			
		}
	}
form.submit();
}

