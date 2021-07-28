ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH apkaye.apkaye.APKaye

USER root

# The following line fix an issue with openjdk installation
RUN mkdir -p /usr/share/man/man1

# Get required apt packages
RUN apt-get update && apt-get install -y default-jre-headless java-common libc6-i386 lib32z1 lib32gcc1 unzip wget && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/al_support

# Download the support files from Amazon S3
RUN wget -O /opt/al_support/apktool.jar https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.4.0.jar
RUN wget -O /tmp/dex2jar.zip https://github.com/pxb1988/dex2jar/releases/download/2.0/dex-tools-2.0.zip
RUN wget -O /tmp/aapt2.jar https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/3.5.1-5435860/aapt2-3.5.1-5435860-linux.jar

RUN unzip -o /tmp/dex2jar.zip -d /opt/al_support
RUN chmod +x /opt/al_support/dex2jar-2.0/*.sh

RUN unzip -o /tmp/aapt2.jar -d /opt/al_support/aapt2

# Cleanup
RUN rm -rf /tmp/*

# Copy APKaye service code
WORKDIR /opt/al_service
COPY . .

# Patch version in manifest
ARG version=4.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

# Switch to assemblyline user
USER assemblyline
