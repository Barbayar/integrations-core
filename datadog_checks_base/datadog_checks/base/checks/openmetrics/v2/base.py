# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from collections import OrderedDict
from contextlib import contextmanager

from ....errors import ConfigurationError
from ... import AgentCheck
from .scraper import OpenMetricsScraper

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap


class OpenMetricsBaseCheckV2(AgentCheck):
    DEFAULT_METRIC_LIMIT = 2000

    def __init__(self, name, init_config, instances):
        super(OpenMetricsBaseCheckV2, self).__init__(name, init_config, instances)

        # All desired scraper configurations, which subclasses can override as needed
        self.scraper_configs = [self.instance]

        # All configured scrapers keyed by the endpoint
        self.scrapers = OrderedDict()

        self.check_initializations.append(self.configure_scrapers)

    def check(self, _):
        for endpoint, scraper in self.scrapers.items():
            self.log.info('Scraping Prometheus endpoint: %s', endpoint)

            with self.adopt_namespace(scraper.namespace):
                scraper.scrape()

    def configure_scrapers(self):
        scrapers = OrderedDict()

        for config in self.scraper_configs:
            endpoints = config.get('prometheus_endpoints', [])
            if not isinstance(endpoints, list):
                raise ConfigurationError('Setting `prometheus_endpoints` must be an array')
            elif not endpoints:
                raise ConfigurationError('Setting `prometheus_endpoints` is required')

            for i, endpoint in enumerate(endpoints, 1):
                if not isinstance(endpoint, str):
                    raise ConfigurationError(
                        'Endpoint #{} of setting `prometheus_endpoints` must be a string'.format(i)
                    )
                elif not endpoint:
                    raise ConfigurationError(
                        'Endpoint #{} of setting `prometheus_endpoints` must not be an empty string'.format(i)
                    )

                scrapers[endpoint] = self.create_scraper(endpoint, config)

        self.scrapers.clear()
        self.scrapers.update(scrapers)

    def create_scraper(self, endpoint, config):
        # Subclasses can override to return a custom scraper based on configuration
        return OpenMetricsScraper(self, endpoint, self.get_config_with_defaults(config))

    def get_config_with_defaults(self, config):
        return ChainMap(config, self.get_default_config())

    def get_default_config(self):
        return {}

    @contextmanager
    def adopt_namespace(self, namespace):
        old_namespace = self.__NAMESPACE__

        try:
            self.__NAMESPACE__ = namespace or old_namespace
            yield
        finally:
            self.__NAMESPACE__ = old_namespace
