ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH apkaye.apkaye.APKaye
ENV APKTOOL_VERSION 2.9.3
ENV DEX2JAR_VERSION 2.4
ENV AAPT2_VERSION 8.2.2-10154469

USER root

# The following line fix an issue with openjdk installation
RUN mkdir -p /usr/share/man/man1

# Get required apt packages
RUN apt-get update && apt-get install -y default-jre-headless java-common libc6-i386 lib32z1 lib32gcc1 unzip wget && rm -rf /var/lib/apt/lists/*

COPY setup_support.sh /tmp/setup_support.sh
RUN chmod +x /tmp/setup_support.sh && . /tmp/setup_support.sh

# Cleanup
RUN rm -rf /tmp/*

# Switch to assemblyline user
USER assemblyline

# Install python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --user --requirement requirements.txt && rm -rf ~/.cache/pip

# Copy APKaye service code
WORKDIR /opt/al_service
COPY . .

# Patch version in manifest
ARG version=4.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

# Switch to assemblyline user
USER assemblyline
