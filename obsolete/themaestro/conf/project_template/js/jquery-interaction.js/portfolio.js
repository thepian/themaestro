/*
porfolio.js
*/
(function($){
    var current_asset;
    var image_cache = {};
    
    function add_cached_image(asset) {
        var cached_img = document.createElement("IMG");
        cached_img.src = asset.still_url;
        image_cache[asset.path] = cached_img;        
    }
    
    function image_loaded(event) {
        var portfolio = event.data;
        // naturalHeight, naturalWidth present on Mozilla only
        var w = portfolio.current_still.attr("width");
        var h = portfolio.current_still.attr("height");
        var nh = Math.floor(h / (w/portfolio.options.current_width));
        portfolio.current_still.attr("width",portfolio.options.current_width).attr("height",nh);
        var has = portfolio.current_asset.hasClass("loading-unavailable");
        portfolio.current_asset.removeClass("loading-still video blank loading-unavailable").addClass(has?"unavailable":"still");
    }
    
    function change_current(event) {
        var portfolio = event.data;
        var target = $(event.target);
        if (event.target.tagName == "IMG") {
            var id = target.attr("asset_id");
            portfolio.select_asset(window.assets[id]);
        }
    }
    
    function render_playlist(entity,item_template) {
        var h = [];
        for(var i=0,l=entity.assets.length;i<l;++i) {
            var a = window.assets[entity.assets[i]];
            h.push(item_template.apply({
                "thumb_url":a.thumb_url,
                "video_url": a.video_url,
                "title": a.name,
                "asset_id":a.path,
                "clip_index": i
            }));
        }
        $("#main div.vertical-scrollable ol.items").html(h.join(''));
        flowplayer().playlist("#main div.vertical-scrollable ol.items a:first");
    }
    


    $.fn.portfolio = function(options) {
        // Turn the supplied list into a portfolio browser
        return new $.fn.portfolio.instance(this,options);
    };
    
    $.fn.portfolio.instance = function(query,options) {
        this.query = query;
        this.options = options;
        this.loaded = false;
        
        /*
        this.player_id = options.player_id;
        this.paging = $(options.paging);
        this.current_still = $(options.current+" img.still");
        this.current_stillmsg = $(options.current+" div.still-msg");
        this.current_video = $(options.current+" div.video");
        this.item_template = options.item_template;
        */
    };
    
    $.extend( $.fn.portfolio.instance.prototype, {
        load: function() {
            this.current_asset = $(this.options.current_asset,this.query);
            this.video = $(this.options.video,this.query);
            this.current_still = $("img.still",this.current_asset);
            this.playlist = $(this.options.playlist,this.query);
            this.item_template = $.template(this.options.item_template);
            this.flowplayer = this.video.flowplayer(this.options.flowplayer_url,{
                plugins: this.options.flowplayer_plugins
            });
            this.loaded = true;
        },
        render: function(entity) {
            if (!this.loaded) this.load();
            this.render_playlist(entity);
            if (entity.assets.length) {
                var firstAsset = window.assets[entity.assets[0]];
                this.select_asset(firstAsset);
            }
        },
        
        render_playlist: function(entity) {
            var h = [];
            for(var i=0,l=entity.assets.length;i<l;++i) {
                var a = window.assets[entity.assets[i]];
                h.push(this.item_template.apply({
                    "thumb_url":a.thumb_url,
                    "video_url": a.video_url,
                    "title": a.name,
                    "asset_id":a.path,
                    "category":a.original_category,
                    "clip_index": i
                }));
            }
            $("ol.items",this.playlist).html(h.join(''));
            $("ol.items a",this.playlist).bind("click",this,this.item_clicked);
            //this.video.playlist("#main div.vertical-scrollable ol.items a:first");
        },
        
        item_clicked: function(event) {
            /* NOT A METHOD OF PORTFOLIO */
            // this = anchor
            var portfolio = event.data;
            var asset_id = $(this).attr("asset_id");
            if (asset_id) portfolio.select_asset(window.assets[asset_id]);
            return false;
        },
               
        select_asset: function(asset) {
            if (asset) {
                if (asset.original_category == "image") {
                    add_cached_image(asset);
                    this.flowplayer.stop();
                    this.current_still.removeAttr("width").removeAttr("height");
                    this.current_still.attr("src",asset.still_url).bind("load",this,image_loaded);
                    this.current_asset.removeClass("still video blank unavailable loading-unavailable").addClass("loading-still");
                } else if (asset.original_category == "video") {
                    this.current_asset.removeClass("loading-still still blank unavailable loading-unavailable").addClass("video");
                    if (asset.status == "ready") {
                        try {
                    		var clip = flowplayer(this.video[0]).play(asset.video_url);
                        }
                        catch(e) {
                            debugger;
                        }
                		//TODO set height 360px or whatever appropriate
                    } else {
                        add_cached_image(asset);
                        this.current_video.flowplayer(0).stop();
                        this.current_still.removeAttr("width").removeAttr("height");
                        this.current_still.attr("src",asset.still_url).bind("load",this,image_loaded);
                        this.current_asset.removeClass("still video blank unavailable loading-still").addClass("loading-unavailable");
                        this.current_stillmsg.html("Video unavailable");
                    }
                } else {
                    this.current_asset.removeClass("loading-still still video unavailable loading-unavailable").addClass("blank");
                    current_asset = undefined;
                    return;
                }
                current_asset = asset;
            }
            else {
                this.current_asset.removeClass("loading-still still video unavailable loading-unavailable").addClass("blank");
                current_asset = undefined;
            }
            
        }
    });
})(jQuery);
