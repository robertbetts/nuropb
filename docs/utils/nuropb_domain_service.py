from diagrams import Diagram, Cluster
from diagrams.onprem.queue import RabbitMQ
from diagrams.programming.language import Python
from diagrams.programming.framework import Spring
from diagrams.programming.framework import React

from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB

with Diagram("Logical Assembly", direction="LR"):

    with Cluster("Application or Domain Service"):

        gateway = ELB("NuroPb Gateway")

        with Cluster("Microservices", direction="LR"):
            broker = RabbitMQ("NuroPb Broker")
            EC2("Worker A") >> broker << EC2("Worker B")
            EC2("Worker C") >> broker << EC2("Worker D")

        gateway >> broker

    enterprise_mesh = ELB("Enterprise Mesh")

    [Python("AI/ML"), Spring("Application"), React("End Users")] >> gateway
    gateway >> enterprise_mesh


