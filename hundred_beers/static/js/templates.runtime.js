(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['beer_table'] = template({"1":function(container,depth0,helpers,partials,data) {
    return "    <div class=\"col-xs-1\">Checkin</div>\n";
},"3":function(container,depth0,helpers,partials,data) {
    return "  <div class=\"col-xs-1\">+/-</div>\n";
},"5":function(container,depth0,helpers,partials,data) {
    var stack1, alias1=container.lambda, alias2=container.escapeExpression, alias3=depth0 != null ? depth0 : (container.nullContext || {});

  return "<div class=\"row beer-row\">\n    <div class=\"col-xs-4\">"
    + alias2(alias1((depth0 != null ? depth0.name : depth0), depth0))
    + "</div>\n    <div class=\"col-xs-4\">"
    + alias2(alias1((depth0 != null ? depth0.brewery : depth0), depth0))
    + "</div>\n    <div class=\"col-xs-1\">"
    + alias2(alias1((depth0 != null ? depth0.brewery_state : depth0), depth0))
    + "</div>\n    <div class=\"col-xs-1\">"
    + alias2(alias1((depth0 != null ? depth0.point_value : depth0), depth0))
    + "</div>\n"
    + ((stack1 = helpers["if"].call(alias3,(depth0 != null ? depth0.player : depth0),{"name":"if","hash":{},"fn":container.program(6, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + ((stack1 = helpers["if"].call(alias3,(depth0 != null ? depth0.editing : depth0),{"name":"if","hash":{},"fn":container.program(9, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "</div>\n";
},"6":function(container,depth0,helpers,partials,data) {
    var stack1;

  return "    <div class=\"col-xs-1\">\n"
    + ((stack1 = helpers["if"].call(depth0 != null ? depth0 : (container.nullContext || {}),(depth0 != null ? depth0.checked_into : depth0),{"name":"if","hash":{},"fn":container.program(7, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "    </div>\n";
},"7":function(container,depth0,helpers,partials,data) {
    return "    <span class=\"glyphicon glyphicon-ok\" aria-hidden=\"true\"></span>\n";
},"9":function(container,depth0,helpers,partials,data) {
    return "    <div class=\"col-xs-1\">\n    <button type=\"button\" class=\"btn btn-default\" aria-label=\"Delete\">\n      <span class=\"glyphicon glyphicon-remove\" aria-hidden=\"true\"></span>\n    </button>\n    </div>\n";
},"compiler":[7,">= 4.0.0"],"main":function(container,depth0,helpers,partials,data) {
    var stack1, alias1=depth0 != null ? depth0 : (container.nullContext || {});

  return "\n\n<div class=\"row beer-row beer-header\">\n  <div class=\"col-xs-4\">Beer</div>\n  <div class=\"col-xs-4\">Brewery</div>\n  <div class=\"col-xs-1\">State</div>\n  <div class=\"col-xs-1\">Points</div>\n"
    + ((stack1 = helpers["if"].call(alias1,(depth0 != null ? depth0.player : depth0),{"name":"if","hash":{},"fn":container.program(1, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + ((stack1 = helpers["if"].call(alias1,(depth0 != null ? depth0.editing : depth0),{"name":"if","hash":{},"fn":container.program(3, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "")
    + "</div>\n"
    + ((stack1 = helpers.each.call(alias1,(depth0 != null ? depth0.beers : depth0),{"name":"each","hash":{},"fn":container.program(5, data, 0),"inverse":container.noop,"data":data})) != null ? stack1 : "");
},"useData":true});
})();