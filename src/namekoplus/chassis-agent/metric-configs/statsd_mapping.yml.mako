mappings:
% for config_dict in config_list:
- match: "${config_dict['statsd_prefix']}.${config_dict['stat_name']}"
  observer_type: summary
  name: "${config_dict['stat_name']}"
  labels:
    provider: "$2"
    outcome: "$3"
    job: "${config_dict['statsd_prefix']}"
  summary_options:
    quantiles:
      - quantile: 0.99
        error: 0.001
      - quantile: 0.95
        error: 0.01
      - quantile: 0.9
        error: 0.05
      - quantile: 0.5
        error: 0.005
    max_summary_age: 30s
    summary_age_buckets: 3
    stream_buffer_size: 1000
% endfor