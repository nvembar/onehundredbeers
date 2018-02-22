
var EditContest = {

  clearErrorStyling: function() {
    // Clear any styling from errors
    $('.alert-for-modal').empty();
    $('.alert-for-tab').empty();
    $('div.modal-body div.form-group.has-error').removeClass('has-error');
    $('div.form-group span.help-block').remove();
  },

  clearFormData: function() {
    $('div.modal-body div.form-group input.form-control').val('');
  },

  setAlert: function(selector, alertText, isError) {
    let style = isError ? 'alert-danger' : 'alert-success';
    selector.find('.alert-for-modal').html(
      '<div class="alert ' + style + '" role="alert">' + alertText + '</div>');
  },

  addToContestFromForm: function(contest, 
                                 fn, 
                                 keys, 
                                 selector, 
                                 nameKey='name', 
                                 transform={}) {
    EditContest.clearErrorStyling();
    let data = {};
    for (let k of keys) {
      if (k in transform) {
        data[k] = transform[k](selector.find('#' + k).val());
      } else {
        data[k] = selector.find('#' + k).val();
      }
    }
    let promise = fn.call(contest, data);
    return promise.then(
      function () {
        EditContest.setAlert(selector, 'Added ' + data[nameKey], false);
      }
    ).fail(function(jqXHR) {
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
            let formGroup = selector.find('#' + k).parent('.form-group');
            formGroup.addClass('has-error');
            formGroup.append('<span class="help-block">' + response[k] + '</span>');
          }
        }
        EditContest.setAlert(selector, alertText, true);
    });
  },

  displayBeers: function(contest) {
    contest.loadBeers(function (beers) {
      console.log('Loaded beers');
      $('.beer-list').html(Handlebars.templates.beer_table(contest));
    });
  },

  displayBreweries: function(contest) {
    contest.loadBreweries(function (breweries) {
      console.log('Loaded breweries');
      $('.brewery-list').html(Handlebars.templates.brewery_table(contest));
    });
  },

  displayBonuses: function(contest) {
    contest.loadBonuses(function (bonuses) {
      console.log('Loaded bonuses');
      $('.bonus-list').html(Handlebars.templates.bonus_table(contest));
    });
  },

  addBeerFromForm: function(contest) {
    console.log('In addBeerFromForm');
    let keys = ['name', 'brewery', 'brewery_url', 'untappd_url', 'point_value'];
    // We only proess the challenge information if the challenge checkbox is checked
    if ($('#is-beer-challenge').is(':checked')) {
      keys.push('challenger', 'challenge_point_value', 
                'challenge_point_loss', 'max_point_loss');
    }
    EditContest.addToContestFromForm(contest, contest.addBeer, 
                                     keys, $('#addBeer')).done(
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

  populateBeerFromLookup: function (contest) {
    let untappdUrl = $('#addBeer #untappd_url').val();
    $('#lookup_beer').prop('disabled', true);
    return contest.lookupBeer(untappdUrl).then(
      function (beer) {
        $('#addBeer #untappd_url').val(beer['untappd_url']);
        $('#addBeer #name').val(beer['name']);
        $('#addBeer #brewery').val(beer['brewery']);
        $('#addBeer #brewery_url').val(beer['brewery_url']);
      }
    ).fail(
      function (jqXHR) {
        errorData = JSON.parse(jqXHR.responseText);
        $('#alert-for-beer-modal').html('<div class="alert alert-danger">Invalid Untappd Beer URL:' + errorData['non_field_errors'][0] + '</div>');
      }
    ).always(
      function () {
        $('#lookup_beer').prop('disabled', false);
      }
    );
  },

  addBreweryFromForm: function(contest) {
    console.log('In addBreweryFromForm');
    let keys = ['name', 'location', 'untappd_url', 'point_value'];
    EditContest.addToContestFromForm(contest, contest.addBrewery, 
                                     keys, $('#addBrewery')).done(
            function () { 
              EditContest.displayBreweries(contest); 
              EditContest.clearFormData();
            });
  },

  removeBreweryFromContest: function (contest, breweryId) {
    return contest.deleteBrewery(breweryId).then(
      function () { 
        $('#brewery-' + breweryId).fadeOut();
        return $('#brewery-' + breweryId).promise();
      }
    ).then(
      function () { return EditContest.displayBreweries(contest); }
    ).fail(
      function (jqXHR) {
        $('#alert-for-brewery').html('<div class="alert alert-danger">Error deleting brewery' + jqXHR.responseText + '</div>')
      }
    );
  },

  populateBreweryFromLookup: function (contest) {
    let untappdUrl = $('#addBrewery #untappd_url').val();
    $('#lookup_brewery').prop('disabled', true);
    return contest.lookupBrewery(untappdUrl).then(
      function (brewery) {
        $('#addBrewery #untappd_url').val(brewery['untappd_url']);
        $('#addBrewery #name').val(brewery['name']);
        $('#addBrewery #location').val(brewery['location']);
      }
    ).fail(
      function (jqXHR) {
        errorData = JSON.parse(jqXHR.responseText);
        $('#alert-for-brewery-modal').html('<div class="alert alert-danger">Invalid Untappd Brewery URL:' + errorData['non_field_errors'][0] + '</div>');
      }
    ).always(
      function () {
        $('#lookup_brewery').prop('disabled', false);
      }
    );
  },

  addBonusFromForm: function(contest) {
    console.log('In addBonusFromForm');
    let keys = ['name', 'description', 'hash_tags', 'point_value'];
    let transform = { hash_tags: s => s.split(',').map(t => t.trim()) }
    EditContest.addToContestFromForm(contest, contest.addBonus, 
                                     keys, $('#addBonus'), 'name', transform).done(
            function () { 
              EditContest.displayBonuses(contest); 
              EditContest.clearFormData();
            });
  },

  removeBonusFromContest: function (contest, bonusId) {
    return contest.deleteBonus(bonusId).then(
      function () { 
        $('#bonus-' + bonusId).fadeOut();
        return $('#bonus-' + bonusId).promise();
      }
    ).then(
      function () { return EditContest.displayBonuses(contest); }
    ).fail(
      function (jqXHR) {
        $('#alert-for-bonus').html('<div class="alert alert-danger">Error deleting bonus ' + jqXHR.responseText + '</div>')
      }
    );
  },
};

