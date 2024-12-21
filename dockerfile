# Use the official Spark image as the base image
FROM bitnami/spark:latest

# Switch to root user to allow modifications (if necessary)
USER root

# Install any additional dependencies you need
RUN apt-get update && apt-get install -y \
    bash \
    vim \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


RUN pip install markitdown

# Set environment variables if needed
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Set Bash as the entry point
ENTRYPOINT ["/bin/bash"]