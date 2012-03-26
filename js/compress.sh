touch combined.min.js combined.js services.min.js
chmod 600 *.js compress.sh
chmod 644 combined.min.js combined.js services.min.js
ls ???-*
cat ???-*.js > combined.js
yui-compressor combined.js >combined.min.js
yui-compressor services.js > services.min.js
