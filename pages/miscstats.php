<script type="text/javascript"><?=readfile("js/miscstats.min.js");?></script>

<h1>Miscellaneous stats <span id="update_data"></span></h1>

<div class="row">
	<div class="span12"><h2>Web</h2></div>
</div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="So low?" data-content="Due to application cache, each user typically loads whole site only once.">
		<h2><small>Pageviews</small></h2>
		<h2 id="stats_web_pageview"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of data files served">
		<h2><small>JSON files served</small></h2>
		<h2 id="stats_web_json_processed"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Server sent events is a system for sending notices to browser.">
		<h2><small>SSE started</small></h2>
		<h2 id="stats_web_sse_started"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of invalid requests (missing mandatory parameters etc.)">
		<h2><small>Invalid requests</small></h2>
		<h2 id="stats_web_invalid"><img src="/img/loading-inline.gif"></h2>
	</div>
</div>

<hr>
<div class="row">
	<div class="span12"><h2>Backend</h2></div>
</div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of requests to Pingdom and Twitter">
		<h2><small>API requests</small></h2>
		<h2 id="stats_api_request"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Cache hits for backend components: number of requests which were retrieved from cache">
		<h2><small>Cache hits</small></h2>
		<h2 id="stats_cache_hit"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Cache misses for backend components: number of requests which were not retrieved from cache">
		<h2><small>Cache miss</small></h2>
		<h2 id="stats_cache_miss"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of cache updates">
		<h2><small>Cache set</small></h2>
		<h2 id="stats_cache_set"><img src="/img/loading-inline.gif"></h2>
	</div>
</div>

<hr>
<div class="row">
	<div class="span12"><h2>Server</h2></div>
</div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Time since last reboot">
		<h2><small>Uptime</small></h2>
		<h2 id="stats_server_uptime_readable"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Server load indicates responsiveness of the server. Lower value is better.">
		<h2><small>Server load</small></h2>
		<h2 id="stats_server_load_1m"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Amount of network traffic since last reboot.">
		<h2><small>Network traffic</small></h2>
		<h2 id="stats_server_net_eth0_total_readable"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of items in redis cache">
		<h2><small>redis items</small></h2>
		<h2 id="stats_redis_db0_keys"><img src="/img/loading-inline.gif"></h2>
	</div>
</div>
<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="Total number of redis commands since last redis restart">
		<h2><small>redis commands</small></h2>
		<h2 id="stats_redis_total_commands_processed"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Redis memory usage">
		<h2><small>redis memory usage</small></h2>
		<h2 id="stats_redis_used_memory_human"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of hits (queries for keys that existed)">
		<h2><small>redis hits</small></h2>
		<h2 id="stats_redis_keyspace_hits"><img src="/img/loading-inline.gif"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="Number of misses (queries for keys that didn't exist)">
		<h2><small>redis misses</small></h2>
		<h2 id="stats_redis_keyspace_misses"><img src="/img/loading-inline.gif"></h2>
	</div>
</div>
