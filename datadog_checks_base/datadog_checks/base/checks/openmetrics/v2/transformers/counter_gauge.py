# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)


def get_counter_gauge(check, metric_name, modifiers, global_options):
    """
    Send as both a `monotonic_count` suffixed by `.count` and a `gauge` suffixed by `.total`.
    """
    gauge_method = check.gauge
    monotonic_count_method = check.monotonic_count

    total_metric = '{}.total'.format(metric_name)
    count_metric = '{}.count'.format(metric_name)

    def counter_gauge(metric, sample_data, runtime_data):
        has_successfully_executed = runtime_data['has_successfully_executed']

        for sample, tags, hostname in sample_data:
            gauge_method(total_metric, sample.value, tags=tags, hostname=hostname)
            monotonic_count_method(
                count_metric,
                sample.value,
                tags=tags,
                hostname=hostname,
                flush_first_value=has_successfully_executed,
            )

    del check
    del metric_name
    del modifiers
    del global_options
    return counter_gauge
