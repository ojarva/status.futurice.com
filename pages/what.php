
<div class="hero-unit">
<h1>What and why?</h1>

<p>Many things can be improved only by taking very small. And many things require great amount of work, money and 
goodwill. Also, many small things bring in much greater advantages. If this site inspires even few others to 
share, it's already a good start.</p>

</div>


<div class="row">
	<div class="span4">
		<h3>Transparency</h3>
		<p>One of the central themes at Futurice is transparency. We can't build the best workplace in the Finland by not being open and honest. It really counts.</p>
	</div>
	<div class="span4">
		<h3>Relevant information</h3>
		<p>Information shared here is relevant for employees and clients. For others, it might be interesting. And it shows a way to be a little bit more open.</p>
	</div>
	<div class="span4">
		<h3>Do new things</h3>

		<p>Too many things are being done certain way just because "that's how it has always
been done". That's not how we can improve our work, our results and our environment. It's important to
experiment.</p>

	</div>
</div>

<?
$images = glob("img/carousel/full/*.jpg");
if ($images != false && count($images) > 0) {
?>
<div class="row">
	<div class="span12">
		<div id="carousel" class="carousel">
			<div class="carousel-inner">
<?
shuffle($images);
foreach ($images as $k => $v) {
?><div class="<?if ($k == 0) {?>active <?}?>item"><img src="/<?=$v;?>"></img></div><?
}
?>
			</div>
			<a class="carousel-control left" href="#carousel" data-slide="prev">&lsaquo;</a>
			<a class="carousel-control right" href="#carousel" data-slide="next">&rsaquo;</a>
		</div>
	</div>
</div>


<script type="text/javascript">
$(document).ready(function() {
$("#carousel").carousel();
});
</script>

<?}?>

<h2>For nerds</h2>

<div class="row">
	<div class="span4">
		<h3>General</h3>

		<p>Site is powered by bootstrap, jQuery, python and php running on Amazon EC2. All data is stored on redis database, except binary files (network map). All redis keys have expiration time, and redis is 
configured with <i>maxmemory</i> directive. If key name is changed, redis cleans up automatically after a while. </p>

		<h3>Services</h3>

		<p>Services are monitored using <a href="http://pingdom.com">Pingdom</a>. In addition to 
Pingdom, we use <a href="http://www.zabbix.com/">Zabbix</a> internally. Pingdom provides public 
information pages, but those are rather limited, so we are using <a 
href="http://pingdom.com/services/api-documentation-rest/">API</a> to fetch information to local copy 
(JSON files in <a href="http://redis.io/">redis</a>). Tooltips are provided by <a 
href="http://twitter.github.com/bootstrap/javascript.html#tooltips">Bootstrap plugin</a>. If we are doing 
a good job with keeping our services up, we can be proud of it, and if not, we need to improve.</p>

		<p>Traditionally monitoring and uptime information is secret, but we didn't find any 
reason to continue this tradition. Security can't depend on secret hostnames or other details, so 
releasing status information is not a problem. Actually, we are not using split-horizon DNS at all. But 
we restrict all access to important internal servers (for example LDAP) and services (user management and 
so on) with firewalls.</p>

	</div>
	<div class="span4">
		<h3>Network map</h3>

		<p>Network map generation is handled by <a 
href="http://www.network-weathermap.com/">Network weathermap</a>. It's not actively maintained, but 
mature enough for our use - and we couldn't find anything better. Traffic data is collected using <a 
href="http://oss.oetiker.ch/mrtg/">MRTG</a>. Our internal server collects traffic data, generates image 
and posts it to this server. Data is not realtime, and doesn't include for example security related 
backup links or networks.</p>

		<p>We had discussions about releasing network structure and services information - main 
argument against was that all additional information might have surprising effects when collected 
together. We tried to release as much as possible without giving out anything too specific - all you can 
see here is available using normal network scanning tools.</p>

	</div>
	<div class="span4">
		<h3>IT tickets</h3>

		<p>Our IT team uses <a href="http://bestpractical.com/rt/">RT</a> for tracking incoming 
emails. RT API wasn't good enough (we are not fan of Perl), so currently small program runs queries 
directly to MySQL database, fetches information, calculates aggregates and posts resulting data to this 
server. No access is allowed other way around.</p>

		<p>When Futurice was smaller, we had just mailing list, and all emails went to all three 
members of IT team. Nowadays that's not feasible anymore. We highly recommend taking ticket tracking 
system into use even in smaller organizations. Using ticket tracking system doesn't necessarily mean 
adding complex process to handling incoming emails.</p>

	</div>
	<div class="span4">
		<h3>Printers</h3>

		<p>Printer information is fetched using SNMP, processed with Python and pushed to 
this server.</p>

		<p>It's hard to know what printer works right now, or is there a need for ordering 
some printer supplies. We have few printers around our offices, because unfortunately not everything 
can be handled electronically. Even though printers are on 24/7, power saving mode saves electricity 
quite a bit.</p>


	</div>
</div>


<div class="row">
	<div class="span4">
		<h3>Frontend stack</h3>
		<p>This service is built on following blocks:</p>
		<ul>
			<li><a href="http://twitter.github.com/bootstrap/">Bootstrap (UI)</a></li>
			<li><a href="http://momentjs.com/">MomentJS</a></li>
			<li><a href="http://raphaeljs.com/">Raphael</a></li>
			<li><a href="https://github.com/ac3522/raphael-sparkline">Raphael sparklines</a></li>
			<li><a href="http://raphaeljs.com/github/dots.html">Raphael dots demo</a></li>
			<li><a href="http://raphaeljs.com/growing-pie.html">Raphael pie demo</a></li>
			<li><a href="http://raphaeljs.com/github/impact.html">Raphael impact demo</a></li>
			<li><a href="http://jquery.com/">jQuery</a></li>
			<li><a href="http://documentcloud.github.com/underscore/">underscore.js</a></li>
			<li><a href="http://handdrawing.olawolska.com/">Hand drawing icons set by Aleksandra Wolska</a></li>
		</ul>
                <p>And using following tutorials/documents:</p>
		<ul>
			<li><a href="http://www.html5rocks.com/en/tutorials/appcache/beginner/">Application cache</a></li>
			<li><a href="http://www.html5rocks.com/en/tutorials/eventsource/basics/">Server-sent events</a> and <a href="http://www.w3.org/TR/eventsource/">W3 EventSource draft</a></li>
			<li><a href="http://www.w3.org/TR/notifications/">Web notifications</a></li>
		</ul>
	</div>
	<div class="span4">
		<h3>Backend stacks</h3>
		<p>Backend (data collection and generation) for this service is built on following blocks:</p>
		<ul>
			<li><a href="http://python.org/">Python</a></li>
			<li><a href="https://github.com/EA2D/pingdom-python">Modified version of EA2Ds pingdom-python wrapper</a></li>
			<li><a href="http://www.pingdom.com/services/api-documentation-rest/">Pingdom API</a></li>
			<li><a href="http://www.network-weathermap.com/">Network weathermap</a></li>
			<li><a href="http://bestpractical.com/rt/">RT (Request Tracker)</a></li>
			<li><a href="http://oss.oetiker.ch/mrtg/">MRTG</a></li>
			<li><a href="http://atlee.ca/software/poster/">python-poster</a></li>
			<li><a href="http://code.google.com/p/python-twitter/">python-twitter</a></li>
			<li><a href="http://oss.oetiker.ch/rrdtool/prog/rrdpython.en.html">rrdpython</a></li>
			<li><a href="http://www.net-snmp.org/">net-snmp</a></li>
			<li><a href="http://redis.io/">redis</a></li>
		</ul>
	</div>
	<div class="span4">
		<h3>Source code</h3>

		<p>There's no need to keep <a href="https://github.com/ojarva/status.futurice.com">source code</a> of this service secret. You need your own backend services and credentials, though. Many parts are quick 
first versions, and there's always better way to do it. Feel free to fork, make improvements and create pull request. We're more than happy to merge improvements and cleanups.</p>

		<p>Also, deployed <a href="/sources/fetch_rt.py.html">RT code</a>, <a href="/sources/fetch_pingdom.py.html">Pingdom code</a> and <a href="/sources/index.php.html">index.php</a> are available for 
viewing.</p>

	</div>
</div>
