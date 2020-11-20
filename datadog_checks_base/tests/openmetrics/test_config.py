# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import pytest

from ..utils import requires_py3
from .utils import get_check

pytestmark = [requires_py3, pytest.mark.openmetrics, pytest.mark.openmetrics_config]


class TestPrometheusEndpoints:
    def test_missing(self, dd_run_check):
        check = get_check({'prometheus_endpoints': []})

        with pytest.raises(Exception, match='^Setting `prometheus_endpoints` is required$'):
            dd_run_check(check, extract_message=True)

    def test_not_array(self, dd_run_check):
        check = get_check({'prometheus_endpoints': 9000})

        with pytest.raises(Exception, match='^Setting `prometheus_endpoints` must be an array$'):
            dd_run_check(check, extract_message=True)

    def test_endpoint_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': [9000]})

        with pytest.raises(Exception, match='^Endpoint #1 of setting `prometheus_endpoints` must be a string$'):
            dd_run_check(check, extract_message=True)

    def test_endpoint_empty_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['']})

        with pytest.raises(
            Exception, match='^Endpoint #1 of setting `prometheus_endpoints` must not be an empty string$'
        ):
            dd_run_check(check, extract_message=True)


class TestNamespace:
    def test_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'namespace': 9000})

        with pytest.raises(Exception, match='^Setting `namespace` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestRawMetricPrefix:
    def test_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'raw_metric_prefix': 9000})

        with pytest.raises(Exception, match='^Setting `raw_metric_prefix` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestHostnameLabel:
    def test_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'hostname_label': 9000})

        with pytest.raises(Exception, match='^Setting `hostname_label` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestHostnameFormat:
    def test_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'hostname_format': 9000})

        with pytest.raises(Exception, match='^Setting `hostname_format` must be a string$'):
            dd_run_check(check, extract_message=True)

    def test_no_placeholder(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'hostname_label': 'foo', 'hostname_format': 'bar'})

        with pytest.raises(
            Exception, match='^Setting `hostname_format` does not contain the placeholder `<HOSTNAME>`$'
        ):
            dd_run_check(check, extract_message=True)


class TestExcludeLabels:
    def test_not_array(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_labels': 9000})

        with pytest.raises(Exception, match='^Setting `exclude_labels` must be an array$'):
            dd_run_check(check, extract_message=True)

    def test_entry_invalid_type(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_labels': [9000]})

        with pytest.raises(Exception, match='^Entry #1 of setting `exclude_labels` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestRenameLabels:
    def test_not_mapping(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'rename_labels': 9000})

        with pytest.raises(Exception, match='^Setting `rename_labels` must be a mapping$'):
            dd_run_check(check, extract_message=True)

    def test_value_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'rename_labels': {'foo': 9000}})

        with pytest.raises(Exception, match='^Value for label `foo` of setting `rename_labels` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestExcludeMetrics:
    def test_not_array(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_metrics': 9000})

        with pytest.raises(Exception, match='^Setting `exclude_metrics` must be an array$'):
            dd_run_check(check, extract_message=True)

    def test_entry_invalid_type(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_metrics': [9000]})

        with pytest.raises(Exception, match='^Entry #1 of setting `exclude_metrics` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestExcludeMetricsByLabels:
    def test_not_mapping(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_metrics_by_labels': 9000})

        with pytest.raises(Exception, match='^Setting `exclude_metrics_by_labels` must be a mapping$'):
            dd_run_check(check, extract_message=True)

    def test_value_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_metrics_by_labels': {'foo': [9000]}})

        with pytest.raises(
            Exception, match='^Value #1 for label `foo` of setting `exclude_metrics_by_labels` must be a string$'
        ):
            dd_run_check(check, extract_message=True)

    def test_invalid_type(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'exclude_metrics_by_labels': {'foo': 9000}})

        with pytest.raises(
            Exception, match='^Label `foo` of setting `exclude_metrics_by_labels` must be an array or set to `true`$'
        ):
            dd_run_check(check, extract_message=True)


class TestTags:
    def test_not_array(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'tags': 9000})

        with pytest.raises(Exception, match='^Setting `tags` must be an array$'):
            dd_run_check(check, extract_message=True)

    def test_entry_invalid_type(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'tags': [9000]})

        with pytest.raises(Exception, match='^Entry #1 of setting `tags` must be a string$'):
            dd_run_check(check, extract_message=True)


class TestRawLineFilters:
    def test_not_array(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'raw_line_filters': 9000})

        with pytest.raises(Exception, match='^Setting `raw_line_filters` must be an array$'):
            dd_run_check(check, extract_message=True)

    def test_entry_invalid_type(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'raw_line_filters': [9000]})

        with pytest.raises(Exception, match='^Entry #1 of setting `raw_line_filters` must be a string$'):
            dd_run_check(check, extract_message=True)

    def test_invalid_pattern(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'raw_line_filters': ['\\1']})

        with pytest.raises(Exception, match='^invalid group reference'):
            dd_run_check(check, extract_message=True)


class TestMetrics:
    def test_not_array(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': 9000})

        with pytest.raises(Exception, match='^Setting `metrics` must be an array$'):
            dd_run_check(check, extract_message=True)

    def test_entry_invalid_type(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [9000]})

        with pytest.raises(Exception, match='^Entry #1 of setting `metrics` must be a string or a mapping$'):
            dd_run_check(check, extract_message=True)

    def test_mapped_value_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': 9000}]})

        with pytest.raises(
            Exception, match='^Value of entry `foo` of setting `metrics` must be a string or a mapping$'
        ):
            dd_run_check(check, extract_message=True)

    def test_config_name_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'name': 9000}}]})

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: field `name` must be a string$'
        ):
            dd_run_check(check, extract_message=True)

    def test_config_type_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 9000}}]})

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: field `type` must be a string$'
        ):
            dd_run_check(check, extract_message=True)

    def test_config_type_unknown(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'bar'}}]})

        with pytest.raises(Exception, match='^Error compiling transformer for metric `foo`: unknown type `bar`$'):
            dd_run_check(check, extract_message=True)


class TestTransformerCompilation:
    def test_temporal_percent_no_scale(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'temporal_percent'}}]})

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: the `scale` parameter is required$'
        ):
            dd_run_check(check, extract_message=True)

    def test_temporal_percent_unknown_scale(self, dd_run_check):
        check = get_check(
            {'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'temporal_percent', 'scale': 'bar'}}]}
        )

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: the `scale` parameter must be one of: '
        ):
            dd_run_check(check, extract_message=True)

    def test_temporal_percent_scale_not_int(self, dd_run_check):
        check = get_check(
            {'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'temporal_percent', 'scale': 1.23}}]}
        )

        with pytest.raises(
            Exception,
            match=(
                '^Error compiling transformer for metric `foo`: '
                'the `scale` parameter must be an integer representing parts of a second e.g. 1000 for millisecond$'
            ),
        ):
            dd_run_check(check, extract_message=True)

    def test_service_check_no_status_map(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'service_check'}}]})

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: the `status_map` parameter is required$'
        ):
            dd_run_check(check, extract_message=True)

    def test_service_check_status_map_not_dict(self, dd_run_check):
        check = get_check(
            {'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'service_check', 'status_map': 5}}]}
        )

        with pytest.raises(
            Exception,
            match='^Error compiling transformer for metric `foo`: the `status_map` parameter must be a mapping$',
        ):
            dd_run_check(check, extract_message=True)

    def test_service_check_status_map_empty(self, dd_run_check):
        check = get_check(
            {'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'service_check', 'status_map': {}}}]}
        )

        with pytest.raises(
            Exception,
            match='^Error compiling transformer for metric `foo`: the `status_map` parameter must not be empty$',
        ):
            dd_run_check(check, extract_message=True)

    def test_service_check_status_map_value_not_number(self, dd_run_check):
        check = get_check(
            {
                'prometheus_endpoints': ['test'],
                'metrics': [{'foo': {'type': 'service_check', 'status_map': {True: 'OK'}}}],
            }
        )

        with pytest.raises(
            Exception,
            match=(
                '^Error compiling transformer for metric `foo`: '
                'value `True` of parameter `status_map` does not represent an integer$'
            ),
        ):
            dd_run_check(check, extract_message=True)

    def test_service_check_status_map_status_not_string(self, dd_run_check):
        check = get_check(
            {
                'prometheus_endpoints': ['test'],
                'metrics': [{'foo': {'type': 'service_check', 'status_map': {'9000': 0}}}],
            }
        )

        with pytest.raises(
            Exception,
            match=(
                '^Error compiling transformer for metric `foo`: '
                'status `0` for value `9000` of parameter `status_map` is not a string$'
            ),
        ):
            dd_run_check(check, extract_message=True)

    def test_service_check_status_map_status_invalid(self, dd_run_check):
        check = get_check(
            {
                'prometheus_endpoints': ['test'],
                'metrics': [{'foo': {'type': 'service_check', 'status_map': {'9000': '0k'}}}],
            }
        )

        with pytest.raises(
            Exception,
            match=(
                '^Error compiling transformer for metric `foo`: '
                'invalid status `0k` for value `9000` of parameter `status_map`$'
            ),
        ):
            dd_run_check(check, extract_message=True)

    def test_metadata_label_not_string(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'metadata', 'label': 9000}}]})

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: the `label` parameter must be a string$'
        ):
            dd_run_check(check, extract_message=True)

    def test_metadata_no_label(self, dd_run_check):
        check = get_check({'prometheus_endpoints': ['test'], 'metrics': [{'foo': {'type': 'metadata'}}]})

        with pytest.raises(
            Exception, match='^Error compiling transformer for metric `foo`: the `label` parameter is required$'
        ):
            dd_run_check(check, extract_message=True)
