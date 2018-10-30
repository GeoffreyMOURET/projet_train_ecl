function editer() {
	$(last_name).hide();
	$(form_last_name).show();
	$(first_name).hide();
	$(form_first_name).show();
	$(statut).hide();
	$(form_statut).show();
	$(reduction).hide();
	$(form_reduction).show();
	$(email).hide();
	$(form_email).show();
	$(bouton_editer).hide();
	$(bouton_valider).show();
	
}

function valider() {
$(form).submit();

}

$(body).keyup(function(e) {    
   if(e.keyCode == 13) { 
          $(form).submit();
 }
});
