
var Validate = {

    refreshList: function() {
      return function (result, status, xhr) {
        try {
          for (var i = 0; i < result.checkins.length; i++) {
            addRow(result.checkins[i]);
          }
          if (result.page_index > 1) {
            $("#previous-link").attr("href", "?page=" + (result.page_index - 1));
          } else {
            $("#previous-link").remove();
          }
          if (result.page_index < result.page_count) {
            console.log("Setting next to " + (result.page_index + 1));
            $("#next-link").attr("href", "?page=" + (result.page_index + 1));
          } else {
            $("#next-link").remove();
          }
          $("#page-description").text("Page " + result.page_index + " of " + result.page_count + ".");
          return "success";
        } catch (err) {
          return $.Deferred().fail(err);
        }
      }
    },

    addRow: function(checkin, even=true, updateSelect=true) {
        console.log('checkin URL: ' + checkin.checkin_url);
        $(".checkin-list").append(
            '<div class="row checkin-row checkin-' + (even ? 'even' : 'odd') + '" id="id_' + checkin.id + '_row" data-validation-id="' + checkin.id + '">' + "\n" +
            '<div class="col-xs-4 col-md-2"><em>' + checkin.player + "</em></div>\n" +
            '<div class="col-xs-8 col-md-6">' +
            '<a href="' + checkin.checkin_url + '" target="_blank">' +
            '<em>' + checkin.beer + ' from ' + checkin.brewery + '</em>' +
            "</a></div>\n" +
            '<div class="col-xs-12 col-md-4"><select id="id_' + checkin.id + '_select" class="beer-select" style="width: 100%;"></select></div>' + "\n" +
            '<div class="col-xs-2 col-md-2"><input type="checkbox">Trump</input></div>' +
            '<div class="col-xs-2 col-md-2"><input type="checkbox">Ballpark</input></div>' +
            '<div class="validation-buttons col-xs-offset-4 col-xs-2 col-md-offset-0 col-md-2"><button type="button" id="id_' + checkin.id + '_dbutton" class="btn dismissal-click">Dismiss</button></div>' + "\n" + 
            '<div class="validation-buttons col-xs-2 col-md-2"><button type="button" id="id_' + checkin.id + '_vbutton" class="btn btn-primary validation-click" disabled>Validate</button></div>' + "\n" + 
            "</div>\n"
        );
        let select = $('#id_' + checkin.id + '_select');
        if ('possible_id'  in checkin) {
            $('#id_' + checkin.id + '_vbutton').prop('disabled', false);
            select.append(
                '<option value="' + checkin.possible_id + '">' + 
                checkin.possible_name + 
                '</option>'
            );
        } else {
            select.append('<option></option>');
        }

        /*
        select.select2({ placeholder: "Select a beer or brewery", allowClear: true, data: exports.data });
        select.on("select2:select", exports.beerListOnSelect);
        select.on("select2:unselect", exports.beerListOnUnselect);
        $("#id_" + checkin.id + "_vbutton").click(exports.validationClick);
        $("#id_" + checkin.id + "_dbutton").click(exports.dismissalClick);
        */
    },

    enableValidate: function(e) {
        $(this).parents(".checkin-row").find(".validation-click").prop('disabled', false);
    },

    removeRow: function(uvId) {
        return function () {
            let row = $('#id_' + uvId + '_row');
            row.slideUp('slow');
            return row.promise().then( function() { $(this).remove(); } );
        }
    },

    disableValidate: function(e) {
        $(this).parents(".checkin-row").find(".validation-click").prop('disabled', true);
    },

    dismissalFunction: function(contest) {
        // Function associated with each dismissal button
        let that = this;
        return function() {
           let row = $(this).parents('.checkin-row'); 
           let uvId = $(row).data('validationId');
           console.log('Dismissing ' + uvId);
           contest.deleteUnvalidatedCheckin(uvId)
               .then(that.removeRow(uvId)).done();
        }
    },

    validationFunction: function(contest) {
        let that = this;
        return function() {
           let row = $(this).parents('.checkin-row'); 
           let uvId = $(row).data('validationId');
           console.log('Validating ' + uvId);
        }
    },
    
    displayCheckins: function(contest, page) {
        let start = 25 * (page - 1) + 1;
        let end = start + 25;
        let that = this;
        contest.getUnvalidatedCheckins(start, end)
            .then(function(data) {
                $('.checkin-list').html('');
                for (let i = 0; i < data.checkins.length; i++) {
                    that.addRow(data.checkins[i], i % 2 == 0);
                }
                /* Convert to select2 for dropdown */
                $(".beer-select").select2(
                    { placeholder: "Select a beer or brewery", 
                      allowClear: true, 
                      data: contest.selectData, 
                    });
                /* When a beer is selected, enable validation */
                $(".beer-select").on("select2:select", this.enableValidate);
                /* When a beer is unselected, disable validation */
                $(".beer-select").on("select2:unselect", this.disableValidate);
                /* When a validate button is clicked, submit the validation information */
                $(".validation-click").click(that.validationFunction(contest));
                /* When a dismissal is clicked, submit the dismissal information */
                $(".dismissal-click").click(that.dismissalFunction(contest));
                $(".step-links").html(function (i, oldHtml) {
                    let html = '';
                    if (data.page_index > 1) {
                        html = html + 
                            '<a href="#" onclick="Validate.displayCheckins(contest, ' + 
                            (data.page_index - 1) + 
                            ')">previous</a>' + "\n";
                    }
                    html = html + '<span id="page-description" closs="current">' +
                           'Page ' + data.page_index + ' of ' + data.page_count +
                           "</span>\n";
                    if (data.page_index < data.page_count) {
                        html = html + 
                            '<a href="#" onclick="Validate.displayCheckins(contest, ' + 
                            (data.page_index + 1) + 
                            ')">next</a>' + "\n";
                    }
                    return html;
                });
             });
    },
};

$(function() {
    csrfSafeMethod = function(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            let csrftoken = Cookies.get('csrftoken');
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    console.log('Finished validate.js');
});
