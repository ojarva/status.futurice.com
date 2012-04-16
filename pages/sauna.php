<script type="text/javascript"><?readfile("js/sauna.min.js");?></script>


<h1>Helsinki office sauna <span id="update_data"></span></h1>


<div class="row">
	<div class="span11">
		<h1 style="line-height:100px;font-size:100px"><span id="sauna_current"><span class="loading-inline-gif"></span></span>&deg;C <small id="sauna_trend" style="font-size:80px;color: #999;"></small></h1>
	</div>
</div>

<div class="row">
	<div class="span11">
		<div id="etacalc"></div>
	</div>
</div>

<div class="row" style="padding-top:2em">
	<div class="span12">
		<div class="btn-group" data-toggle="buttons-radio">
			<button class="btn graph-timerange" data-timeh="2">2h</button>
			<button class="btn graph-timerange active" data-timeh="6">6h</button>
			<button class="btn graph-timerange" data-timeh="24">24h</button>
			<button class="btn graph-timerange" data-timeh="168">7d</button>
		</div>
	</div>
</div>
<div class="row" style="padding-top:1em">
	<div class="span12">
		<img width="500" height="300" id="temperature_graph" data-src="/graph/sauna.php" data-width="500" data-height="300" data-range="6" data-graphmode="normal" src="/graph/sauna.php">
	</div>
</div>
