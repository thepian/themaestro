(function($){
    $.fn.uploadform = function(options) {
        // Turn the supplied list into a upload button form
        return new $.fn.uploadform.instance(this,options);
    };
    
    $.fn.uploadform.instance = function(query,options) {
        this.query = query;
        this.options = options;
        
        this.file_input = $("#id_file",query);
        this.upload_iframe = $('iframe[name=upload_frame]', query);
        
        this.file_input.change(function(){ this.form.submit(); });
        this.upload_iframe.bind("load",this,this.options.after_iframe_load);
    };
    
    $.extend( $.fn.uploadform.instance.prototype, {
        
    });
    
    function onload_script(event) {
        var options = event.data;
        if (options.after_load) {
            options.after_load.call(this,event);
            $(this).unbind("load",onload_script);
            $(this).unbind("onreadystatechange",onreadystatechange_script);
            options.after_load = null;
        }
    }
    function onreadystatechange_script(event){
        var options = event.data;
        if (this.readyState == "loaded") {
            onload_script.call(this,event);
        }
    }
    
    $.fn.reload_script = function(options) {   
      // Run function on the scripts to be reloaded     
      return this.each(function() { 
        var parent = this.parentNode; 
        var old_src = this.src, old_id = this.id, old_name = this.getAttribute("name");
    	$(this).remove();
    	var newscript = $(document.createElement("SCRIPT"));
    	newscript.attr("type","text/javascript"); 
    	if (old_id) newscript.attr("id",old_id);
    	if (old_name) newscript.attr("name",old_name);
    	newscript.attr("src",old_src.split("?")[0]+ "?_="+new Date().getTime());
    	//if (window.console) console.log('new script: '+newscript.attr("src"));
    	newscript.bind("onreadystatechange",options,onreadystatechange_script);
    	newscript.bind("load",options,onload_script);
    	parent.appendChild(newscript[0]);
      });  
    };  
})(jQuery);

/*

$().bind("load",function(){
	$('script[name=entity.js]').reload_script({
	    "after_load":function() { portfolio.render(); }
	});
});

*/