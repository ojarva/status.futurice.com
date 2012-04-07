<?php

# Collectd Redis plugin

require_once 'conf/common.inc.php';
require_once 'type/Default.class.php';
require_once 'type/GenericStacked.class.php';
require_once 'type/Uptime.class.php';

require_once 'inc/collectd.inc.php';


$obj = new Type_Default($CONFIG);
switch($obj->args['type']) {
	case 'df':
		$obj->data_sources = array('used', 'free');
		$obj->ds_names = array(
			'used' => "Used",
			'free' => "Free",
		);
		$obj->colors = array(
			'used' => 'ff0000',
			'free' => '00ff00',
                );
		$obj->rrd_title = sprintf('Used memory (MB)', $obj->args['pinstance']);
		$obj->rrd_vertical = 'Memory usage (B)';
		$obj->rrd_format = '%5.1lf%sB';
		$obj->scale = '0.001';
	break;
	case 'memcached_items':
		$obj->data_sources = array('value');
		$obj->ds_names = array(
			'value' => "Value",
		);
		$obj->colors = array(
			'value' => '00ff00',
                );
		$obj->rrd_title = sprintf('Number of items', $obj->args['pinstance']);
		$obj->rrd_vertical = 'Items';
		$obj->rrd_format = '%5.1lf%s';
		$obj->scale = '0.001';
	break;
	case 'files':
		$obj->data_sources = array('value');
		$obj->ds_names = array(
			'value' => "Value",
		);
		$obj->colors = array(
			'value' => '00ff00',
                );
		$obj->rrd_title = sprintf('Unsaved changes', $obj->args['pinstance']);
		$obj->rrd_vertical = 'Number of unsaved items';
		$obj->rrd_format = '%5.1lf%s';
		$obj->scale = '0.001';
	break;
	case 'uptime':
		$obj = new Type_Uptime($CONFIG);
		$obj->data_sources = array('value');
		$obj->ds_names = array(
		        'value' => 'Current',
		);
		$obj->colors = array(
		        'value' => '00e000',
		);
		$obj->rrd_title = 'Redis uptime';
		$obj->rrd_vertical = 'Days';
		$obj->rrd_format = '%.1lf';
	break;
	case 'memcached_connections':
                $obj->data_sources = array('value');
                $obj->ds_names = array(
                        'value' => 'Conns/s',
                );
                $obj->colors = array(
                        'value' => '00b000',
                );
                $obj->rrd_title = sprintf('Redis connections');
                $obj->rrd_vertical = 'Conns/s';
		$obj->rrd_format = '%5.1lf';

	break;

	case 'memcached_command':
		$obj->data_sources = array('value');
		$obj->ds_names = array(
			'value' => "Value",
		);
		$obj->colors = array(
			'value' => '00ff00',
                );
		$obj->rrd_title = sprintf('Number of commands processed', $obj->args['pinstance']);
		$obj->rrd_vertical = 'Commands';
		$obj->rrd_format = '%5.1lf%s';
		$obj->scale = '0.001';
	break;

        default:
		$obj->data_sources = array('value');
		$obj->ds_names = array(
			'value' => "Value",
		);
		$obj->colors = array(
			'value' => '00ff00',
                );
		$obj->rrd_title = sprintf('?', $obj->args['pinstance']);
		$obj->rrd_vertical = '?';
		$obj->rrd_format = '%5.1lf%s?';
		$obj->scale = '0.001';
	break;
}
$obj->width = $width;
$obj->heigth = $heigth;

collectd_flush($obj->identifiers);
$obj->rrd_graph();
