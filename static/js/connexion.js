

var form_actif = 1;

$(body).keyup(function(e) {    
   if(e.keyCode == 13) { 
          submit(form_actif);
 }
});


$( function() {
		$(formulaire1).show(500);
	}
);

function changer_form(k) {
	if (k == 1) {
		$(formulaire2).hide(500,complete = complete1);
		function complete1() {
			$(formulaire1).show(500);
			form_actif = 1;
		}
	}
	else {
			$(formulaire1).hide(500,complete = complete2);
		function complete2() {
			$(formulaire2).show(500);
			form_actif = 2;
		}
	}

}

function submit(k) {
	if (k==1) {
		form = $(form1)[0];
	}
	else {
		form = $(form2)[0];
	}
	for(var i=0; i < form.elements.length; i++){
	      if(form.elements[i].value === '' && form.elements[i].hasAttribute('required')){
			form.elements[i].style.border = "2px solid #f00";
		        return false;
	      } else {
			
		}
	}
	form.submit();
}
