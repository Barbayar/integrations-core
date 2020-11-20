# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import re
from copy import deepcopy

from six import raise_from

from ....config import is_affirmative
from . import transformers

DEFAULT_METRIC_TYPE = 'native'


class MetricTransformer(object):
    def __init__(self, check, config):
        self.check = check
        self.cache_metric_wildcards = is_affirmative(config.get('cache_metric_wildcards', True))
        self.histogram_buckets_as_distributions = is_affirmative(
            config.get('histogram_buckets_as_distributions', False)
        )
        self.collect_histogram_buckets = self.histogram_buckets_as_distributions or is_affirmative(
            config.get('collect_histogram_buckets', True)
        )
        self.non_cumulative_histogram_buckets = self.histogram_buckets_as_distributions or is_affirmative(
            config.get('non_cumulative_histogram_buckets', False)
        )

        # Accessible to every transformer
        self.global_options = {
            'collect_histogram_buckets': self.collect_histogram_buckets,
            'histogram_buckets_as_distributions': self.histogram_buckets_as_distributions,
            'non_cumulative_histogram_buckets': self.non_cumulative_histogram_buckets,
        }

        metrics = config.get('metrics', [])
        if not isinstance(metrics, list):
            raise TypeError('Setting `metrics` must be an array')

        metrics_config = {}
        for i, entry in enumerate(metrics, 1):
            if isinstance(entry, str):
                metrics_config[entry] = {'name': entry, 'type': DEFAULT_METRIC_TYPE}
            elif isinstance(entry, dict):
                for key, value in entry.items():
                    if isinstance(value, str):
                        metrics_config[key] = {'name': value, 'type': DEFAULT_METRIC_TYPE}
                    elif isinstance(value, dict):
                        metrics_config[key] = value.copy()
                        metrics_config[key].setdefault('name', key)
                        metrics_config[key].setdefault('type', DEFAULT_METRIC_TYPE)
                    else:
                        raise TypeError(
                            'Value of entry `{}` of setting `metrics` must be a string or a mapping'.format(key)
                        )
            else:
                raise TypeError('Entry #{} of setting `metrics` must be a string or a mapping'.format(i))

        metrics_config = deepcopy(metrics_config)

        self.transformers = {}
        self.metric_patterns = []
        for raw_metric_name, config in metrics_config.items():
            escaped_metric_name = re.escape(raw_metric_name)

            if raw_metric_name != escaped_metric_name:
                self.metric_patterns.append(re.compile(raw_metric_name))
            else:
                try:
                    self.transformers[raw_metric_name] = self.compile_transformer(config)
                except Exception as e:
                    error = 'Error compiling transformer for metric `{}`: {}'.format(raw_metric_name, e)
                    raise_from(type(e)(error), None)

    def get(self, metric):
        metric_name = metric.name

        transformer = self.transformers.get(metric_name)
        if transformer is not None:
            return transformer
        elif self.metric_patterns:
            for metric_pattern in self.metric_patterns:
                if metric_pattern.search(metric_name):
                    transformer = self.compile_transformer({'name': metric_name, 'type': DEFAULT_METRIC_TYPE})
                    if self.cache_metric_wildcards:
                        self.transformers[metric_name] = transformer

                    return transformer

    def compile_transformer(self, config):
        metric_name = config.pop('name')
        if not isinstance(metric_name, str):
            raise TypeError('field `name` must be a string')

        metric_type = config.pop('type')
        if not isinstance(metric_type, str):
            raise TypeError('field `type` must be a string')

        factory = TRANSFORMERS.get(metric_type)
        if factory is None:
            raise ValueError('unknown type `{}`'.format(metric_type))

        return factory(self.check, metric_name, config, self.global_options)


def get_native_transformer(check, metric_name, modifiers, global_options):
    """
    Uses whatever the endpoint describes as the metric type.
    """
    # In theory the type of a metric exposed by an endpoint could change,
    # so this is used to stored the compiled transformers by type.
    transformer_cache = {}

    def native(metric, sample_data, runtime_data):
        transformer = transformer_cache.get(metric.type)
        if transformer is None:
            factory = NATIVE_TRANSFORMERS.get(metric.type)
            if factory is None:
                raise ValueError('Metric `{}` has unknown type `{}`'.format(metric.name, metric.type))

            transformer = factory(check, metric_name, modifiers, global_options)
            transformer_cache[metric.type] = transformer

        transformer(metric, sample_data, runtime_data)

    return native


# https://prometheus.io/docs/concepts/metric_types/
NATIVE_TRANSFORMERS = {
    'counter': transformers.get_counter,
    'gauge': transformers.get_gauge,
    'histogram': transformers.get_histogram,
    'summary': transformers.get_summary,
}

TRANSFORMERS = {
    'counter_gauge': transformers.get_counter_gauge,
    'metadata': transformers.get_metadata,
    'native': get_native_transformer,
    'service_check': transformers.get_service_check,
    'temporal_percent': transformers.get_temporal_percent,
    'time_elapsed': transformers.get_time_elapsed,
}
TRANSFORMERS.update(NATIVE_TRANSFORMERS)


# For documentation generation
class Transformers(object):
    pass


for transformer_name, transformer_factory in sorted(TRANSFORMERS.items()):
    setattr(Transformers, transformer_name, transformer_factory)
