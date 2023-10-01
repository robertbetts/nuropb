from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.queue import RabbitMQ
from diagrams.programming.language import Python
from diagrams.programming.framework import Spring
from diagrams.programming.framework import React

from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB

with (Diagram(direction="LR")):

    with Cluster("Application or Domain Service", direction="LR"):

        with Cluster("Micro-Service A"):
            service_a = [EC2("Worker"), EC2("Worker")]

        with Cluster("Micro-Service B"):
            service_b = [EC2("Worker"), EC2("Worker")]

        with Cluster("Service C"):
            service_c = [EC2("Worker")]

        broker = RabbitMQ("NuroPb Broker")
        gw = ELB("NuroPb Gateway")
        service_a >> broker << service_b
        gw >> Edge(color="darkgreen") << broker << service_c

    with Cluster("Application Consumers", direction="TB"):
        [Python("AI/ML/Jupyter"), Spring("Applications"), React("End Users")] >> gw

    with Cluster("Direct Broker Consumers", direction="TB"):
        broker << Python("NuroPb Consumer")

    with Cluster("Larger Mesh or Integrations", direction="TB"):
        enterprise_mesh = ELB("Enterprise Mesh")
        gw >> Edge(color="darkgreen") << enterprise_mesh
