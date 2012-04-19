<script type="text/javascript"><?php readfile("js/miscstats.min.js");?></script>

<h1>Miscellaneous stats <span id="update_data"></span></h1>


<?php /*
<div class="row" style="padding-top:2em">
	<div class="span12"><h2>Your usage</h2></div>
</div>

<div class="row">
	<div class="span2" rel="popover" data-original-title="What?" data-content="This is the number of pageviews server has recorded for your current session. Application cache reduces actual page loads from the server greatly.">
		<h2><small>Pageviews</small></h2>
		<h2 id="your_session_web_pageview"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2" rel="popover" data-original-title="What?" data-content="This is the number of page views from your IP - it might include others too.">
		<h2><small>... from your IP</small></h2>
		<h2 id="your_ip_web_pageview"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2" rel="popover" data-original-title="What?" data-content="Number of static files your browser has downloaded.">
		<h2><small>Static files</small></h2>
		<h2 id="your_session_static_served"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2" rel="popover" data-original-title="What?" data-content=".. and number of static files from your IP address.">
		<h2><small>... from your IP</small></h2>
		<h2 id="your_ip_static_served"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2" rel="popover" data-original-title="What?" data-content="Number of data files (for example, service status information) your browser has downloaded so far.">
		<h2><small>Data files</small></h2>
		<h2 id="your_session_web_json_processed"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2" rel="popover" data-original-title="What?" data-content="Number of data files downloaded from your current IP address.">
		<h2><small>... from your IP</small></h2>
		<h2 id="your_ip_web_json_processed"><span class="loading-inline-gif"></span></h2>
	</div>

</div>
<hr>
*/?>
<div class="row" style="padding-top:2em">
	<div class="span12"><h2>Web</h2></div>
</div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="So low?" data-content="Due to application cache, each user typically loads whole site only once.">
		<h2><small>Pageviews</small></h2>
		<h2 id="stats_web_pageview"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of data files served">
		<h2><small>JSON files served</small></h2>
		<h2 id="stats_web_json_processed"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Server sent events is a system for sending notices to browser.">
		<h2><small>SSE started</small></h2>
		<h2 id="stats_web_sse_started"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of invalid requests (missing mandatory parameters etc.)">
		<h2><small>Invalid requests</small></h2>
		<h2 id="stats_web_invalid"><span class="loading-inline-gif"></span></h2>
	</div>
</div>

<hr>
<div class="row">
	<div class="span12"><h2>Backend</h2></div>
</div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of requests to Pingdom and Twitter">
		<h2><small>API requests</small></h2>
		<h2 id="stats_api_request"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Cache hits for backend components: number of requests which were retrieved from cache">
		<h2><small>Cache hits</small></h2>
		<h2 id="stats_cache_hit"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Cache misses for backend components: number of requests which were not retrieved from cache">
		<h2><small>Cache miss</small></h2>
		<h2 id="stats_cache_miss"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of cache updates">
		<h2><small>Cache set</small></h2>
		<h2 id="stats_cache_set"><span class="loading-inline-gif"></span></h2>
	</div>
</div>

<hr>
<div class="row">
	<div class="span12"><h2>Server</h2></div>
</div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Time since last reboot">
		<h2><small>Uptime</small></h2>
		<h2 id="stats_server_uptime_readable"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Server load indicates responsiveness of the server. Lower value is better.">
		<h2><small>Server load</small></h2>
		<h2 id="stats_server_load_1m"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Amount of network traffic since last reboot.">
		<h2><small>Network traffic</small></h2>
		<h2 id="stats_server_net_eth0_total_readable"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of items in redis cache">
		<h2><small>redis items</small></h2>
		<h2 id="stats_redis_db0_keys"><span class="loading-inline-gif"></span></h2>
	</div>
</div>
<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Total number of redis commands since last redis restart">
		<h2><small>redis commands</small></h2>
		<h2 id="stats_redis_total_commands_processed"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Redis memory usage">
		<h2><small>redis memory usage</small></h2>
		<h2 id="stats_redis_used_memory_human"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of hits (queries for keys that existed)">
		<h2><small>redis hits</small></h2>
		<h2 id="stats_redis_keyspace_hits"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of misses (queries for keys that didn't exist)">
		<h2><small>redis misses</small></h2>
		<h2 id="stats_redis_keyspace_misses"><span class="loading-inline-gif"></span></h2>
	</div>
</div>

<hr>
<div class="row" style="padding-top:2em">
	<div class="span12"><h2>Your browser</h2></div>
</div>
<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Event source provides instant updates to page content. All modern browsers support it (not Internet Explorer).">
		<h2><small>Event source</small></h2>
		<h2 id="your_browser_eventsource"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Local storage provides a way to store data on your computer - in this service it's for shorter page loading times.">
		<h2><small>localStorage</small></h2>
		<h2 id="your_browser_localstorage"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Desktop notifications show small notification on your desktop when some service goes down. You have to specifically allow these - it's off by default.">
		<h2><small>Desktop notifications</small></h2>
		<h2 id="your_browser_notifications"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Application cache stores whole site (just about 2MB, it's pretty small) on your browser, which means very or instant fast page loads">
		<h2><small>Application cache</small></h2>
		<h2 id="your_browser_appcache"></h2>
	</div>
</div>

<div class="row" style="padding-top: 2em">
	<div class="span12">
		<ul class="thumbnails" id="graphs">
		</ul>
	</div>
</div>
