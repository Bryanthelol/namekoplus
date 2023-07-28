(function () {
    return {
        "port": 8125,
        "backends": ["./backends/repeater"],
        "repeater": [{host: 'statsd-exporter', port: 9125}],
    };
})();

