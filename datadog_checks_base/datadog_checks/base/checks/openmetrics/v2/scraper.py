# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import inspect
import re
from math import isinf, isnan

from prometheus_client.parser import text_fd_to_metric_families

from ....config import is_affirmative
from ....constants import ServiceCheck
from ....errors import ConfigurationError
from ....utils.http import RequestsWrapper
from .transform import MetricTransformer
from .utils import get_label_normalizer


class OpenMetricsScraper(object):
    SERVICE_CHECK_HEALTH = 'prometheus.health'

    # 32 KiB seems optimal, and is also the recommended chunk size of the Bittorrent protocol.
    STREAM_CHUNK_SIZE = 1024 * 32

    def __init__(self, check, endpoint, config):
        self.config = config

        # Save a reference to the check instance
        self.check = check

        # Parse the configuration
        self.endpoint = endpoint

        self.namespace = config.get('namespace', '')
        if not isinstance(self.namespace, str):
            raise ConfigurationError('Setting `namespace` must be a string')

        self.metric_transformer = MetricTransformer(self.check, config)

        self.raw_metric_prefix = config.get('raw_metric_prefix', '')
        if not isinstance(self.raw_metric_prefix, str):
            raise ConfigurationError('Setting `raw_metric_prefix` must be a string')

        self.enable_health_service_check = is_affirmative(config.get('enable_health_service_check', True))

        self.hostname_label = config.get('hostname_label', '')
        if not isinstance(self.hostname_label, str):
            raise ConfigurationError('Setting `hostname_label` must be a string')

        hostname_format = config.get('hostname_format', '')
        if not isinstance(hostname_format, str):
            raise ConfigurationError('Setting `hostname_format` must be a string')

        self.hostname_formatter = None
        if self.hostname_label and hostname_format:
            placeholder = '<HOSTNAME>'
            if placeholder not in hostname_format:
                raise ConfigurationError(
                    'Setting `hostname_format` does not contain the placeholder `{}`'.format(placeholder)
                )

            self.hostname_formatter = lambda hostname: hostname_format.replace('<HOSTNAME>', hostname, 1)

        exclude_labels = config.get('exclude_labels', [])
        if not isinstance(exclude_labels, list):
            raise ConfigurationError('Setting `exclude_labels` must be an array')

        self.exclude_labels = set()
        for i, entry in enumerate(exclude_labels, 1):
            if not isinstance(entry, str):
                raise ConfigurationError('Entry #{} of setting `exclude_labels` must be a string'.format(i))

            self.exclude_labels.add(entry)

        self.rename_labels = config.get('rename_labels', {})
        if not isinstance(self.rename_labels, dict):
            raise ConfigurationError('Setting `rename_labels` must be a mapping')

        for key, value in self.rename_labels.items():
            if not isinstance(value, str):
                raise ConfigurationError('Value for label `{}` of setting `rename_labels` must be a string'.format(key))

        exclude_metrics = config.get('exclude_metrics', [])
        if not isinstance(exclude_metrics, list):
            raise ConfigurationError('Setting `exclude_metrics` must be an array')

        self.exclude_metrics = set()
        self.exclude_metrics_pattern = None
        exclude_metrics_patterns = []
        for i, entry in enumerate(exclude_metrics, 1):
            if not isinstance(entry, str):
                raise ConfigurationError('Entry #{} of setting `exclude_metrics` must be a string'.format(i))

            escaped_entry = re.escape(entry)
            if entry == escaped_entry:
                self.exclude_metrics.add(entry)
            else:
                exclude_metrics_patterns.append(entry)

        if exclude_metrics_patterns:
            self.exclude_metrics_pattern = re.compile('|'.join(exclude_metrics_patterns))

        self.exclude_metrics_by_labels = {}
        exclude_metrics_by_labels = config.get('exclude_metrics_by_labels', {})
        if not isinstance(exclude_metrics_by_labels, dict):
            raise ConfigurationError('Setting `exclude_metrics_by_labels` must be a mapping')
        elif exclude_metrics_by_labels:
            for label, values in exclude_metrics_by_labels.items():
                if values is True:
                    self.exclude_metrics_by_labels[label] = lambda label_value: True
                elif isinstance(values, list):
                    for i, value in enumerate(values, 1):
                        if not isinstance(value, str):
                            raise ConfigurationError(
                                'Value #{} for label `{}` of setting `exclude_metrics_by_labels` '
                                'must be a string'.format(i, label)
                            )

                    self.exclude_metrics_by_labels[label] = (
                        lambda label_value, pattern=re.compile('|'.join(values)): pattern.search(label_value)
                        is not None
                    )
                else:
                    raise ConfigurationError(
                        'Label `{}` of setting `exclude_metrics_by_labels` '
                        'must be an array or set to `true`'.format(label)
                    )

        custom_tags = config.get('tags', [])
        if not isinstance(custom_tags, list):
            raise ConfigurationError('Setting `tags` must be an array')

        for i, entry in enumerate(custom_tags, 1):
            if not isinstance(entry, str):
                raise ConfigurationError('Entry #{} of setting `tags` must be a string'.format(i))

        # These will be applied only to service checks
        self.static_tags = ['endpoint:{}'.format(self.endpoint)]
        self.static_tags.extend(custom_tags)
        self.static_tags = tuple(self.static_tags)

        # These will be applied to everything except service checks
        self.tags = self.static_tags

        self.raw_line_filter = None
        raw_line_filters = config.get('raw_line_filters', [])
        if not isinstance(raw_line_filters, list):
            raise ConfigurationError('Setting `raw_line_filters` must be an array')
        elif raw_line_filters:
            for i, entry in enumerate(raw_line_filters, 1):
                if not isinstance(entry, str):
                    raise ConfigurationError('Entry #{} of setting `raw_line_filters` must be a string'.format(i))

            self.raw_line_filter = re.compile('|'.join(raw_line_filters))

        self.http = RequestsWrapper(config, self.check.init_config, self.check.HTTP_CONFIG_REMAPPER, self.check.log)

        # Explicitly set the content type we accept
        self.http.options['headers'].setdefault('Accept', 'text/plain')

        # Used for monotonic counts
        self.has_successfully_executed = False

        self.enable_telemetry = is_affirmative(config.get('telemetry', False))
        # Make every telemetry submission method a no-op to avoid many lookups of `self.enable_telemetry`
        if not self.enable_telemetry:
            for name, _ in inspect.getmembers(self, predicate=inspect.ismethod):
                if name.startswith('submit_telemetry_'):
                    setattr(self, name, lambda *args, **kwargs: None)

    def scrape(self):
        runtime_data = {'has_successfully_executed': self.has_successfully_executed, 'static_tags': self.static_tags}

        for metric in self.parse_metrics():
            transformer = self.metric_transformer.get(metric)
            if transformer is None:
                self.log.debug('Skipping metric `%s` as it is not defined in `metrics`', metric.name)
                continue

            transformer(metric, self.generate_sample_data(metric), runtime_data)

        self.has_successfully_executed = True

    def parse_metrics(self):
        line_streamer = self.stream_connection_lines()
        if self.raw_line_filter is not None:
            line_streamer = self.filter_connection_lines(line_streamer)

        for metric in text_fd_to_metric_families(line_streamer):
            self.submit_telemetry_number_of_total_metric_samples(metric)

            metric_name = metric.name
            if metric_name in self.exclude_metrics or (
                self.exclude_metrics_pattern is not None and self.exclude_metrics_pattern.search(metric_name)
            ):
                continue

            if self.raw_metric_prefix and metric_name.startswith(self.raw_metric_prefix):
                metric.name = metric_name[len(self.raw_metric_prefix) :]

            yield metric

    def generate_sample_data(self, metric):
        label_normalizer = get_label_normalizer(metric.type)

        for sample in metric.samples:
            value = sample.value
            if isnan(value) or isinf(value):
                self.log.debug('Ignoring sample for metric `%s` as it has an invalid value: %s', metric.name, value)
                continue

            tags = []
            skip_sample = False
            labels = sample.labels
            label_normalizer(labels)

            for label_name, label_value in labels.items():
                sample_excluder = self.exclude_metrics_by_labels.get(label_name)
                if sample_excluder is not None and sample_excluder(label_value):
                    skip_sample = True
                    break
                elif label_name in self.exclude_labels:
                    continue

                label_name = self.rename_labels.get(label_name, label_name)
                tags.append('{}:{}'.format(label_name, label_value))

            if skip_sample:
                continue

            tags.extend(self.tags)

            hostname = self.hostname
            if self.hostname_label and self.hostname_label in labels:
                hostname = labels[self.hostname_label]
                if self.hostname_formatter is not None:
                    hostname = self.hostname_formatter(hostname)

            self.submit_telemetry_number_of_processed_metric_samples()
            yield sample, tags, hostname

    def stream_connection_lines(self):
        with self.get_connection() as connection:
            for line in connection.iter_lines(chunk_size=self.STREAM_CHUNK_SIZE, decode_unicode=True):
                yield line

    def filter_connection_lines(self, line_streamer):
        for line in line_streamer:
            if not self.raw_line_filter.search(line):
                yield line

    def get_connection(self):
        try:
            response = self.send_request()
        except Exception:
            self.submit_health_check(ServiceCheck.CRITICAL)
            raise
        else:
            try:
                response.raise_for_status()
            except Exception:
                self.submit_health_check(ServiceCheck.CRITICAL)
                response.close()
                raise
            else:
                self.submit_health_check(ServiceCheck.OK)

                # Never derive the encoding from the locale
                if response.encoding is None:
                    response.encoding = 'utf-8'

                self.submit_telemetry_endpoint_response_size(response)
                return response

    def send_request(self, **kwargs):
        kwargs['stream'] = True
        return self.http.get(self.endpoint, **kwargs)

    def submit_health_check(self, status, **kwargs):
        if self.enable_health_service_check:
            self.service_check(self.SERVICE_CHECK_HEALTH, status, tags=self.static_tags, **kwargs)

    def submit_telemetry_number_of_total_metric_samples(self, metric):
        self.count('telemetry.metrics.input.count', len(metric.samples), tags=self.tags)

    def submit_telemetry_number_of_processed_metric_samples(self):
        self.count('telemetry.metrics.processed.count', 1, tags=self.tags)

    def submit_telemetry_endpoint_response_size(self, response):
        content_length = response.headers.get('Content-Length')
        if content_length is not None:
            content_length = int(content_length)
        else:
            content_length = len(response.content)

        self.gauge('telemetry.payload.size', content_length, tags=self.tags)

    def __getattr__(self, name):
        # Forward all unknown attribute lookups to the check instance
        attribute = getattr(self.check, name)
        setattr(self, name, attribute)
        return attribute
