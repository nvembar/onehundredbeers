"use strict";

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

    addRow: function(contest, checkin, even=true, updateSelect=true) {
        if (checkin.has_possibles) {
            let beer = contest.beers.find(b => 
                    (checkin.beer == b.name && checkin.brewery && b.brewery));
            checkin.possible_id = beer.id;
            checkin.any_possible = true;
            checkin.possible_name = beer.name;
        }
        if (checkin.possible_bonuses) {
            checkin.any_possible = true;
        }
        $(".checkin-list").append(Handlebars.templates.validation_grid(
            { 'checkin': checkin, 'bonuses': contest.bonuses }
        ));
        if (checkin.possible_bonuses) {
            for (let i = 0; i < checkin.possible_bonuses.length; ++i) {
                $('#id_' + checkin.id + '_' + checkin.possible_bonuses[i]).prop(
                        'checked', true);
            }
        }
    },

    determineValidateState: function(e) {
        let row = $(this).parents('.checkin-row');
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
            let selected = $(row).find('.beer-select option:selected').val();
            let checkboxes = $(row).find('.bonus-checkbox:checked');
            let bonuses = null;
            if (checkboxes.length > 0) {
                bonuses = $(checkboxes).map(
                    function() { 
                        return $(this).data('bonusType'); 
                    }).get();
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
        return contest.loadBonuses()
            .then(() => contest.getUnvalidatedCheckins(start, end))
            .then(function(data) {
                let page_count = Math.ceil(data.count / 25);
                $('.checkin-list').html('');
                $('.checkin-list').data('currentPage', page);
                $('.checkin-list').data('startIndex', start);
                $('.checkin-list').data('pageCount', page_count);
                $('.checkin-list').data('pageSize', data.results.length);
                for (let i = 0; i < data.results.length; i++) {
                    that.addRow(contest, data.results[i], i % 2 == 0);
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
                    if (page > 1) {
                        html = html + 
                            '<a href="#" onclick="Validate.displayCheckins(contest, ' +
                            '1)">first</a>' + "\n";
                        if (page > 2) {
                            html = html + 
                                '<a href="#" onclick="Validate.displayCheckins(contest, ' + 
                                (page - 1) + 
                                ')">previous</a>' + "\n";
                        }
                    }
                    html = html + '<span id="page-description" closs="current">' +
                           'Page ' + page + ' of ' + page_count + "</span>\n";
                    if (page < page_count) {
                        if (page < page_count - 1) {
                            html = html + 
                                '<a href="#" onclick="Validate.displayCheckins(contest, ' + 
                                (page + 1) + 
                                ')">next</a>' + "\n";
                        }
                        html = html + 
                            '<a href="#" onclick="Validate.displayCheckins(contest, ' +
                            (page_count) +
                            ')">last</a>' + "\n";
                    }
                    return html;
                });
             });
    },

    addUnvalidatedCheckinToContest: function (contest) {
        let urlInput = document.getElementById('uv_untappd_url')
        console.log("--urlInput w var--")
        console.log(urlInput)
        console.log("--urlInput w var--")
        var untappdUrl = urlInput.value;
        console.log("In addUnvalidatedCheckinToContest(" + untappdUrl + ")")
        $("#uv-help-block").removeClass(["has-success", "has-error"]);
        $("#uv-form-group").removeClass(["has-success", "has-error"]);
        $("#uv-help-block").text("")
        return contest.addUnvalidatedCheckin(untappdUrl).then(
            function (uv) {
                $("#uv-help-block").text("Added " + uv.player + " checkin to " + uv.beer);
                $("#uv-form-group").addClass("has-success");
            }
        ).then(
            function (data) {
                let page = $(".checkin-list").data("currentPage")
                if (page == null) {
                    page = 1
                }
                Validate.displayCheckins(contest, page)
            }
        ).fail(
            function (jqXHR) {
                try {
                    let errors = JSON.parse(jqXHR.responseText)
                    console.log(jqXHR.responseText)
                    if (errors["non_field_errors"] != undefined) {
                        $("#uv-help-block").text(errors["non_field_errors"][0])
                        $("#uv-help-block").addClass("has-error")
                        $("#uv-form-group").addClass("has-error")
                    } else if (errors["untappd_checkin"] != undefined) {
                        $("#uv-help-block").text(errors["untappd_checkin"])
                        $("#uv-help-block").addClass("has-error")
                        $("#uv-form-group").addClass("has-error")
                    }
                } catch (e) {
                    $("#uv-help-block").text('Unknown Error')
                    $("#uv-help-block").addClass("has-error")
                    $("#uv-form-group").addClass("has-error")
                    console.log("Exception caught: " + e)
                    console.log('--Returned text below--')
                    console.log(jqXHR.responseText)
                    console.log('--End Returned text--')
                }
            }
        );
    }
};

$(function() {
    var csrfSafeMethod = function(method) {
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
});
