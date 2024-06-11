import sys

from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Deployment
from diagrams.programming.language import Python
from diagrams.saas.cdn import Fastly

with Diagram("", filename=sys.argv[1], show=sys.argv[2].lower() == "true"):
    with Cluster("Rubin Science Platform"):
        datalinker = Deployment("datalinker")
        portal = Deployment("portal")
        tap = Deployment("tap")

    with Cluster("Roundtable"):
        ook = Deployment("ook")

    with Cluster("lsst.io"):
        dr1 = Fastly("dr1.lsst.io")

    documenteer = Python("documenteer")
    sdm_schemas = Python("sdm_schemas")

    documenteer >> dr1
    dr1 >> ook
    datalinker << ook
    sdm_schemas >> tap
    tap >> portal
    datalinker >> tap
