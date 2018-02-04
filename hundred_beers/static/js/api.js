var Contests = {

    init: function(baseUrl, contestId) {
        // Returns a contest object that provides access to the data 
        // specific to the contest.
        return {
            baseUrl: baseUrl,
            contestId: contestId,
            contestUrl: baseUrl + 'contests/' + contestId,

            getUnvalidatedCheckins: function (startIndex, endIndex) {
                // Returns an AJAX Promise to get thel ist of checkins
                let url = this.contestUrl + '/unvalidated_checkins';
                console.log('Trying to use ' + url);
                return $.ajax({
                    url: url,
                    headers: { Accept: 'application/json' },
                    data: { 'slice_start': startIndex, 'slice_end': endIndex, },
                    method: 'GET',
                    contentType: 'application/json',
                });
            },

            deleteUnvalidatedCheckin: function (uvId) {
                let url = this.contestUrl + '/unvalidated_checkins/' + uvId;
                return $.ajax({
                    url: url,
                    headers: { Accept: 'application/json' },
                    dataType: 'json',
                    method: 'DELETE'
                });
            },

            loadBeers: function(success) {
                let url = this.baseUrl + 'api/contests/' + this.contestId + '/beers';
                var that = this;
                return $.getJSON(url, function(data) {
                    that.beers = data;
                    if (success != null) {
                        success(data);
                    }
                });
            },

            validateBeer: function(uvId, beerId, bonuses = null) {
              let url = this.contestUrl + '/checkins';
              content = { 
                  'checkin': uvId, 
                  'as_beer': beerId,
              };
              if (bonuses) {
                  content['bonuses'] = bonuses;
              }
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                data: JSON.stringify(content),
                contentType: 'application/json',
                dataType: 'json',
                method: 'POST'
              });
            },

            validateBrewery: function(uvId, breweryId, bonuses = null) {
              let url = this.contestUrl + '/checkins';
              content = { 
                  'checkin': uvId, 
                  'as_brewery': breweryId,
              };
              if (bonuses) {
                  content['bonuses'] = bonuses;
              }
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                data: JSON.stringify(content),
                contentType: 'application/json',
                dataType: 'json',
                method: 'POST'
              });
            },

            validateBonuses: function(uvId, bonuses) {
              let url = this.contestUrl  + '/checkins';
              content = { 
                  'checkin': uvId, 
                  'bonuses': bonuses,
              };
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                data: JSON.stringify(content),
                contentType: 'application/json',
                dataType: 'json',
                method: 'POST'
              });
            },


            addBeer: function(data) {
              let url = this.baseUrl + 'api/contests/' + this.contestId + '/beers/';
              console.log('Calling addBeer with JSON');
              console.log(JSON.stringify(data, null, 2));
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                data: JSON.stringify(data),
                contentType: 'application/json',
                dataType: 'json',
                method: 'POST',
              });
            },

            deleteBeer: function(beerId) {
              let url = this.baseUrl + 'api/contests/' 
                                     + this.contestId + '/beers/' + beerId;
              console.log('Calling deleteBeer');
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                contentType: 'application/json',
                method: 'DELETE',
              });
            },
        }
    }
};

