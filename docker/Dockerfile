FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH alsvc_apkaye.apkaye.APKaye

# Get required apt packages
RUN apt-get update && apt-get install -y \
  libc6-i386 \
  lib32z1 \
  lib32gcc1 \
  unzip

RUN mkdir -p /opt/al/support/apkaye

# Download the support files from Amazon S3
RUN aws s3 cp s3://assemblyline-support/apktool_2.0.3.jar /opt/al/support/apkaye
RUN aws s3 cp s3://assemblyline-support/dex-tools-2.0.zip /tmp
RUN aws s3 cp s3://assemblyline-support/aapt.tgz /tmp

RUN unzip -o /tmp/dex-tools-2.0.zip -d /tmp
RUN cp -R /tmp/dex2jar-2.0/ /opt/al/support/apkaye/
RUN chmod +x /opt/al/support/apkaye/dex2jar-2.0/*.sh

RUN tar -zxf /tmp/aapt.tgz -C /tmp
RUN cp -R /tmp/aapt /opt/al/support/apkaye

# Cleanup
RUN rm -rf /tmp

# Switch to assemblyline user
USER assemblyline

# Copy APKaye service code
WORKDIR /opt/al/al_services/alsvc_apkaye
COPY . .