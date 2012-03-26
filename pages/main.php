
      <div class="hero-unit">
        <h1>Status information from Futurice</h1>
        <p>This site shows some information from <a href="http://www.futurice.com/">Futurice</a> IT services. We try to promote transparency in everything we do, and publishing our server and network status is part of that.</p>
        <p><a class="btn btn-primary btn-large">Learn more &raquo;</a></p>
      </div>

<div class="row">
<div class="span12">
<div class="alert alert-error">
We are experiencing problems with netdisk access. We are working on it right now. (Last updated 15 minutes ago)
</div>

<div class="alert alert-info">
Next general maintenance break: Saturday 14.2.2012 from 16 onwards.
</div>

<div class="alert alert-info">
git server is down for maintenance on Thursday from 16:00. Expected downtime is 10 minutes, but might be longer. Changing https access from webdav to git-http-gateway.
</div>
</div>
</div>


      <div class="row">
        <div class="span4">
          <h2>Services</h2>
	<p>
<a href="#" rel="popover" data-original-title="What?" data-content="This is the number of services that seems to be down. Service might be down for maintenance, or monitoring might be broken."><span class="badge badge-error">1</span></a>
<a href="#" rel="popover" data-original-title="What?" data-content="This is the number of services that might be down. We can't detect everything with automatic monitoring, and sometimes monitoring system isn't sure."><span class="badge badge-warning">1</span></a>
<a href="#" rel="popover" data-original-title="What?" data-content="This is the number of services that seems to be up. Sometimes automatic monitoring doesn't catch all errors, so service might be inaccessible in fact."><span class="badge badge-success">35</span></a>
</p>
           <p>We are monitoring IT services and servers using Pingdom. Also, we have an internal Zabbix server, but unfortunately it contains great deal of confidential client information, so it's not available here.</p>
          <p><a class="btn" href="?page=services">View status &raquo;</a> 
<a class="btn btn-info" rel="popover" data-content="Pingdom provides API for fetching service information. Traditionally monitoring and uptime information is secret, but we didn't find any reason to continue with this tradition. Security can't depend on secret hostnames or so, so releasing status information is not a problem. If we are doing a good job with keeping our services up, we can be proud of it, and if not, we need to improve." data-original-title="How and why?" href="?page=what">How and why</a>
</p>
        </div>
        <div class="span4">
          <h2>Network map</h2>
	<p>Total traffic right now: 54Mbit/s <a href="#" rel="popover" data-original-title="Status" data-content="No link is saturated. All links do have spare capacity available. Also, response times are fast enough."><i class="icon-ok-circle"></i></a></p>
           <p>We have few offices and separate networks, so we need system for seeing overall status. For that reason we have network map. Published map is simplified version from what we have in the wall at the office.</p>
          <p><a class="btn" href="?page=netmap">View map &raquo;</a>
<a href="?page=what" class="btn btn-info" rel="popover" data-original-title="How and why" data-content="Data from switches and routers is collected with MRTG and aggregated to map with PHP weathermap. We have only simplified version here, because full version is quite large and complicated. We thought it might be interesting to see how our network is constructed.">How and why</a>
</p>
       </div>
        <div class="span4">
          <h2>IT tickets</h2>
	<p>
<a href="#" rel="popover" data-original-title="What?" data-content="This is the number of tickets received by IT team during last 7 days. Automatic tickets are excluded from this number."><span class="badge badge-info">55</span></a>
 tickets received this week</p>
          <p>Our IT team handles tasks and resolves all kind of problems from employees and clients. For that, we are using RT. We can't tell who sends messages and we don't have classifications for ticket complexity, but best we can do is to publish amount of handled tickets.</p>
          <p><a class="btn" href="?page=ittickets">View statistics &raquo;</a>
<a href="?page=what" class="btn btn-info" rel="popover" data-original-title="How and why" data-content="Sometimes when you see corporate IT offices, you think nothing ever happens. Based on surveys in Futurice (not conducted by IT team), that's not the case. But anyway, we thought it might be good idea to tell how much work we are doing. Also, these statistics filter out all automatic tickets and automatic replies." data-placement="top">How and why</a>
</p>
        </div>
      </div>

