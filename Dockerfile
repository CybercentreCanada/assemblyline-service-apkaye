ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH apkaye.apkaye.APKaye
ENV APKTOOL_VERSION 2.9.3
ENV DEX2JAR_VERSION 2.4

USER root

# The following line fix an issue with openjdk installation
RUN mkdir -p /usr/share/man/man1

# Get required apt packages
RUN apt-get update && apt-get install -y default-jre-headless java-common libc6-i386 lib32z1 lib32gcc1 unzip wget && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/al_support

# Download the support files from Amazon S3
RUN wget -O /opt/al_support/apktool.jar https://github.com/iBotPeaches/Apktool/releases/download/v$APKTOOL_VERSION/apktool_$APKTOOL_VERSION.jar
RUN wget -O /tmp/dex2jar.zip https://github.com/pxb1988/dex2jar/releases/download/v$DEX2JAR_VERSION/dex2jar-$DEX2JAR_VERSION.zip
RUN wget -O /tmp/aapt2.jar https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/7.3.0-8691043/aapt2-7.3.0-8691043-linux.jar

RUN unzip -o /tmp/dex2jar.zip -d /opt/al_support
RUN chmod +x /opt/al_support/dex-tools-$DEX2JAR_VERSION/*.sh

RUN unzip -o /tmp/aapt2.jar -d /opt/al_support/aapt2

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
