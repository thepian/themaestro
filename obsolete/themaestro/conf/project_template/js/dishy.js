dishy = {

	owner:'codepo8',
	fontMin:13,
	fontMax:30,
	amountOfTags:20,
	showAmount:true,
	callback:null,

	tagHTML:[],
	tagFeed:[],

	getLatest:function(){
		var url = 'http://del.icio.us/feeds/json/'+dishy.owner+'?raw&callback=dishy.feedLatest';
		dishy.engage(url);
	},
	feedLatest:function(o){
		dishy.latest=o;
		var out = dishy.xFolkify(o);
		dishy.latestHTML=out;
		if(dishy.callback !== null){
			eval(dishy.callback+'()');
			dishy.callback = null;
		}
	},

	getByTag:function(tag){
		var url = 'http://del.icio.us/feeds/json/'+dishy.owner+'/'+tag+'?raw&callback=dishy.feedByTag';
		dishy.currentTag=tag;
		dishy.engage(url);
	},	
	feedByTag:function(o){
		dishy.tagFeed[dishy.currentTag]=o;
		var out = dishy.xFolkify(o);
		dishy.tagHTML[dishy.currentTag] = out;
		if(dishy.callback !== null){
			eval(dishy.callback+'()');
			dishy.callback = null;
		}
	},

	getTags:function(){
		var url = 'http://del.icio.us/feeds/json/tags/'+dishy.owner+'?raw';
		if(dishy.amountOfTags!==null){url+='&count='+dishy.amountOfTags;}
		url+='&sort=alpha&callback=dishy.feedTags';
		dishy.engage(url);
	},
	feedTags:function(o){
		dishy.tags=o;
		var out = [];
		for (var k in o) {
			if(o[k]<dishy.fontMin){
				var size = dishy.fontMin;
			} 
			if(o[k]>dishy.fontMin){
				var size = dishy.fontMax;
			} 
			if(o[k]>dishy.fontMin && o[k]<dishy.fontMax){
				var size = o[k];
			} 
			var tag = '<a rel="tag" style="font-size:'+size+'px" href="http://del.icio.us/'+dishy.owner+'/'+k+'">'+k;
			tag+= dishy.showAmount===true?'('+o[k]+')':'';
			tag+='</a> ';
			out.push(tag);
		}
		out = out.join('');
		dishy.tagsHTML=out;
		if(dishy.callback !== null){
			eval(dishy.callback+'()');
			dishy.callback = null;
		}
	},

	engage:function(url){
		var s = document.createElement('script');
		s.setAttribute('src', url);
		document.getElementsByTagName('head')[0].appendChild(s);
	},
	xFolkify:function(o){
		var out = [];
		for (var k in o) {
			var entry ='<li class="xfolkentry"><a class="taggedlink" href="'+o[k].u+'">'+o[k].d+'</a>';
			if(o[k].n!==undefined){
				entry+= '<p class="description">'+o[k].n+'</p>';
			}
			if(o[k].t){
				entry+='<ul class="meta">';
				for(var i=0;i<o[k].t.length;i++){
					entry+='<li><a rel="tag" href="http://del.icio.us/'+dishy.owner+'/'+o[k].t[i]+'">'+o[k].t[i]+'</a></li>'
				}
				entry+='</ul></li>';
				out.push(entry);
			}
		}
		out = out.join('');
		return out;
	}
}
