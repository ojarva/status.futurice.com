<h1>IT tickets</h1>
<style type="text/css" media="screen">
            #dotschart, #workflowchart {
                width: 100%;
                _width: 500px;
                overflow: auto;
                clear: left;
            }
            .invisible {
                visibility: hidden;
            }
            .hidden {
                display: none;
            }
            #legend,
            #legend2 {
                -moz-border-radius: 2px;
                -webkit-border-radius: 2px;
                width: 1em;
                height: 1em;
                border: solid 1px #000;
                margin-right: .3em;
                line-height: 1;
            }
            #name,
            #name2 {
                float: left;
                clear: left;
            }
            #name div,
            #name2 div {
                float: left;
            }
            #placeholder {
                clear: left;
                color: #999;
            }
            em {
                color: #666;
                font-style: normal;
            }
        </style>
<script type="text/javascript">
ticketdata = <?
include("ittickets.json");
?>

ticketdata = ticketdata.data;

$(document).ready(function() {
 $("#total-tickets-popover").data('content', "This is the total number of tickets since March 2010 ("+moment("2010-03-15", "YYYY-MM-DD").fromNow()+"), including automatic messages");
 $("#total-tickets-popover").data("original-title", "What?")
 $("#total-tickets-popover").data("placement", "top");
 $("#total-tickets-popover").attr("rel", "popover");
 $("#total-tickets-popover").popover();
 for (key in ticketdata) {
  if ($("#"+key) != null) {
    $("#"+key).html(ticketdata[key])
  }
 }

$("#workflowchart").slideUp();

$("#dots_all").addClass("btn-info");
$("#dotschart").dotsgraph({"data": ticketdata.dots.all});
$("#dotschart").dotsgraph("update");


$(".dots-btn").click(function() {
 if ($(this).hasClass("btn-info")) {
  return;
 }
 $("#dotschart").slideDown();
 $("#workflowchart").slideUp();
 dictname = $(this).data("name");
 $("#dotschart").dotsgraph({"data": ticketdata["dots"][dictname]});
 $("#dotschart").dotsgraph("update");
 $(".dots-btn").removeClass("btn-info");
 $("#change_graph").removeClass("btn-info");
 $(this).addClass("btn-info");
 $("#placeholder").html("mouse over the circles for more details");
 $("#placeholder").removeClass("hidden");
 $("#name2").addClass("hidden");
});

$("#change_graph").click(function() {
 $("#placeholder").html("mouse over the graph for more details");
 $("#dotschart").slideUp();
 $("#workflowchart").html("");
 process(ticketdata.workflow);
 $("#workflowchart").removeClass("hidden");
 $("#workflowchart").slideDown();
 $(".dots-btn").removeClass("btn-info");
 $(this).addClass("btn-info");
});

emailpie_values = [ticketdata.other_users, ticketdata.futurice_users];
emailpie_labels = ["External", "Internal"];
Raphael("emailpieholder", 400, 200).pieChart(180, 100, 69, emailpie_values, emailpie_labels, "#fff");
});
</script>
<div class="row">
	<div class="span12">
		<div class="btn-group">
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
        <div id="dotschart"></div>
        <div id="workflowchart" class="hidden"></div>
</div></div>

<div class="row">
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of new tickets. New tickets are not yet acknowledged. For example, it might be assigned to someone who didn't read it yet." data-placement="top">
		<h2><small>New tickets</small></h2>
		<h2 id="new_tickets"></h2>
	</div>
	<div class="span3" rel="popover" data-original-title="What?" data-content="This is the number of currently open ticket. New tickets are not yet acknowledged" data-placement="top">
		<h2><small>Open tickets</small></h2>
		<h2 id="open_tickets"></h2>
	</div>
	<div class="span3" id="total-tickets-popover">
		<h2><small>Total number of tickets</small></h2>
		<h2 id="all_tickets"></h2>
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
		<h2 id="unique_manual_7d"></h2>
	</div>
	<div class="span2">
		<h2><small>Last 30 days</small></h2>
		<h2 id="unique_manual_30d"></h2>
	</div>
	<div class="span2">
		<h2><small>Last 365 days</small></h2>
		<h2 id="unique_manual_365d"></h2>
	</div>
	<div class="span2">
		<h2><small>All-time</small></h2>
		<h2 id="unique_manual"></h2>
	</div>
</div>

<div class="row" style="padding-top:2em">
	<div class="span4">
		<h1>Ticket sources</h1>
		<div id="emailpieholder"></div>
	</div>
</div>

