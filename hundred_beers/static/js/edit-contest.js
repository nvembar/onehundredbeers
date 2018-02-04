
var EditContest = {

  displayBeers: function(contest) {
    contest.loadBeers(function (beers) {
      console.log('Loaded beers');
      console.log(JSON.stringify(contest, null, 2));
      $('.beer-list').html(Handlebars.templates.beer_table(contest));
    });
  },

  clearErrorStyling: function() {
    // Clear any styling from errors
    $('#alert-for-modal').empty();
    $('.alert-for-tab').empty();
    $('div.modal-body div.form-group.has-error').removeClass('has-error');
    $('div.form-group span.help-block').remove();
  },

  clearFormData: function() {
    $('div.modal-body div.form-group input.form-control').val('');
  },

  setAlert: function(alertText, isError) {
    let style = isError ? 'alert-danger' : 'alert-success';
    $('#alert-for-modal').html(
      '<div class="alert ' + style + '" role="alert">' + alertText + '</div>');
  },

  addToContestFromForm: function(contest, fn, keys, nameKey) {
    console.log('In addBeerFromForm');
    EditContest.clearErrorStyling();
    let data = {};
    for (let k of keys) {
      data[k] = document.getElementById(k).value;
    }
    let promise = fn.call(contest, data);
    return promise.then(
      function () {
        EditContest.setAlert('Added ' + data[nameKey], false);
      }
    ).fail(function(jqXHR) {
        console.log('Failed to add beer');
        console.log(jqXHR.responseText);
        alertText = 'Failed to add ' + data[nameKey];
        response = JSON.parse(jqXHR.responseText);
        for (let k in response) {
          if (!response.hasOwnProperty(k)) {
            continue;
          }
          if (k === 'non_field_errors') {
            alertText += "<ul>\n";
            for (let e of response['non_field_errors']) {
              alertText += "<li>" + e + "</li>\n"; 
            }
            alertText += "</ul>\n";
          } else {
            let formGroup = $('#' + k).parent('.form-group');
            formGroup.addClass('has-error');
            formGroup.append('<span class="help-block">' + response[k] + '</span>');
          }
        }
        EditContest.setAlert(alertText, true);
    });
  },

  addBeerFromForm: function(contest) {
    console.log('In addBeerFromForm');
    let keys = ['name', 'brewery', 'brewery_state', 'untappd_url', 'point_value'];
    EditContest.addToContestFromForm(contest, contest.addBeer, keys, 'name').done(
            function () { 
              EditContest.displayBeers(contest); 
              EditContest.clearFormData();
            });
  },

  removeBeerFromContest: function (contest, beerId) {
    return contest.deleteBeer(beerId).then(
      function () { 
        $('#beer-' + beerId).fadeOut();
        return $('#beer-' + beerId).promise();
      }
    ).then(
      function () { return EditContest.displayBeers(contest); }
    ).fail(
      function (jqXHR) {
        $('#alert-for-beer').html('<div class="alert alert-danger">Error deleting beer ' + jqXHR.responseText + '</div>')
      }
    );
  },

};

