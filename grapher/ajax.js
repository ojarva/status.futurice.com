function getP(host, plugin) {
	getData(host, plugin, 'load');
}

function rmP(host, plugin) {
	getData(host, plugin, 'del');
}

// From http://stackoverflow.com/a/901144/592174
function getParameterByName(name)
{
  name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
  var regexS = "[\\?&]" + name + "=([^&#]*)";
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.search);
  if(results == null)
    return "";
  else
    return decodeURIComponent(results[1].replace(/\+/g, " "));
}

var xmlHttp

function getData(obj, id, action) {
	xmlHttp=GetXmlHttpObject();
	if (xmlHttp==null) {
		alert ("Your browser does not support AJAX!");
		return;
	}

	var url="plugin.php";
	url=url+"?h="+obj+"&p="+id+"&a="+action+"&tz="+getParameterByName("tz");
	xmlHttp.onreadystatechange=function(){setData(id)}
	xmlHttp.open("GET",url,true);
	xmlHttp.send(null);
}

function setData(obj) {
	if (xmlHttp.readyState==4) {
		div = document.getElementById(obj);

		div.innerHTML=xmlHttp.responseText;
	}
}

function GetXmlHttpObject() {
	var xmlHttp=null;
	try {
		// Firefox, Opera 8.0+, Safari
		xmlHttp=new XMLHttpRequest();
	} catch (e) {
		// Internet Explorer
		try {
			xmlHttp=new ActiveXObject("Msxml2.XMLHTTP");
		} catch (e) {
			xmlHttp=new ActiveXObject("Microsoft.XMLHTTP");
		}
	}
	return xmlHttp;
}
