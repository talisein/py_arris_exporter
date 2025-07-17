"""The primary module for this skeleton application."""
import time
import os
import logging
from prometheus_client import start_http_server, REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR
from handler import ArrisCollector
import systemd.daemon

logging.basicConfig(level=logging.CRITICAL)

log = logging.getLogger('main')

REGISTRY.register(ArrisCollector())
REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)

def main():

    server_port = int(os.getenv('ARRIS_EXPORTER_PORT') or '9393')

    server, t = start_http_server(server_port)
    systemd.daemon.notify('READY=1')
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            server.shutdown()
            t.join()
            return

if __name__ == '__main__':
    main()
