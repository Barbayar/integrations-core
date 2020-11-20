# (C) Datadog, Inc. 2020-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from datadog_checks.base import OpenMetricsBaseCheck


def get_check(instance=None, init_config=None):
    if instance is None:
        instance = {}
    if init_config is None:
        init_config = {}

    return OpenMetricsBaseCheck('test', init_config, [instance])
