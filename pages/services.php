<script src="/js/combined.raphael.min.js"></script>
<script type="text/javascript" src="/js/services.min.js"></script>

<h1>Overview of service status <span id="update_data"></span> <button id="notification_permissions" class="btn btn-info">Show notifications</button></h1>

<div class="row">
<div class="span2">
<h2><small>Overall</small></h2>
<h2 id="overall"><span class="loading-inline-gif"></span></h2>
</div>

<div class="span2" rel="popover" data-original-title="What?" data-content="This is number of outages today over all services. Even very short breaks counts." data-placement="bottom">
<h2><small>Outages today</small></h2>
<h2 id="outages_today"><span class="loading-inline-gif"></span></h2>
</div>

<div class="span2">
<h2><small>Networks uptime</small></h2>
<h2 id="networks"><span class="loading-inline-gif"></span></h2>
</div>

<div class="span3">
<h2><small>Virtualization platforms</small></h2>
<h2 id="virtualization_platforms"><span class="loading-inline-gif"></span></h2>
</div>

<div class="span2">
<h2><small>Websites</small></h2>
<h2 id="websites"><span class="loading-inline-gif"></span></h2>
</div>

</div>

<div class="row"><div class="span12">
<ul class="nav nav-tabs" style="padding-top: 2em">
<li class="active"><a href="#checks-summary-table" data-toggle="tab">Summary</a></li>
<li><a href="#checks-overview-table" data-toggle="tab">Overview</a></li>
</ul>

<div class="tab-content">
<div class="tab-pane fade in active" id="checks-summary-table">
<div class="row" style="padding-top:0.2em" id="checks-summary-container">
<div class="span6">

<h2 id="status-text"></h2>
<table id="checks-normal" class="dt table table-bordered table-striped">
<thead>
<tr>
<th>Name</th>
<th>Status</th>
<th>Response times</th>
<th>Uptime</th>
</tr>
</thead>
<tbody id="checks-summary-tbody">
<tr><td colspan="4"><center><img class="loading-indicator" src="/img/loading.gif"></center></td></tr>
</tbody>
</table>
</div>
</div>
</div>
<div class="tab-pane fade" id="checks-overview-table">
<div class="row" style="padding-top:0.2em; display:" id="checks-overview-container">
<div class="span10">

<table id="checks-overview" class="dt table table-bordered table-striped">
<colgroup><col width="30">
<col width="300">
</colgroup>

<thead>
<tr><th class="check-status"></th><th class="check-name">Name</th>
<th class="">Response time</th>
<th class="check-day check-day-title sorting">-</th>
<th class="check-day check-day-title sorting">-</th>
<th class="check-day check-day-title sorting">-</th>
<th class="check-day check-day-title sorting">-</th>
<th class="check-day check-day-title sorting">-</th>
<th class="check-day check-day-title sorting">-</th>
<th class="check-day check-day-title sorting">-</th>
</tr>
</thead>

<tbody id="checks-overview-tbody">
<tr><td colspan="9"><center><img class="loading-indicator" src="/img/loading.gif"></center></td></tr>
</tbody></table>
</div>
</div>
</div> <!-- tab-pane -->
</div> <!-- tab-content -->
</div> <!-- span12 -->
</div> <!-- row -->
