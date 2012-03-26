touch combined.css combined.min.css
chmod 644 combined.css combined.min.css
cat bootstrap.min.css  bootstrap-responsive.min.css  custom.css > combined.css
yui-compressor combined.css > combined.min.css
