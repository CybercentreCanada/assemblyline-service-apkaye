# Download the support files from Amazon S3
mkdir -p /opt/al_support
wget -O /opt/al_support/apktool.jar https://github.com/iBotPeaches/Apktool/releases/download/v$APKTOOL_VERSION/apktool_$APKTOOL_VERSION.jar
wget -O /tmp/dex2jar.zip https://github.com/pxb1988/dex2jar/releases/download/v$DEX2JAR_VERSION/dex-tools-v$DEX2JAR_VERSION.zip
wget -O /tmp/aapt2.jar https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/$AAPT2_VERSION/aapt2-$AAPT2_VERSION-linux.jar

unzip -o /tmp/dex2jar.zip -d /opt/al_support && mv /opt/al_support/dex-tools-v$DEX2JAR_VERSION /opt/al_support/dex-tools
chmod +x /opt/al_support/dex-tools/*.sh

unzip -o /tmp/aapt2.jar -d /opt/al_support/aapt2_dir && \
    mv /opt/al_support/aapt2_dir/aapt2 /opt/al_support/aapt2 && \
    rm -rf /opt/al_support/aapt2_dir
