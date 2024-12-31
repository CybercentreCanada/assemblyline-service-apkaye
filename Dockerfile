ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

# Python path to the service class from your service directory
ENV SERVICE_PATH apkaye.apkaye.APKaye
ENV APKTOOL_VERSION 2.9.3
ENV DEX2JAR_VERSION 2.4
ENV AAPT2_VERSION 8.2.2-10154469

# Install apt dependencies
USER root

# The following line fix an issue with openjdk installation
RUN mkdir -p /usr/share/man/man1

COPY pkglist.txt /tmp/setup/
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    $(grep -vE "^\s*(#|$)" /tmp/setup/pkglist.txt | tr "\n" " ") && \
    rm -rf /tmp/setup/pkglist.txt /var/lib/apt/lists/*

COPY setup_support.sh /tmp/setup_support.sh
RUN chmod +x /tmp/setup_support.sh && . /tmp/setup_support.sh
# Cleanup
RUN rm -rf /tmp/*

# Install python dependencies
USER assemblyline
COPY requirements.txt requirements.txt
RUN pip install \
    --no-cache-dir \
    --user \
    --requirement requirements.txt && \
    rm -rf ~/.cache/pip

# Copy service code
WORKDIR /opt/al_service
COPY . .

# Patch version in manifest
ARG version=1.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

# Switch to assemblyline user
USER assemblyline
