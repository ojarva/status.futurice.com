<style type="text/css" media="screen">
            #dotschart, #workflowchart {
                width: 100%;
                _width: 500px;
                overflow: auto;
                clear: left;
            }
            .hidden {
                display: none;
            }
            #name2 {
                float: left;
                clear: left;
            }
            #name2 div {
                float: left;
            }
            #placeholder {
                clear: left;
                color: #999;
            }
</style>

<script src="/js/combined.raphael.min.js"></script>
<script type="text/javascript"><?readfile("js/ittickets.min.js");?></script>

<h1>IT tickets <span id="update_data"></span></h1>

<div class="row">
	<div class="span12">
		<div class="btn-group" data-toggle="buttons-radio">
			<button rel="popover" data-original-title="What?" data-content="This includes all tickets, also automatically generated warnings, information messages and errors." data-placement="bottom"  data-name="all" id="dots_all" class="btn dots-btn">All tickets by creation time</button>
			<button rel="popover" data-original-title="What?" data-content="This shows resolve times (time when ticket was marked as resolved) for all tickets" data-placement="bottom" data-name="all_resolved" id="dots_all_resolved" class="btn dots-btn">All tickets by resolve time</button>
			<button rel="popover" data-original-title="What?" data-content="This shows only tickets created by human being. Practically all machine generated tickets are removed." data-placement="bottom" data-name="manual" id="dots_manual" class="btn dots-btn">Non-automatic tickets by creation time</button>
			<button rel="popover" data-original-title="What?" data-content="This shows resolve time (time when ticket was marked as resolved) for tickets created by human being" data-placement="bottom" data-name="manual_resolved" id="dots_manual_resolved" class="btn dots-btn">Non-automatic tickets by resolve time</button>
			<button rel="popover" data-original-title="What?" data-content="This is stream graph for per week ticket actions." data-placement="bottom" id="change_graph" class="btn">Streamgraph</button>
		</div>
	</div>
</div>
<div class="row">
<div class="span12">
        <div id="name2" class="hidden">
            <div id="legend2">&nbsp;</div>
            <div id="username2">legend</div>
        </div>
        <div id="placeholder">mouse over the circles for more details</div>
        <div id="dotschart"><img src="/img/loading.gif"></div>
        <div id="workflowchart" class="hidden"></div>
</div></div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of new tickets. New tickets are not yet acknowledged. For example, it might be assigned to someone who didn't read it yet." data-placement="top">
		<h2><small>New tickets</small></h2>
		<h2 id="new_tickets"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of currently open ticket. New tickets are not yet acknowledged" data-placement="top">
		<h2><small>Open tickets</small></h2>
		<h2 id="open_tickets"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span3" data-content="This is the total number of tickets since March 2010, including automatic messages" data-original-title="What?" data-placement="top">
		<h2><small>Total number of tickets</small></h2>
		<h2 id="all_tickets"><span class="loading-inline-gif"></span></h2>
	</div>
</div>


<div class="row" style="padding-top:2em">
	<div class="span6" rel="popover" data-original-title="What?" data-content="These are tickets with unique title coming from real people instead of from automatic systems">
		<h1>Received tickets</h1>
	</div>
</div>
<div class="row">
	<div class="span2">
		<h2><small>Last 7 days</small></h2>
		<h2 id="unique_manual_7d"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2">
		<h2><small>Last 30 days</small></h2>
		<h2 id="unique_manual_30d"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2">
		<h2><small>Last 365 days</small></h2>
		<h2 id="unique_manual_365d"><span class="loading-inline-gif"></span></h2>
	</div>
	<div class="span2">
		<h2><small>All-time</small></h2>
		<h2 id="unique_manual"><span class="loading-inline-gif"></span></h2>
	</div>
</div>

<div class="row" style="padding-top:2em">
	<div class="span4">
		<h1>Ticket sources</h1>
		<div id="emailpieholder"><img src="/img/loading.gif"></div>
	</div>
</div>

