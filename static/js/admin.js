
function submit() {
	form = $(form)[0];
	console.log(form);
	for(var i=0; i < form.elements.length; i++){
		      if(form.elements[i].value === '' && form.elements[i].hasAttribute('required')){
				form.elements[i].style.border = "2px solid #f00";
				return false;
		      } else {
			
			}
		}
	form.submit();
}



function add_gare() {
	liste_gare = $('#liste_gare');

	div = document.createElement('div');
	div.className = 'block_gare';

	input = document.createElement('input');
	input_heure = document.createElement('input');
	input_date = document.createElement('input');

	input.placeholder = 'Gare';
	label = liste_gare.append(div)[0];
	div = label.lastChild;

	div.append(input);
	input = div.lastChild;
	$(input).attr('list','gare').attr('type','text').attr('name','gares').attr('autocomplete','off');

	div.append(input_date);
	input = div.lastChild;
	$(input).attr('name','dates').attr('type','date').attr('autocomplete','off');

	div.append(input_heure);
	input = div.lastChild;
	$(input).attr('name','heures').attr('type','time').attr('autocomplete','off');

}

function add_voiture() {
	liste_voiture = $('#liste_voiture');

	div = document.createElement('div');
	div.className = 'block_gare';

	input = document.createElement('input');

	input.placeholder = 'Nombre de places';
	label = liste_voiture.append(div)[0];
	div = label.lastChild;

	div.append(input);
	input = div.lastChild;
	$(input).attr('type','number').attr('name','voitures');
 
}


function submit_2() {
	var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();
	form = $('#form_2');
	numero = $('#numero_billet')[0];
	agence = $('#agence_billet')[0];
	console.log(agence);
        $.ajax({

            type: 'POST',

            url: form[0].action,

            data: {csrfmiddlewaretoken:csrftoken, numero_billet:numero.value, agence:agence.value},

            timeout: 3000,

            success: function(data){
		$('.erreur').hide();
		$('#apercu').show();
		$('#billet_numero').html(data['numero']);
		$('#billet_gare_depart').html(data['gare_depart']);
		$('#billet_gare_depart_2').html(data['gare_depart']);
		$('#billet_gare_arrivee').html(data['gare_arrivee']);
		$('#billet_gare_arrivee_2').html(data['gare_arrivee']);
		$('#billet_date_depart').html(data['date_depart']);
		$('#billet_date_depart_2').html(data['date_depart']);
		$('#billet_date_arrivee_2').html(data['date_arrivee']);
		$('#billet_heure_depart').html(data['heure_depart']);
		$('#billet_heure_depart_2').html(data['heure_depart']);
		$('#billet_heure_arrivee_2').html(data['heure_arrivee']);
		$('#billet_prix').html(data['prix']+' €');
		$('#billet_voiture').html(data['voiture']);
		$('#billet_place').html(data['place']);
		$('#billet_reduction').html(data['reduction']);
		if (data['payee'] == 0) {
			$('#payee').attr('class','non_payee');
			$('#payee').html('Non payée');
			$('#valider_paiement').show();
			
		}
		else {
			$('#payee').attr('class','payee');
			$('#payee').html('Payée');
			$('#valider_paiement').hide();
		}
		$('#numero_paiement').attr('value',data['numero_billet']);
		
		$('#agence_paiement').attr('value',data['agence']);
		

            }
	}
	)
}

function submit_3() {
$('#form_3')[0].submit()
}



