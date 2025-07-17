py_arris_exporter
===============
This is a python script, installed into Docker, which facilitates scraping Arris S34 cablemodems for their relevant RF data and surfacing that to prometheus.

The metrics collected here were rooted in [PeterGrace/py_arris_exporter](https://github.com/PeterGrace/py_arris_exporter)'s SB6183 exporter, but the implementation of the HNAP client (which SB6183 doesn't use) was taken from [nickdepinet/arrismonitor](https://github.com/nickdepinet/arrismonitor), and then I rewrote the server to use prometheus_client. PeterGrace's grafana dashboard should still be compatible, but there are additional metrics available as well.

![Screenshot of grafana dashboard](/doc/ae-screenshot.png?raw=true "Screenshot")

## How to use
There are three methods one could use to run this software:

  * [Run the script on a machine locally](#local)
  * [Run the docker container on a docker host](#docker)
  * [Deploy to Kubernetes via Helm](#helm)

## local
One can install this app by running `pip install .` in the source directory.  If you're curious about prerequisites, check setup.py.  Once installed, executing `py_arris_exporter` will start a python webserver on port 9393.  Any request uri to the service will return a set of prometheus metrics.

## docker
You can also run this app as a docker container by executing `docker run -d -p9393:9393 petergrace/arris_exporter` which will spawn a container and daemonize, exposing the port on your local system at port 9393.  This is better if you don't want to commingle your python environment installs.

## helm
If you are leveraging kubernetes, there is a helm chart under the helm/ subdirectory of this repository where you can deploy petergrace/arris_exporter directly to your kubernetes cluster.  It will create a service called `arris-exporter` on a ClusterIP that you can then target with your prometheus install.


## prometheus configuration
Here's a snippet of my scrape config for prometheus inside of my kubernetes environment:

```
- job_name: 'arris'
  static_configs:
    - targets: ['arris-exporter:9393']
```

As you can see, it doesn't have many bells or whistles; it just reports the data I wanted to see to prometheus.

The environment variables `ARRIS_EXPORTER_PORT` (9393), `ARRIS_HOST` (192.168.100.1), `ARRIS_USER` (admin), `ARRIS_PASSWORD` (password) can all be set, otherwise they will use the paranthetical defaults.

## grafana config
In the grafana/ subdirectory, I have included my grafana dashboard json that I use to query the datapoints from prometheus, to make the screenshot shown above.
