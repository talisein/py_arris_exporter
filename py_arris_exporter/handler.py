import os
import logging
from .arris_client import ArrisClient

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, InfoMetricFamily, Histogram
from prometheus_client.registry import Collector


log = logging.getLogger('main')

ARRIS_URL = "http://192.168.100.1/RgConnect.asp"

LOGIN_LATENCY = Histogram('arris_login_latency_seconds', 'Time spent logging in')
COLLECT_LATENCY = Histogram('arris_collect_latency_seconds', 'Time spent collecting')

class ArrisCollector(Collector):
    def __init__(self):
        self.arris_hostname = os.getenv('ARRIS_HOST') or '192.168.100.1'
        self.arris_username = os.getenv('ARRIS_USER') or 'admin'
        self.arris_password = os.getenv('ARRIS_PASSWORD') or 'password'

    def describe(self):
        gauge_labels = ['index', 'modulation', 'channel_id', 'frequency']
        yield GaugeMetricFamily('arris_upstream_locked', '', labels=gauge_labels)
        yield GaugeMetricFamily('arris_upstream_power', 'Channel power in dBmV', labels=gauge_labels)
        yield GaugeMetricFamily('arris_upstream_symbol_rate', '', labels=gauge_labels)
        yield GaugeMetricFamily('arris_downstream_locked', '', labels=gauge_labels)
        yield CounterMetricFamily('arris_downstream_packets_corrected', '', labels=gauge_labels)
        yield CounterMetricFamily('arris_downstream_packets_uncorrectable', '', labels=gauge_labels)
        yield GaugeMetricFamily('arris_downstream_power', '', labels=gauge_labels)
        yield GaugeMetricFamily('arris_downstream_snr', '', labels=gauge_labels)
        yield InfoMetricFamily('arris_connection', '')
        yield InfoMetricFamily('arris_status_startup_sequence', '')
        yield GaugeMetricFamily('arris_connectivity_state', '')
        yield InfoMetricFamily('arris_software', '')

    @LOGIN_LATENCY.time()
    def do_login(self, c):
        login_result = c.login(self.arris_username, self.arris_password)
        if not login_result:
            log.error("Failed to login")
        return login_result

    def collect(self):
        c = ArrisClient(self.arris_hostname)
        self.do_login(c)
        return self.do_collect(c)

    @COLLECT_LATENCY.time()
    def do_collect(self, c):
        gauge_labels = ['index', 'modulation', 'channel_id', 'frequency']
        is_locked = lambda text: 1 if text == 'Locked' else 0

        gauge_upstream_locked = GaugeMetricFamily('arris_upstream_locked', '', labels=gauge_labels)
        gauge_upstream_power = GaugeMetricFamily('arris_upstream_power', 'Channel power in dBmV', labels=gauge_labels)
        gauge_upstream_symbol_rate = GaugeMetricFamily('arris_upstream_symbol_rate', '', labels=gauge_labels)

        infos = c.multiple_hnap_request(['GetCustomerStatusUpstreamChannelInfo', 'GetCustomerStatusDownstreamChannelInfo', 'GetCustomerStatusConnectionInfo', 'GetCustomerStatusStartupSequence', 'GetInternetConnectionStatus', 'GetCustomerStatusSoftware'])
        log.debug(f'INFOS: {infos}')
        for channel in infos['GetCustomerStatusUpstreamChannelInfo']:
            log.debug(f'UPSTREAM: {channel}')
            labels = [channel['Channel'], channel['Type'], channel['ID'], channel['Frequency']]
            gauge_upstream_locked.add_metric(labels, is_locked(channel['Status']))
            gauge_upstream_power.add_metric(labels, float(channel['Power']))
            gauge_upstream_symbol_rate.add_metric(labels, float(channel['Symbol Rate']))

        yield gauge_upstream_locked
        yield gauge_upstream_power
        yield gauge_upstream_symbol_rate

        gauge_downstream_locked = GaugeMetricFamily('arris_downstream_locked', '', labels=gauge_labels)
        gauge_corrected         = CounterMetricFamily('arris_downstream_packets_corrected', '', labels=gauge_labels)
        gauge_uncorrected       = CounterMetricFamily('arris_downstream_packets_uncorrectable', '', labels=gauge_labels)
        gauge_power             = GaugeMetricFamily('arris_downstream_power', '', labels=gauge_labels)
        gauge_snr               = GaugeMetricFamily('arris_downstream_snr', '', labels=gauge_labels)
        for channel in infos['GetCustomerStatusDownstreamChannelInfo']:
            log.debug(f'DOWNSTREAM: {channel}')
            labels = [channel['Channel'], channel['Modulation'], channel['ID'], channel['Frequency']]
            gauge_downstream_locked.add_metric(labels, is_locked(channel['Status']))
            gauge_corrected.add_metric(labels, float(channel['Corrected']))
            gauge_uncorrected.add_metric(labels, float(channel['Uncorrected']))
            gauge_power.add_metric(labels, float(channel['Power']))
            gauge_snr.add_metric(labels, float(channel['SNR']))

        yield gauge_downstream_locked
        yield gauge_corrected
        yield gauge_uncorrected
        yield gauge_power
        yield gauge_snr

        connection_info = infos['GetCustomerStatusConnectionInfo']
        log.debug(f'Connection Info: {connection_info}')
        del connection_info['CustomerCurSystemTime']
        yield InfoMetricFamily('arris_connection', '', value=connection_info)

        startup_sequence = infos['GetCustomerStatusStartupSequence']
        log.debug(f'Startup sequence: {startup_sequence}')
        yield InfoMetricFamily('arris_status_startup_sequence', '', value=startup_sequence)

        internet_connection = infos['GetInternetConnectionStatus']
        log.debug(f'Internet Connection: {internet_connection}')
        is_connected = lambda text: 1 if text == 'Connected' else 0
        yield GaugeMetricFamily('arris_connectivity_state', '', value=is_connected(internet_connection['InternetConnection']))

        software_info = infos['GetCustomerStatusSoftware']
        log.debug(f'Software Info: {software_info}')
        del software_info['CustomerConnSystemUpTime']
        yield InfoMetricFamily('arris_software', '', value=software_info)
