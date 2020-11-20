# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)


def get_counter(check, metric_name, modifiers, global_options):
    """
    https://prometheus.io/docs/concepts/metric_types/#counter
    https://github.com/OpenObservability/OpenMetrics/blob/master/specification/OpenMetrics.md#counter-1
    """
    monotonic_count_method = check.monotonic_count
    metric_name = '{}.count'.format(metric_name)

    def counter(metric, sample_data, runtime_data):
        has_successfully_executed = runtime_data['has_successfully_executed']

        for sample, tags, hostname in sample_data:
            if sample.name.endswith('_total'):
                monotonic_count_method(
                    metric_name,
                    sample.value,
                    tags=tags,
                    hostname=hostname,
                    flush_first_value=has_successfully_executed,
                )

    del check
    del modifiers
    del global_options
    return counter
