
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
        $(".checkin-list").append(
            '<div class="row checkin-row checkin-' + (even ? 'even' : 'odd') + '" id="id_' + checkin.id + '_row" data-validation-id="' + checkin.id + '">' + "\n" +
            '<div class="col-xs-4 col-md-2"><em>' + checkin.player + "</em></div>\n" +
            '<div class="col-xs-8 col-md-6">' +
            '<a href="' + checkin.checkin_url + '" target="_blank">' +
            '<em>' + checkin.beer + ' from ' + checkin.brewery + '</em>' +
            "</a></div>\n" +
            '<div class="col-xs-12 col-md-4"><select id="id_' + checkin.id + '_select" class="beer-select" style="width: 100%;"></select></div>' + "\n" +
            '<div class="col-xs-2 col-md-2"><input id="id_' + checkin.id + '_trump" data-bonus-type="trump" class="bonus-checkbox" type="checkbox">Trump</input></div>' +
            '<div class="col-xs-2 col-md-2"><input id="id_' + checkin.id + '_ballpark" data-bonus-type="ballpark" class="bonus-checkbox" type="checkbox">Ballpark</input></div>' +
            '<div class="validation-buttons col-xs-4 col-md-offset-0 col-md-2"><button type="button" id="id_' + checkin.id + '_dbutton" class="btn dismissal-click">Dismiss</button></div>' + "\n" + 
            '<div class="validation-buttons col-xs-4 col-md-2"><button type="button" id="id_' + checkin.id + '_vbutton" class="btn btn-primary validation-click" disabled>Validate</button></div>' + "\n" + 
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

    determineValidateState: function(e) {
        console.log('Detemrmining Validate State for ' + this);
        row = $(this).parents('.checkin-row');
        console.log('Selection: ' + $(row).find('.beer-select option:selected').val());
        let selected = $(row).find('.beer-select option:selected').val();
        $(row).find('.validation-click').prop('disabled', 
            !($(row).find('.beer-select option:selected').val() ||
                $(row).find('.bonus-checkbox:checked').length > 0));
    },

    removeRow: function(contest, uvId) {
        return function () {
            let row = $('#id_' + uvId + '_row');
            row.slideUp('slow');
            return row.promise().then( function() { $(this).remove(); } );
        }
    },

    dismissalFunction: function(contest) {
        // Function associated with each dismissal button
        let that = this;
        return function() {
           let row = $(this).parents('.checkin-row'); 
           let uvId = $(row).data('validationId');
           let checkins = $('.checkin-list');
           let currentPage = $(checkins).data('currentPage');
           console.log('Dismissing ' + uvId);
           contest.deleteUnvalidatedCheckin(uvId)
               .then(that.removeRow(uvId)).then(
                    function () {
                        if (checkins.data('pageSize') == 1) {
                            return that.displayCheckins(contest, currentPage - 1);
                        } else {
                            return that.displayCheckins(contest, currentPage);
                        }
                    }
                ).done();
        }
    },

    validationFunction: function(contest) {
        let that = this;
        return function() {
            let row = $(this).parents('.checkin-row'); 
            let uvId = $(row).data('validationId');
            console.log('Validating ' + uvId);
            let selected = $(row).find('.beer-select option:selected').val();
            let checkboxes = $(row).find('.bonus-checkbox:checked');
            let bonuses = null;
            if (checkboxes.length > 0) {
                bonuses = checkboxes.map(function(c) { return $(c).data('bonusType'); });
            }
            let promise = null;
            if (selected) {
                if (selected.startsWith('beer:')) {
                    promise = contest.validateBeer(uvId, selected.substring(5), bonuses);
                } else if (selected.startsWith('brewery:')) {
                    promise = contest.validateBrewery(uvId, selected.substring(8), bonuses);
                } else {
                    return;
                }
            } else if (bonuses) {
                promise = contest.validateBonuses(uvId, bonuses);
            } else {
                return;
            }
            let checkins = $('.checkin-list');
            let currentPage = $(checkins).data('currentPage');
            return promise.then(that.removeRow(uvId)).then(
                function () {
                    if (checkins.data('pageSize') == 1) {
                        return that.displayCheckins(contest, currentPage - 1);
                    } else {
                        return that.displayCheckins(contest, currentPage);
                    }
                }
            );
        }
    },
    
    displayCheckins: function(contest, page) {
        let start = 25 * (page - 1) + 1;
        let end = start + 25;
        let that = this;
        contest.getUnvalidatedCheckins(start, end)
            .then(function(data) {
                $('.checkin-list').html('');
                $('.checkin-list').data('currentPage', page);
                $('.checkin-list').data('startIndex', data['page_index']);
                $('.checkin-list').data('pageCount', data['page_count']);
                $('.checkin-list').data('pageSize', data['page_size']);
                for (let i = 0; i < data.checkins.length; i++) {
                    that.addRow(data.checkins[i], i % 2 == 0);
                }
                /* Convert to select2 for dropdown */
                $(".beer-select").select2(
                    { placeholder: "Select a beer or brewery", 
                      allowClear: true, 
                      data: contest.selectData, 
                    });
                /* When a beer or brewery is modified or a bonus is clicked, 
                   check the state of the button */
                $(".beer-select").on("change", that.determineValidateState);
                $(".bonus-checkbox").change(that.determineValidateState);
                /* When a validate button is clicked, submit the validation information */
                $(".validation-click").click(that.validationFunction(contest));
                /* When a dismissal is clicked, submit the dismissal information */
                $(".dismissal-click").click(that.dismissalFunction(contest));
                $(".step-links").html(function (i, oldHtml) {
                    let html = '';
                    if (data.page_index > 1) {
                        html = html + 
                            '<a href="#" onclick="Validate.displayCheckins(contest, ' +
                            '1)">first</a>' + "\n";
                        if (data.page_index > 2) {
                            html = html + 
                                '<a href="#" onclick="Validate.displayCheckins(contest, ' + 
                                (data.page_index - 1) + 
                                ')">previous</a>' + "\n";
                        }
                    }
                    html = html + '<span id="page-description" closs="current">' +
                           'Page ' + data.page_index + ' of ' + data.page_count +
                           "</span>\n";
                    if (data.page_index < data.page_count) {
                        if (data.page_index < data.page_count - 1) {
                            html = html + 
                                '<a href="#" onclick="Validate.displayCheckins(contest, ' + 
                                (data.page_index + 1) + 
                                ')">next</a>' + "\n";
                        }
                        html = html + 
                            '<a href="#" onclick="Validate.displayCheckins(contest, ' +
                            (data.page_count) +
                            ')">last</a>' + "\n";
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
