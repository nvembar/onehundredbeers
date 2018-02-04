(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['beer_table'] = template({"1":function(container,depth0,helpers,partials,data) {
    return "    <div class=\"col-xs-1\">Checkin</div>\n";
},"3":function(container,depth0,helpers,partials,data) {
    return "  <div class=\"col-xs-1\">+/-</div>\n";
},"5":function(container,depth0,helpers,partials,data) {
    return "<div class=\"col-xs-12\"><span>No beers added to the contest yet</span></div>\n";
},"7":function(container,depth0,helpers,partials,data,blockParams,depths) {
    var stack1, alias1=container.lambda, alias2=container.escapeExpression, alias3=depth0 != null ? depth0 : (container.nullContext || {});

  return "<div id=\"beer-"
    + alias2(alias1((depth0 != null ? depth0.id : depth0), depth0))
    + "\" class=\"row beer-row "
    + ((stack1 = helpers["if"].call(alias3,(depth0 != null ? depth0.checked_into : depth0),{"name":"if","hash":{},"fn":container.program(8, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "\">\n    <div class=\"col-xs-4\">"
    + alias2(alias1((depth0 != null ? depth0.name : depth0), depth0))
    + "</div>\n    <div class=\"col-xs-4\">"
    + alias2(alias1((depth0 != null ? depth0.brewery : depth0), depth0))
    + "</div>\n    <div class=\"col-xs-1\">"
    + alias2(alias1((depth0 != null ? depth0.brewery_state : depth0), depth0))
    + "</div>\n    <div class=\"col-xs-1\">"
    + alias2(alias1((depth0 != null ? depth0.point_value : depth0), depth0))
    + "</div>\n"
    + ((stack1 = helpers["if"].call(alias3,(depth0 != null ? depth0.player : depth0),{"name":"if","hash":{},"fn":container.program(10, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + ((stack1 = helpers["if"].call(alias3,(depths[1] != null ? depths[1].editing : depths[1]),{"name":"if","hash":{},"fn":container.program(13, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "</div>\n";
},"8":function(container,depth0,helpers,partials,data) {
    return "beer-checkedin";
},"10":function(container,depth0,helpers,partials,data) {
    var stack1;

  return "    <div class=\"col-xs-1\">\n"
    + ((stack1 = helpers["if"].call(depth0 != null ? depth0 : (container.nullContext || {}),(depth0 != null ? depth0.checked_into : depth0),{"name":"if","hash":{},"fn":container.program(11, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "    </div>\n";
},"11":function(container,depth0,helpers,partials,data) {
    return "    <span class=\"glyphicon glyphicon-ok\" aria-hidden=\"true\"></span>\n";
},"13":function(container,depth0,helpers,partials,data) {
    return "    <div class=\"col-xs-1\">\n    <button type=\"button\" class=\"btn btn-default\" aria-label=\"Delete\">\n      <span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\" onclick=\"EditContest.removeBeerFromContest(contest, "
    + container.escapeExpression(container.lambda((depth0 != null ? depth0.id : depth0), depth0))
    + ")\"></span>\n    </button>\n    </div>\n";
},"15":function(container,depth0,helpers,partials,data) {
    return "<button type=\"button\" class=\"btn btn-primary\" data-toggle=\"modal\" data-target=\"#addBeer\">Add Beer</button>\n";
},"compiler":[7,">= 4.0.0"],"main":function(container,depth0,helpers,partials,data,blockParams,depths) {
    var stack1, alias1=depth0 != null ? depth0 : (container.nullContext || {});

  return "\n<div id=\"alert-for-beer\" class=\"alert-for-tab\"></div>\n<div class=\"row beer-row beer-header\">\n  <div class=\"col-xs-4\">Beer</div>\n  <div class=\"col-xs-4\">Brewery</div>\n  <div class=\"col-xs-1\">State</div>\n  <div class=\"col-xs-1\">Points</div>\n"
    + ((stack1 = helpers["if"].call(alias1,(depth0 != null ? depth0.player : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + ((stack1 = helpers["if"].call(alias1,(depth0 != null ? depth0.editing : depth0),{"name":"if","hash":{},"fn":container.program(3, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "</div>\n"
    + ((stack1 = helpers.unless.call(alias1,(depth0 != null ? depth0.beers : depth0),{"name":"unless","hash":{},"fn":container.program(5, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + ((stack1 = helpers.each.call(alias1,(depth0 != null ? depth0.beers : depth0),{"name":"each","hash":{},"fn":container.program(7, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + ((stack1 = helpers["if"].call(alias1,(depth0 != null ? depth0.editing : depth0),{"name":"if","hash":{},"fn":container.program(15, data, 0, blockParams, depths),"inverse":container.noop,"data":data})) != null ? stack1 : "");
},"useData":true,"useDepths":true});
})();