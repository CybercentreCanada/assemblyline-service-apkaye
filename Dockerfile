FROM cccs/assemblyline-v4-service-base:latest

ENV SERVICE_PATH apkaye.APKaye

# Get required apt packages
RUN apt-get update && apt-get install -y \
  openjdk-8-jdk
  libc6-i386 \
  lib32z1 \
  lib32gcc1 \
  unzip

RUN mkdir -p /opt/al/support/apkaye

# Download the support files from Amazon S3
RUN wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.4.0.jar -P /opt/al/support/apkaye
#RUN git archive --remote=git://github.com/pxb1988/dex2jar.git HEAD:dex2jar/dex-tools /tmp
#RUN git clone https://github.com/pxb1988/dex2jar.git /tmp
RUN wget https://downloads.sourceforge.net/project/dex2jar/dex2jar-2.0.zip -P /tmp
#RUN aws s3 cp s3://assemblyline-support/dex-tools-2.0.zip /tmp
#RUN aws s3 cp s3://assemblyline-support/aapt.tgz /tmp
RUN wget https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/3.5.1-5435860/aapt2-3.5.1-5435860-linux.jar -P /tmp

RUN unzip -o /tmp/dex2jar-2.0.zip -d /tmp
RUN cp -R /tmp/dex2jar-2.0/ /opt/al/support/apkaye/
#RUN cp -R /tmp/dex2jar/ /opt/al/support/apkaye/
RUN chmod +x /opt/al/support/apkaye/dex2jar-2.0/*.sh
#RUN chmod -R +x /opt/al/support/apkaye/dex2jar/

#RUN tar -zxf /tmp/aapt.tgz -C /tmp
RUN cd /tmp
RUN jar xf aapt2-3.5.1-5435860-linux.jar
RUN mv /tmp/aapt2 /opt/al/support/apkaye/

# Cleanup
RUN rm -rf /tmp/*

# Switch to assemblyline user
USER assemblyline

# Copy APKaye service code
WORKDIR /opt/al_service
COPY . .