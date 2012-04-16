<script src="/js/combined.raphael.min.js"></script>
<script type="text/javascript"><?readfile("js/servicedetails.min.js");?></script>

<ul class="breadcrumb">
  <li>
    <a href="/page/services">Services</a> <span class="divider">/</span>
  </li>
  <li class="active">Service details</li>
</ul>

<h1>Details for service <span id="name"></span> <span id="update_data"></span></h1>

<div class="row">
	<div class="span2">
		<h2><small>Status</small></h2>
		<h2 id="status"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2">
		<h2><small>Response time</small></h2>
		<h2><span id="lastresponsetime"><span class="loading-inline-gif"></span></span>ms</h2>
	</div>
	<div class="span3">
		<h2><small>Last check</small></h2>
		<h2 id="last_check" class="automatic-moment"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3">
		<h2><small>Last error</small></h2>
		<h2 id="last_error" class="automatic-moment"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2">
		<h2><small>Test type</small></h2>
		<h2 id="type"><span class="loading-inline-gif"></span></h2>
	</div>
</div>

<div class="row" style="padding-top:2em">
	<div class="span12">
		<h2>Response times</h2>
	</div>
</div>
<div class="row">
	<div class="span12">
	 	<div id="response_graph"><img src="/img/loading.gif"></div>
	</div>
</div>

<div class="row">
	<div class="span12">
		<h2>Uptime</h2>
	</div>
</div>
<div class="row">
	<div class="span12">
		<div id="uptime_graph"><img src="/img/loading.gif"></div>
	</div>
</div>
