/*
    http://www.JSON.org/json2.js
    2010-11-17

    Public Domain.

    NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.

    See http://www.JSON.org/js.html


    This code should be minified before deployment.
    See http://javascript.crockford.com/jsmin.html

    USE YOUR OWN COPY. IT IS EXTREMELY UNWISE TO LOAD CODE FROM SERVERS YOU DO
    NOT CONTROL.


    This file creates a global JSON object containing two methods: stringify
    and parse.

        JSON.stringify(value, replacer, space)
            value       any JavaScript value, usually an object or array.

            replacer    an optional parameter that determines how object
                        values are stringified for objects. It can be a
                        function or an array of strings.

            space       an optional parameter that specifies the indentation
                        of nested structures. If it is omitted, the text will
                        be packed without extra whitespace. If it is a number,
                        it will specify the number of spaces to indent at each
                        level. If it is a string (such as '\t' or '&nbsp;'),
                        it contains the characters used to indent at each level.

            This method produces a JSON text from a JavaScript value.

            When an object value is found, if the object contains a toJSON
            method, its toJSON method will be called and the result will be
            stringified. A toJSON method does not serialize: it returns the
            value represented by the name/value pair that should be serialized,
            or undefined if nothing should be serialized. The toJSON method
            will be passed the key associated with the value, and this will be
            bound to the value

            For example, this would serialize Dates as ISO strings.

                Date.prototype.toJSON = function (key) {
                    function f(n) {
                        // Format integers to have at least two digits.
                        return n < 10 ? '0' + n : n;
                    }

                    return this.getUTCFullYear()   + '-' +
                         f(this.getUTCMonth() + 1) + '-' +
                         f(this.getUTCDate())      + 'T' +
                         f(this.getUTCHours())     + ':' +
                         f(this.getUTCMinutes())   + ':' +
                         f(this.getUTCSeconds())   + 'Z';
                };

            You can provide an optional replacer method. It will be passed the
            key and value of each member, with this bound to the containing
            object. The value that is returned from your method will be
            serialized. If your method returns undefined, then the member will
            be excluded from the serialization.

            If the replacer parameter is an array of strings, then it will be
            used to select the members to be serialized. It filters the results
            such that only members with keys listed in the replacer array are
            stringified.

            Values that do not have JSON representations, such as undefined or
            functions, will not be serialized. Such values in objects will be
            dropped; in arrays they will be replaced with null. You can use
            a replacer function to replace those with JSON values.
            JSON.stringify(undefined) returns undefined.

            The optional space parameter produces a stringification of the
            value that is filled with line breaks and indentation to make it
            easier to read.

            If the space parameter is a non-empty string, then that string will
            be used for indentation. If the space parameter is a number, then
            the indentation will be that many spaces.

            Example:

            text = JSON.stringify(['e', {pluribus: 'unum'}]);
            // text is '["e",{"pluribus":"unum"}]'


            text = JSON.stringify(['e', {pluribus: 'unum'}], null, '\t');
            // text is '[\n\t"e",\n\t{\n\t\t"pluribus": "unum"\n\t}\n]'

            text = JSON.stringify([new Date()], function (key, value) {
                return this[key] instanceof Date ?
                    'Date(' + this[key] + ')' : value;
            });
            // text is '["Date(---current time---)"]'


        JSON.parse(text, reviver)
            This method parses a JSON text to produce an object or array.
            It can throw a SyntaxError exception.

            The optional reviver parameter is a function that can filter and
            transform the results. It receives each of the keys and values,
            and its return value is used instead of the original value.
            If it returns what it received, then the structure is not modified.
            If it returns undefined then the member is deleted.

            Example:

            // Parse the text. Values that look like ISO date strings will
            // be converted to Date objects.

            myData = JSON.parse(text, function (key, value) {
                var a;
                if (typeof value === 'string') {
                    a =
/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)Z$/.exec(value);
                    if (a) {
                        return new Date(Date.UTC(+a[1], +a[2] - 1, +a[3], +a[4],
                            +a[5], +a[6]));
                    }
                }
                return value;
            });

            myData = JSON.parse('["Date(09/09/2001)"]', function (key, value) {
                var d;
                if (typeof value === 'string' &&
                        value.slice(0, 5) === 'Date(' &&
                        value.slice(-1) === ')') {
                    d = new Date(value.slice(5, -1));
                    if (d) {
                        return d;
                    }
                }
                return value;
            });


    This is a reference implementation. You are free to copy, modify, or
    redistribute.
*//*jslint evil: true, strict: false, regexp: false *//*members "", "\b", "\t", "\n", "\f", "\r", "\"", JSON, "\\", apply,
    call, charCodeAt, getUTCDate, getUTCFullYear, getUTCHours,
    getUTCMinutes, getUTCMonth, getUTCSeconds, hasOwnProperty, join,
    lastIndex, length, parse, prototype, push, replace, slice, stringify,
    test, toJSON, toString, valueOf
*/// Create a JSON object only if one does not already exist. We create the
// methods in a closure to avoid creating global variables.
function toRelativeTimeSeconds(a,b){return b==="seconds"?a/time_factors_seconds.seconds:b==="minutes"?a/time_factors_seconds.minutes:b==="hours"?a/time_factors_seconds.hours:b==="days"?a/time_factors_seconds.days:b==="months"?a/time_factors_seconds.months:b==="years"?a/time_factors_seconds.years:null}function toRelativeTimeMilliseconds(a,b){return b==="seconds"?a/time_factors_milliseconds.seconds:b==="minutes"?a/time_factors_milliseconds.minutes:b==="hours"?a/time_factors_milliseconds.hours:b==="days"?a/time_factors_milliseconds.days:b==="months"?a/time_factors_milliseconds.months:b==="years"?a/time_factors_milliseconds.years:null}function toSeconds(a,b){return b==="seconds"?a*time_factors_seconds.seconds:b==="minutes"?a*time_factors_seconds.minutes:b==="hours"?a*time_factors_seconds.hours:b==="days"?a*time_factors_seconds.days:b==="months"?a*time_factors_seconds.months:b==="years"?a*time_factors_seconds.years:null}function toMilliseconds(a,b){return b==="seconds"?a*time_factors_milliseconds.seconds:b==="minutes"?a*time_factors_milliseconds.minutes:b==="hours"?a*time_factors_milliseconds.hours:b==="days"?a*time_factors_milliseconds.days:b==="months"?a*time_factors_milliseconds.months:b==="years"?a*time_factors_milliseconds.years:null}function create_query(){var a={};$("#filter").attr("checked")&&(a.filter=[[]],$("#filter_options").children(".fields").children().each(function(b,c){$(c).parent().css("display")!=="none"&&(parseFloat($(c).val())?a.filter[0].push(parseFloat($(c).val())):a.filter[0].push($(c).val()))})),$("#exclude").attr("checked")&&(a.exclude=[[]],$("#exclude_options").children(".fields").children().each(function(b,c){$(c).parent().css("display")!=="none"&&(parseFloat($(c).val())?a.exclude[0].push(parseFloat($(c).val())):a.exclude[0].push($(c).val()))})),a.segmentize={},a.segmentize.field=$("#segmentize_field").val(),a.segmentize.method=[$("#segmentize_method").val()];var b=$("#segmentize_field");$("#segmentize_method").val()=="range"?(a.segmentize.method.push({}),$.each($("#segmentize_range").children("div").children("input"),function(c,d){b.val()==="runtime"||b.val()==="totaltime"||b.val()==="waittime"?$(d).attr("name")!=="interval"?a.segmentize.method[1][$(d).attr("name")]=parseFloat($(d).val()):a.segmentize.method[1][$(d).attr("name")]=toSeconds($(d).val(),$("#interval_select").val()):$(d).attr("name")!=="interval"?a.segmentize.method[1][$(d).attr("name")]=parseDate(d):a.segmentize.method[1][$(d).attr("name")]=toMilliseconds($(d).val(),$("#interval_select").val())})):$("#segmentize_method").val()=="values"&&a.segmentize.method.push($("#segmentize_values").children("div").children("input").val().split(/[\s,]+/)),a.aggregate=[];var c=$("#aggregate_table tr");c.each(function(b,c){if(b!=0){var d=$(c).children();a.aggregate.push({}),a.aggregate[b-1].field=$.text([d[0]]),a.aggregate[b-1].methods=$.text([d[1]]).split(/[\s,]+/)}}),console.log(JSON.stringify(a)),submitQuery(JSON.stringify(a))}function formatData(a){var b,c=$("#segmentize_field");CMA.Core.testUrls&&(a=JSON.parse(a));if(c.val()==="sent"||c.val()==="received"||c.val()==="started"||c.val()==="succeeded"||c.val()==="failed"){var d=a.data[0],e=d.length;for(b=0;b<e;b++)d[b]=toRelativeTimeMilliseconds(d[b],$("#interval_select").val())}else System.EventBus.fireEvent("formatData",a)}function submitQuery(a){CMA.Core.ajax.getDispatchedTasksData(a,formatData)}function startChart(a){var b=CMA.Core.DataParser.getTicks();c1=Chart("#chart",a,b),c1.displayBarChart(!0),c1.enableTooltips()}function parseDate(a){var b=new AnyTime.Converter({format:'{"year":"%Y","month":"%m","day":"%d","hour":"%H","minute":"%i","second":"%s"}'}),c=new AnyTime.Converter,d=null,e=null;d=c.parse($(a).val()),obj=JSON.parse(b.format(d)),e=new Date(parseFloat(obj.year),parseFloat(obj.month),parseFloat(obj.day),parseFloat(obj.hour),parseFloat(obj.minute),parseFloat(obj.second));return e.getTime()}function onReady(){System.Handlers.loadHandlers();var a={segmentize:{field:"worker",method:["all"]},aggregate:[{field:"waittime",methods:["average","max","min"]}]};submitQuery(JSON.stringify(a))}function Chart(a,b,c){function p(){if(f.xaxis!==undefined&&(f.xaxis.ticks!==undefined||f.xaxis.ticks!==null)){var a,b=f.xaxis.ticks.length;if(i==="line")for(a=0;a<b;a++)f.xaxis.ticks[a][0]-=.3;else for(a=0;a<b;a++)f.xaxis.ticks[a][0]+=.3}}function j(){g=$.plot(d,e,f)}var d=a,e=b,f=c,g=null,h=null,i=null,k=function(a,b,c){$.each(e,function(d,e){e.label==a&&$.each(e.data,function(a,d){d[0]==b&&(d[1]=c)})}),j()},l=function(a,b){$.each(this.data,function(c,d){d.label==a&&(d.data=b)}),j()},m=function(a){e.push(a),j()},n=function(a){f.series===undefined&&(f.series={}),a!==undefined&&a===!0?f.series.stack=!0:delete f.series.stack,f.series.lines!==undefined&&(f.series.lines.show=!1,f.series.points!==null&&r()),f.series.bars={show:!0,barWidth:.6},i="bar",p(),j()},o=function(){f.series===undefined&&(f.series={points:{show:!0}}),f.series.stack!==undefined&&delete f.series.stack,f.series.bars!==undefined&&(f.series.bars.show=!1),f.series.lines={show:!0},i="line",q(),p(),j()},q=function(){f.series.points={show:!0},j()},r=function(){f.series.points={show:!1},j()},s=function(){f.legend!==undefined?f.legend.show=!0:(f.legend={},f.legend.show=!0),j()},t=function(){f.legend!==undefined?f.legend.show=!1:(f.legend={},f.legend.show=!1),j()},u=function(a){f.selection={};var b=g.getAxes().xaxis.max,c=g.getAxes().xaxis.min;if(i==="line")var h={lines:{show:!0,lineWidth:1},shadowSize:0};else var h={bars:{show:!0},shadowSize:0};var k={series:h,xaxis:{ticks:[]},yaxis:{ticks:[],autoscaleMargin:.1},y2axis:{ticks:[],autoscaleMargin:.1},selection:{mode:"x"},legend:{show:!1}},l=$.plot($(a),e,k);$(d).bind("plotselected",function(a,b){plotRef=$.plot($(d),e,$.extend(!0,{},f,{xaxis:{min:b.xaxis.from,max:b.xaxis.to}})),l.setSelection(b,!0)}),$(a).bind("plotselected",function(a,b){g.setSelection(b)}),$(a).after('<button id="zoom_out">Zoom Out</button>'),$("#zoom_out").click(function(){f.xaxis={min:c,max:b},l.setSelection({},!0),j()})},v=function(a){$(a).html("").next().remove(),f.selection.mode="none",j()},w=function(a){f.y2axis===null&&(a.yaxis=2,e.push(a),f.y2axis={}),j()},x=function(){f.y2axis!==null&&($.each(e,function(a,b){b.yaxis==2&&e.splice(a,1)}),delete f.y2axis),j()},y=function(a){alert("Not implemented yet!")},z=function(){function a(a,b,c){$('<div id="tooltip">'+c+"</div>").css({position:"absolute",display:"none",top:b+5,left:a+5,border:"1px solid #fdd",padding:"2px","background-color":"#fee",opacity:.8}).appendTo("body").fadeIn(200)}f.grid===undefined&&(f.grid={hoverable:!0,clickable:!0}),j();var b=null;$(d).bind("plothover",function(c,d,e){if(e)if($("#tooltip").length!==0&&i==="line")var f;else if(b!=e.datapoint){b=e.datapoint,$("#tooltip").remove();var g=e.datapoint[0].toFixed(2),h=e.datapoint[1].toFixed(2);i=="line"?a(e.pageX,e.pageY,e.series.label+": ("+g+", "+h+")"):a(e.pageX,e.pageY,e.series.label+": "+h)}else $("#tooltip").remove(),b=null;else $("#tooltip").remove()})},A=function(){$("#tooltip").remove(),f.grid!==undefined&&delete f.grid,j()},B=function(a,b,c){var d=null;$.each(e,function(c,e){e.label==a&&$.each(e.data,function(a,c){c[0]==b&&(d=c[1])})});var f=g.pointOffset({x:b,y:d}),h={left:f.left-4,top:f.top-4},i=6,j=g.getCanvas().getContext("2d");j.moveTo(h.left,h.top),j.lineTo(h.left-i,h.top),j.lineTo(h.left-i/3,h.top-i/3),j.lineTo(h.left,h.top-i),j.lineTo(h.left,h.top),j.fillStyle="#222",j.fill(),j.moveTo(h.left-i/2+2,h.top-i/2+2),j.lineTo(h.left-i*2,h.top-i*2),j.strokeStyle="#222",j.stroke(),j.fillText(c,h.left-i*4,h.top-i*3+i/2)},C=function(a,b){$("."+a+"_"+b).remove()},D=function(a){f=a,j()},E=function(){return e},F=function(){return g};return{changePoint:k,changeDataPlot:l,addDataPlot:m,displayBarChart:n,displayLineChart:o,enablePoints:q,disablePoints:r,enableLegend:s,disableLegend:t,enableOverview:u,disableOverview:v,addSecondaryAxis:w,removeSecondaryAxis:x,enableDataSelection:y,enableTooltips:z,disableTooltips:A,addAnnotation:B,removeAnnotation:C,setTicks:D,getData:E,getPlot:F}}function createTable(a){var b=$(".content");b.html(""),b.html("<table> </table>"),a.each(function(a,b){alert(a+" "+b)})}this.JSON||(this.JSON={}),function(){function str(a,b){var c,d,e,f,g=gap,h,i=b[a];i&&typeof i==="object"&&typeof i.toJSON==="function"&&(i=i.toJSON(a)),typeof rep==="function"&&(i=rep.call(b,a,i));switch(typeof i){case"string":return quote(i);case"number":return isFinite(i)?String(i):"null";case"boolean":case"null":return String(i);case"object":if(!i)return"null";gap+=indent,h=[];if(Object.prototype.toString.apply(i)==="[object Array]"){f=i.length;for(c=0;c<f;c+=1)h[c]=str(c,i)||"null";e=h.length===0?"[]":gap?"[\n"+gap+h.join(",\n"+gap)+"\n"+g+"]":"["+h.join(",")+"]",gap=g;return e}if(rep&&typeof rep==="object"){f=rep.length;for(c=0;c<f;c+=1)d=rep[c],typeof d==="string"&&(e=str(d,i),e&&h.push(quote(d)+(gap?": ":":")+e))}else for(d in i)Object.hasOwnProperty.call(i,d)&&(e=str(d,i),e&&h.push(quote(d)+(gap?": ":":")+e));e=h.length===0?"{}":gap?"{\n"+gap+h.join(",\n"+gap)+"\n"+g+"}":"{"+h.join(",")+"}",gap=g;return e}}function quote(a){escapable.lastIndex=0;return escapable.test(a)?'"'+a.replace(escapable,function(a){var b=meta[a];return typeof b==="string"?b:"\\u"+("0000"+a.charCodeAt(0).toString(16)).slice(-4)})+'"':'"'+a+'"'}function f(a){return a<10?"0"+a:a}"use strict",typeof Date.prototype.toJSON!=="function"&&(Date.prototype.toJSON=function(a){return isFinite(this.valueOf())?this.getUTCFullYear()+"-"+f(this.getUTCMonth()+1)+"-"+f(this.getUTCDate())+"T"+f(this.getUTCHours())+":"+f(this.getUTCMinutes())+":"+f(this.getUTCSeconds())+"Z":null},String.prototype.toJSON=Number.prototype.toJSON=Boolean.prototype.toJSON=function(a){return this.valueOf()});var cx=/[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,escapable=/[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,gap,indent,meta={"\b":"\\b","\t":"\\t","\n":"\\n","\f":"\\f","\r":"\\r",'"':'\\"',"\\":"\\\\"},rep;typeof JSON.stringify!=="function"&&(JSON.stringify=function(a,b,c){var d;gap="",indent="";if(typeof c==="number")for(d=0;d<c;d+=1)indent+=" ";else typeof c==="string"&&(indent=c);rep=b;if(b&&typeof b!=="function"&&(typeof b!=="object"||typeof b.length!=="number"))throw new Error("JSON.stringify");return str("",{"":a})}),typeof JSON.parse!=="function"&&(JSON.parse=function(text,reviver){function walk(a,b){var c,d,e=a[b];if(e&&typeof e==="object")for(c in e)Object.hasOwnProperty.call(e,c)&&(d=walk(e,c),d!==undefined?e[c]=d:delete e[c]);return reviver.call(a,b,e)}var j;text=String(text),cx.lastIndex=0,cx.test(text)&&(text=text.replace(cx,function(a){return"\\u"+("0000"+a.charCodeAt(0).toString(16)).slice(-4)}));if(/^[\],:{}\s]*$/.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g,"@").replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,"]").replace(/(?:^|:|,)(?:\s*\[)+/g,""))){j=eval("("+text+")");return typeof reviver==="function"?walk({"":j},""):j}throw new SyntaxError("JSON.parse")})}();var CMA=typeof CMA==="undefined"||!CMA?{}:CMA;CMA.Core=typeof CMA.Core==="undefined"||!CMA.Core?{}:CMA.Core,CMA.Core.ajax=function(){var a={},b=function(){root_url="/celerymanagementapp/",a={get_tasks_url:root_url+"task/all/list/",get_workers_url:root_url+"worker/all/list/",tasks_per_worker_url:root_url+"task/all/dispatched/byworker/count/",pending_tasks_url:root_url+"task/all/dispatched/pending/count/",worker_processes_url:root_url+"worker/all/subprocess/count/",shutdown_worker_url:root_url+"worker/<placeHolder>/shutdown/",query_dispatched_tasks_url:root_url+"xy_query/dispatched_tasks/",task_url:"/celerymanagementapp/view/task/",worker_url:"/celerymanagementapp/view/worker/",out_of_band_worker_create_url:root_url+"outofbandworker/",out_of_band_worker_update_url:root_url+"outofbandworker/<placeHolder>/update/",out_of_band_worker_delete_url:root_url+"outofbandworker/<placeHolder>/delete/",provider_create_url:root_url+"provider/",provider_delete_url:root_url+"provider/<placeHolder>/delete/",get_images_url:root_url+"provider/images/",delete_instance_url:root_url+"provider/delete_worker/",policy_create_url:root_url+"policy/create/",policy_update_url:root_url+"policy/modify/<placeHolder>/",policy_delete_url:root_url+"policy/delete/<placeHolder>/"}},c=function(){var b="/celerymanagementapp/site_media/test_data/",c="/celerymanagementapp/test/post/";a={get_tasks_url:b+"tasks.json",get_workers_url:b+"workers.json",tasks_per_worker_url:b+"tasks_per_worker.json",pending_tasks_url:b+"tasks_pending.json",worker_processes_url:b+"worker_processes.json",shutdown_worker_url:c+"worker/<placeHolder>/shutdown/",query_dispatched_tasks_url:c+"xy_query/dispatched_tasks/",task_url:"/celerymanagementapp/test/view/task/",worker_url:"/celerymanagementapp/test/view/worker/",chart_data_url:b+"chart/enumerate-1.json",out_of_band_worker_create_url:c+"outofbandworker/",out_of_band_worker_update_url:c+"outofbandworker/<placeHolder>/update/",out_of_band_worker_delete_url:c+"outofbandworker/<placeHolder>/delete/",provider_create_url:c+"provider/",provider_delete_url:c+"provider/<placeHolder>/delete/",get_images_url:c+"provider/images/",delete_instance_url:c+"provider/delete_worker/1/",policy_create_url:c+"policy/create/",policy_update_url:c+"policy/modify/<placeHolder>/",policy_delete_url:c+"policy/delete/<placeHolder>/"}},d=function(){return a},e=function(b){$.getJSON(a.get_tasks_url,b)},f=function(b){$.getJSON(a.get_workers_url,b)},g=function(b){$.getJSON(a.tasks_per_worker_url,b)},h=function(b){$.getJSON(a.pending_tasks_url,b)},i=function(b){$.getJSON(a.worker_processes_url,b)},j=function(b,c){$.post(a.shutdown_worker_url.replace("<placeHolder>",b),c)},k=function(b,c){$.post(a.query_dispatched_tasks_url,b,c)},l=function(b){$.post(a.get_images_url,$("#blankProviderForm").serialize(),b,"json")},m=function(b,c){$.post(a.delete_instance_url.replace("<placeHolder>",b),c,"json")},n=function(b,c){b.ajaxSubmit({dataType:"json",url:a.out_of_band_worker_create_url,success:c})},o=function(b,c,d){b.ajaxSubmit({dataType:"json",url:a.out_of_band_worker_update_url.replace("<placeHolder>",c),success:d})},p=function(b,c){$.post(a.out_of_band_worker_delete_url.replace("<placeHolder>",b),{},c,"json")},q=function(b,c){console.log("test"),b.ajaxSubmit({dataType:"json",url:a.provider_create_url,success:c})},r=function(b,c){$.post(a.provider_delete_url.replace("<placeHolder>",b),{},c,"json")},s=function(b,c){$.post(a.policy_create_url,b,c,"json")},t=function(b,c){$.post(a.policy_delete_url.replace("<placeHolder>",b),{},c,"json")},u=function(b,c,d){$.post(a.policy_update_url.replace("<placeHolder>",c),b,d,"json")};return{getUrls:d,loadUrls:b,loadTestUrls:c,getTasks:e,getWorkers:f,getTasksPerWorker:g,getPendingTasks:h,getWorkerProcesses:i,postShutdownWorker:j,getDispatchedTasksData:k,postGetImages:l,postDeleteInstance:m,postCreateOutOfBandWorker:n,postUpdateOutOfBandWorker:o,postDeleteOutOfBandWorker:p,postCreateProvider:q,postDeleteProvider:r,postCreatePolicy:s,postUpdatePolicy:u,postDeletePolicy:t}}();var CMA=typeof CMA==="undefined"||!CMA?{}:CMA;CMA.Core=typeof CMA.Core==="undefined"||!CMA.Core?{}:CMA.Core,CMA.Core.ajax=typeof CMA.Core.ajax==="undefined"||!CMA.Core.ajax?{}:CMA.Core.ajax,CMA.Core.util=function(){var a=function(a){$(a).animate({height:"toggle"},500,function(){})},b=function(a){$("#statusText").text(a),$("#statusText").show(),$("#statusText").fadeOut(6e3,function(){})},c=function(c,d,e,f){var g=function(d){var e=function(){var a=d.failure[g].error.length,b="";for(j=0;j<a;j+=1)b+=d.failure[g].error[j];return b};if(d.hasOwnProperty("failure")){var g=0,h,i=d.failure.length,k=d.id;for(g=0;g<i;g+=1)k!==null&&k!==undefined?h=document.getElementById(k+"_"+d.failure[g].field+"_error"):h=document.getElementById(d.failure[g].field+"_error"),$(h).text(e),$(h).text()!==""?$(h).show():$(h).hide()}else typeof f.successCallback==="undefined"?(b(d),a(c)):(f.successCallback(d),a(c))};f.urlID?d(e,f.urlID,g):d(e,g)},d=function(a,b){var c,d,e,f='<div id="boxes"><div id="popupContainer"><div id="popupTextBox">'+a+'</div><div id="popupButtonContainer"><button class="popupButton click left positiveButton" id="popupYesButton" >Yes</button><button class="popupButton click left negativeButton" id="popupCancelButton" >Cancel</button></div></div><div id="mask"></div></div>',g=$(window).height(),h=$(window).width();$("body").append(f),e=$("#popupContainer"),c=h/2-e.width()/2,d=g/2-e.height()/2,e.css({left:c,top:d}),$("#mask").css({width:h+"px",height:g+"px"}),$("#mask").click(function(){$("#boxes").remove()}),$("#popupCancelButton").click(function(){$("#boxes").remove()}),$("#popupYesButton").click(function(){b(),$("#boxes").remove()}),e.show()},e=function(a){var b=a.target,c=b.selectionStart,d=b.selectionEnd,e="    ";if(a.keyCode==9){a.preventDefault();if(c!=d&&b.value.slice(c,d).indexOf("\n")!=-1){var f=b.value.slice(0,c),g=b.value.slice(c,d).replace(/\n/g,"\n"+e),h=b.value.slice(d,b.value.length);b.value=f.concat(e).concat(g).concat(h),b.selectionStart=c+e.length,b.selectionEnd=d+e.length}else b.value=b.value.slice(0,c).concat(e).concat(b.value.slice(c,b.value.length)),c==d?b.selectionStart=b.selectionEnd=c+e.length:(b.selectionStart=c+e.length,b.selectionEnd=d+e.length)}else a.keyCode==8&&b.value.slice(c-4,c)==e?(a.preventDefault(),b.value=b.value.slice(0,c-4).concat(b.value.slice(c,b.value.length)),b.selectionStart=b.selectionEnd=c-e.length):a.keyCode==46&&b.value.slice(d,d+4)==e?(a.preventDefault(),b.value=b.value.slice(0,c).concat(b.value.slice(c+4,b.value.length)),b.selectionStart=b.selectionEnd=c):a.keyCode==37&&b.value.slice(c-4,c)==e?(a.preventDefault(),b.selectionStart=b.selectionEnd=c-4):a.keyCode==39&&b.value.slice(c,c+4)==e&&(a.preventDefault(),b.selectionStart=b.selectionEnd=c+4)};return{expand:a,formSubmit:c,createPopup:d,checkTab:e,showStatus:b}}(),CMA.Core.init=function(){typeof CMA.Core.testUrls==="undefined"?CMA.Core.ajax.loadUrls():CMA.Core.ajax.loadTestUrls(),CMA.Core.expandedTasks=!1,CMA.Core.expandedWorkers=!1,$("#content").css("width",$(window).width()-$("#dummy").css("width").split("px")[0]-30+"px"),$(window).height()>$("#container").css("min-height").split("px")[0]?$("#navigation").css("height",$(window).height()-$("#header").css("height").split("px")[0]-2+"px"):$("#navigation").css("height",$("#container").css("min-height")),$("li").hover(function(){$(this).css({color:"orange"})},function(){$(this).css({color:"#000000"})})},CMA.Core.setupEvents=function(){$("#taskNavigationMaster").click(function(){CMA.Core.expandedTasks?($("#taskNavigationMaster").text("+ Tasks"),$("#taskNavigation").hide(),CMA.Core.expandedTasks=!1):($("#taskNavigationMaster").text("- Tasks"),$("#taskNavigation").show(),CMA.Core.expandedTasks=!0)}),$("#workerNavigationMaster").click(function(){CMA.Core.expandedWorkers?($("#workerNavigationMaster").text("+ Workers"),$("#workerNavigation").hide(),CMA.Core.expandedWorkers=!1):($("#workerNavigationMaster").text("- Workers"),$("#workerNavigation").show(),CMA.Core.expandedWorkers=!0)}),CMA.Core.taskname!=="undefined"&&$("#taskNavigationMaster").click(),CMA.Core.workername!=="undefined"&&$("#workerNavigationMaster").click(),$(".menuItem").hover(function(){var a=$(this),b=document.getElementById(a.attr("id")+"Img");$(a).toggleClass("menuItemHover rightRounded"),$(b).toggleClass("menuItemHover leftRounded")},function(){var a=$(this),b=document.getElementById(a.attr("id")+"Img");$(a).toggleClass("menuItemHover rightRounded"),$(b).toggleClass("menuItemHover leftRounded")});var a=function(){var a=$(window),b=$("#container"),c=$("#navigation"),d=function(){a.width()>b.css("min-width").split("px")[0]&&$("#content").css("width",a.width()-$("#dummy").css("width").split("px")[0]-20+"px"),a.height()>b.css("min-height").split("px")[0]?c.css("height",a.height()-$("#header").css("height").split("px")[0]-2+"px"):c.css("height",b.css("min-height"))};return d}();$(window).resize(a)},CMA.Core.navigation=function(){var a=CMA.Core.ajax,b=function(a,b,c,d){var e="#7D7D7D",f=b.clone(),g=a.length,h,i,j,k=function(a,b,d){f.append("<li><a  id='navigation_"+a+"' style='color: "+d+";' id='"+a+"' href='"+c+a+"/'>"+b+"</a></li>")};for(i=0;i<g;i+=1)h=a[i],e=h===d?"red":"#7D7D7D",j=h.length>15?"..."+h.substring(h.length-15,h.length):h,k(h,j,e);b.replaceWith(f)},c=function(c){b(c,$("#taskNavigation"),a.getUrls().task_url,CMA.Core.taskname)},d=function(c){b(c,$("#workerNavigation"),a.getUrls().worker_url,CMA.Core.workername)};return{populateTaskNavigation:c,populateWorkerNavigation:d}}(),CMA.Core.policy=function(){var a=CMA.Core.ajax,b=CMA.Core.util,c=function(){var c={},e=function(c){b.showStatus(c.success),$("#configurationManagement").append(c.html),$(".policyForm").hide(),$("#"+c.pk+"_update").click(function(){var a=document.getElementById($(this).attr("id").split("_")[0]+"_Form");b.expand(a)}),$("#"+c.pk+"_delete").click(function(){d($(this))}),$("#"+c.pk+"_editButton").click(function(){var c=$(this).attr("id"),d=c.split("_"),e=document.getElementById(d[0]+"_Form");b.formSubmit($(this).parent(),a.postUpdatePolicy,$(e).serialize(),{urlID:d[0]})}),$("textarea").keydown(b.checkTab)};c.name=$("#id_name").val(),c.enabled=$("#id_enabled").attr("checked"),c.source=$("#id_source").val(),b.formSubmit($(this).parent(),a.postCreatePolicy,c,{successCallback:e})},d=function(c){b.createPopup("Are you sure you wish to delete policy "+$(c).parent().children(":first").text()+" ?",function(){a.postDeletePolicy(c.attr("id").split("_")[0],function(a){if(a.hasOwnProperty("failure"))b.showStatus(a.failure);else{c.parent().remove();var d=c.attr("id").split("_")[0];$("#"+d+"_Form").remove(),b.showStatus(a)}})})},e=function(){$("textarea").attr("rows","10"),$("textarea").css("resize","none"),$(".policyForm").hide(),$(".editPolicy").click(function(){var a=document.getElementById($(this).attr("id").split("_")[0]+"_Form");b.expand(a)}),$(".createPolicy").click(function(){b.expand($("#blankPolicyForm"))}),$("#submitPolicyButton").click(c),$(".deletePolicy").click(function(){d($(this))}),$(".submitPolicyEdit").click(function(){var c=$(this).attr("id"),d=c.split("_"),e=document.getElementById(d[0]+"_Form");b.formSubmit($(this).parent(),a.postUpdatePolicy,$(e).serialize(),{urlID:d[0]})}),$("textarea").keydown(b.checkTab)};return{registerEvents:e}}(),CMA.Core.configure=function(){var a=CMA.Core.util,b=CMA.Core.ajax,c=function(){if(CMA.Core.USE_MODE==="static"){var c=function(c){$("#configurationManagement").append(unescape(c.html)),$(".outOfBandForm").hide(),$("#"+c.pk+"_update").click(function(){var b=document.getElementById($(this).attr("id").split("_")[0]+"_Form");a.expand(b)}),$("#"+c.pk+"_delete").click(function(){var c=$(this).attr("id"),d=c.split("_"),e=this;a.createPopup("Are you sure you wish to delete worker instance "+$(e).parent().children(":first").text()+"?",function(){b.postDeleteOutOfBandWorker(d[0],function(b){b.hasOwnProperty("failure")?a.showStatus(b.failure):($(e).parent().remove(),$("#"+d[0]+"_Form").remove())})})}),$("#"+c.pk+"_editButton").click(function(){var c=$(this).attr("id"),d=c.split("_"),e=document.getElementById(d[0]+"_Form");a.formSubmit($(this).parent(),b.postUpdateOutOfBandWorker,$(e),{urlID:d[0]})}),$("textarea").keydown(a.checkTab),$("textarea").attr("rows","3"),$("textarea").css("resize","none"),$("#blankOutOfBandForm")[0].reset()},d=function(){};$("textarea").attr("rows","3"),$("textarea").css("resize","none"),$(".outOfBandForm").hide(),$(".editWorkerNode").click(function(){var c=$(this).attr("id"),d=c.split("_"),e=this;d[1]==="update"?a.expand(document.getElementById(d[0]+"_Form")):d[1]==="delete"&&a.createPopup("Are you sure you wish to delete worker instance "+$(e).parent().children(":first").text()+"?",function(){b.postDeleteOutOfBandWorker(d[0],function(b){b.hasOwnProperty("failure")?a.showStatus(b.failure):($(e).parent().remove(),$("#"+d[0]+"_Form").remove())})})}),$(".createNewOutOfBand").click(function(){a.expand($("#blankOutOfBandForm"))}),$(".updateOutOfBandButton").click(function(){var c=$(this).attr("id"),e=c.split("_"),f=document.getElementById(e[0]+"_Form");a.formSubmit($(this).parent(),b.postUpdateOutOfBandWorker,$(f),{urlID:e[0],successCallback:d})}),$("#submitOutOfBandButton").click(function(){a.formSubmit($("#blankOutOfBandForm"),b.postCreateOutOfBandWorker,$("#blankOutOfBandForm"),{successCallback:c})}),$("#blankOutOfBandForm").submit(function(){return!1})}else if(CMA.Core.USE_MODE==="dynamic"){var e=function(a){var b=$("#providerStep2"),c,d,e,f;if(a.hasOwnProperty("failure"))b.text(originalText);else{c='<div class="fieldWrapper">',d=a.length;for(e=0;e<d;e+=1)c+='<input class="imageID" type="radio" name="image_id" value="'+a[e].id+'">'+a[e].name+"<br/>";c+="</div>",b.text("Step 2: Please choose the image ID to be used."),f=$(c),b.append(f),$("#providerStep3").show(),$("#submitProviderButton").show(),$(".fieldWrapper").show()}};$("#getImagesButton").click(function(){var a=$("#providerStep2");$(this).hide(),a.text("Please wait while we determine the availible images..."),a.show(),b.postGetImages(e)}),$("#viewProvider").click(function(){$("textarea").attr("rows","3"),$("textarea").css("resize","none"),a.expand($("#providerFormWrapper"))}),$(".deleteInstance").click(function(){var c=$(this).attr("id");element=$(this).parent(),b.postDeleteInstance(c,function(b){b.hasOwnProperty("failure")?a.showStatus(b.failure):(element.remove(),a.showStatus(b))})}),$("#blankProviderForm").submit(function(){return!1}),$("#submitProviderButton").hasClass("positiveButton")?$("#submitProviderButton").click(function(){a.formSubmit($(this).parent(),b.postCreateProvider,$("#blankProviderForm"))}):$("#submitProviderButton").hasClass("negativeButton")&&$("#submitProviderButton").click(function(){a.createPopup("WARNING: Deleting a provider will delete all Worker instances.  Are you sure you wish to continue?",function(){b.postDeleteProvider($("#providerID").text(),function(a){if(!a.hasOwnProperty("failure")){$("#configurationManagement").children().remove();var b=$(a);$("#configurationManagement").append(b),CMA.
Core.configure.registerEvents(),$("textarea").attr("rows","3"),$("textarea").css("resize","none")}})})})}};return{registerEvents:c}}(),$(document).ready(function(){var a=CMA.Core;a.init(),a.setupEvents(),CMA.Core.USE_MODE==="dynamic"&&a.policy.registerEvents(),a.configure.registerEvents()});var System=typeof System==="undefined"||!System?{}:System,CMA=typeof CMA==="undefined"||!CMA?{}:CMA;CMA.Core=typeof CMA.Core==="undefined"||!CMA.Core?{}:CMA.Core,System.Handlers=function(){var a=CMA.Core,b=function(){System.EventBus.addEventHandler("formatData",a.DataParser.formatData),System.EventBus.addEventHandler("dataFormatted",startChart)};return{loadHandlers:b}}();var CMA=typeof CMA==="undefined"||!CMA?{}:CMA;CMA.Core=typeof CMA.Core==="undefined"||!CMA.Core?{}:CMA.Core,CMA.Core.DataParser=function(){var a={},b={},c=function(b){var c=b.data;console.log(b),console.log(c),typeof c[0][0]==="string"?c[0][1][0].fieldname==="runtime"?a=e(c):c[0][1][0].fieldname==="state"?a=f(c):a=h(c):typeof c[0][0]==="number"&&(c[0][1][0].fieldname==="count"?a=g(c):a=i()),System.EventBus.fireEvent("dataFormatted",a)},d=function(a){var b=[],c=[],d=[],e,f=a.length,g=a[0][1][0].methods.length;for(var h in a)a.hasOwnProperty(h)&&(c[h]=a[h][0]);for(e=0;e<g;e++)d[e]=a[0][1][0].methods[e].name;for(e=0;e<f;e++){var i,k={};k.data=[],k.label=c[e];for(i=0;i<g;i++)k.data.push([i,a[e][1][0].methods[i].value]);b.push(k),console.log(b)}j(d);return b},e=function(a){var b=[],c=[],d=0,e,f,g=a.length,h=a[0][1][0].methods.length;for(e=0;e<g;e++){var i={};i.data=[],i.label=a[e][0]+" - Runtime";for(f=0;f<h;f++)i.data.push([e,a[e][1][0].methods[f].value]);b.push(i)}return b},f=function(a){var b=[],c=[],d=[],e,f,g=a.length,h=a[0][1][0].methods[0].value.length;for(e=0;e<g;e++)c[e]=a[e][0];for(e=0;e<h;e++)d[e]=a[0][1][0].methods[0].value[e][0];for(e=0;e<h;e++){var i={};i.data=[],i.label=c[e];for(f=0;f<g;f++)i.data.push([f,a[e][1][0].methods[0].value[f][1]]);b.push(i),console.log(b)}j(d);return b},g=function(a){var b=[],c=[],d={};for(var e in a)if(a.hasOwnProperty(e)){var f=a[e],g=f[0],h=f[1][0].methods;for(var i in h)h.hasOwnProperty(i)&&c.push([g,h[i].value])}d.data=c,d.label=a[0][1][0].fieldname,b.push(d);return b},h=function(a){var b=[],c=0;for(var d in a)if(a.hasOwnProperty(d)){var e={};e.label=a[d][0],e.data=[[c+=1,a[d][1][0].methods[0].value]],b.push(e)}return b},i=function(){var a=[],b=[],c={},d;for(d=0;d<14;d+=.5)b.push([d,Math.sin(d)]);c.label="Malformed data returned by server",c.data=b,a.push(c);return a},j=function(a){b={xaxis:{ticks:[]}};var c=a.length,d;for(d=0;d<c;d++)b.xaxis.ticks.push([d,a[d]])},k=function(){return b};return{formatData:c,getTicks:k}}();var System=typeof System==="undefined"||!System?{}:System;System.EventBus=function(){var a={},b=function(b,c){a[b]||(a[b]=[]),a[b].push(c)},c=function(b,c){if(a[b]){var d,e,f=a[b].length;for(d=0;d<f;d++)e=a[b][d],typeof e==="function"&&e.call(this,c)}else console.error("No such handler for event type: "+b)},d=function(a){return Object.prototype.toString.apply(a)==="[object Array]"};return{addEventHandler:b,fireEvent:c}}(),CMA.Core.testUrls?CMA.Core.ajax.loadTestUrls():CMA.Core.ajax.loadUrls();var c1=null,time_factors_milliseconds={seconds:1e3,minutes:6e4,hours:36e5,days:864e5,months:2629743830,years:31556926e3},time_factors_seconds={seconds:1,minutes:60,hours:3600,days:86400,months:2629743.83,years:31556926};$(document).ready(onReady),$(function(){function c(){$("#range_min").AnyTime_noPicker(),$("#range_max").AnyTime_noPicker();var a=$("#segmentize_field optgroup[id=enum]"),c=$("#segmentize_field optgroup[id=time]"),d=$("#segmentize_method option[value=range]"),e=$("#segmentize_field");if(e.val()==="sent"||e.val()==="received"||e.val()==="started"||e.val()==="succeeded"||e.val()==="failed")$("#range_min").AnyTime_picker({format:"%Y-%m-%d %T"}),$("#range_max").AnyTime_picker({format:"%Y-%m-%d %T"});a.children("[value="+$(this).val()+"]").length!==0?(d.attr("disabled","disabled"),d.next().attr("selected","selected"),b()):(d.attr("disabled",!1),d.attr("selected","selected"),b())}function b(){var a=$("#segmentize_method"),b=$("#segmentize_field");a.val()=="range"?($("#segmentize_range").show(),$("#segmentize_values").hide(),$("#segmentize_taskname").hide()):a.val()=="values"?($("#segmentize_values").show(),$("#segmentize_range").hide(),$("#segmentize_taskname").hide()):($("#segmentize_range").hide(),$("#segmentize_values").hide())}function a(){var a=$("#aggregate_table tr:last");if($("#aggregate_methods").val()){var b=$("#aggregate_field").val(),c=$("#aggregate_methods").val();a.after("<tr><td>"+b+"</td><td>"+c+'</td><td><a href="#" class="'+b+'-delete"><strong>x</strong></span></td></tr>'),$("."+b+"-delete").click(function(){$(this).parent().parent().remove()})}else alert("Select methods for field: "+$("#aggregate_field").val())}$("#segmentize_field").change(c),$("#segmentize_method").change(b),$("#add_aggregation").click(a),$(":checkbox").change(function(){$(this).attr("checked")?$(this).siblings("div").show():$(this).siblings("div").hide()}),$("#filter_option").change(function(){var a=$("#filter_arg2");$(this).val()==="range"?a.show().next().show():a.hide().next().hide()}),$("#exclude_option").change(function(){var a=$("#exclude_arg2");$(this).val()==="range"?a.show().next().show():a.hide().next().hide()})}),$(function(){var a=$("#displayBarChart"),b=$("#displayLineChart"),c=$("#enableTooltips"),d=$("#disableTooltips"),e=$("#enableLegend"),f=$("#disableLegend");a.click(function(){$(this).attr("checked")?(b.attr("checked",!1),c1.displayBarChart()):(b.attr("checked",!0),c1.displayLineChart())}),b.click(function(){$(this).attr("checked")?(a.attr("checked",!1),c1.displayLineChart()):(a.attr("checked",!0),c1.displayBarChart())}),c.click(function(){$(this).attr("checked")?(d.attr("checked",!1),c1.enableTooltips()):(d.attr("checked",!0),c1.disableTooltips())}),d.click(function(){$(this).attr("checked")?(c.attr("checked",!1),c1.disableTooltips()):(c.attr("checked",!0),c1.disableTooltips())}),e.click(function(){$(this).attr("checked")?(f.attr("checked",!1),c1.enableLegend()):(f.attr("checked",!0),c1.disableLegend())}),f.click(function(){$(this).attr("checked")?(e.attr("checked",!1),c1.disableLegend()):(e.attr("checked",!0),c1.enableLegend())})})