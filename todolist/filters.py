import logging


class HealthCheckFilter(logging.Filter):

    def filter(self, record) -> bool:  # noqa
        return record.getMessage().find('/ping/') == -1