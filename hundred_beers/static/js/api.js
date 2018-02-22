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

            loadBreweries: function(success) {
                let url = this.baseUrl + 'api/contests/' + this.contestId + '/breweries';
                var that = this;
                return $.getJSON(url, function(data) {
                    that.breweries = data;
                    if (success != null) {
                        success(data);
                    }
                });
            },

            loadBonuses: function(success) {
                let url = this.baseUrl + 'api/contests/' + this.contestId + '/bonuses';
                var that = this;
                return $.getJSON(url, function(data) {
                    that.bonuses = data;
                    if (success != null) {
                        success(data);
                    }
                });
            },

            loadPlayers: function(success) {
                let url = this.baseUrl + 'api/contests/' + this.contestId + '/players';
                var that = this;
                return $.getJSON(url, function(data) {
                    // sort by username
                    that.players = data.sort((p1,p2) => 
                            p1.username.localeCompare(p2.usernmae));
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

            addObject: function(data, toList) {
              let url = this.baseUrl + 'api/contests/' 
                            + this.contestId + '/' + toList + '/';
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                data: JSON.stringify(data),
                contentType: 'application/json',
                dataType: 'json',
                method: 'POST',
              });
            },

            deleteObject: function(id, fromList) {
              let url = this.baseUrl + 'api/contests/' 
                                     + this.contestId + '/' + fromList + '/' + id;
              return $.ajax({
                url: url,
                headers: { Accept: 'application/json' },
                contentType: 'application/json',
                method: 'DELETE',
              });
            },

            addBeer: function(data) {
              console.log('Calling addBeer with JSON');
              console.log(JSON.stringify(data, null, 2));
              return this.addObject(data, 'beers');
            },

            deleteBeer: function(beerId) {
              console.log('Calling deleteBeer');
              return this.deleteObject(beerId, 'beers');
            },

            addBrewery: function(data) {
              console.log('Calling addBrewery with JSON');
              console.log(JSON.stringify(data, null, 2));
              return this.addObject(data, 'breweries');
            },

            deleteBrewery: function(breweryId) {
              console.log('Calling deleteBrewery');
              return this.deleteObject(breweryId, 'breweries');
            },

            addBonus: function(data) {
              console.log('Calling addBonus with JSON');
              console.log(JSON.stringify(data, null, 2));
              return this.addObject(data, 'bonuses');
            },

            deleteBonus: function(bonusId) {
              console.log('Calling deleteBrewery');
              return this.deleteObject(bonusId, 'bonuses');
            },

            lookupBeer: function(untappdUrl) {
              let url = this.baseUrl + 'api/lookup/beer';
              return $.ajax({
                url: url,
                data: { 'url': untappdUrl, },
                headers: { Accept: 'application/json' },
                contentType: 'application/json',
                method: 'GET',
              })
            },
                        
            lookupBrewery: function(untappdUrl) {
              let url = this.baseUrl + 'api/lookup/brewery';
              console.log('Looking up brewery at URL: ' + untappdUrl);
              return $.ajax({
                url: url,
                data: { 'url': untappdUrl, },
                headers: { Accept: 'application/json' },
                contentType: 'application/json',
                method: 'GET',
              })
            },
        }
    }
};

