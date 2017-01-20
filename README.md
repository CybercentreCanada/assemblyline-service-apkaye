# APKaye Service

This Assemblyline service analyzes Android APKs. APKs are decompiled and inspected. Network indicators and information found in the APK manifest file is displayed.

**NOTE**: This service does not require you to buy any licence and is preinstalled and working after a default installation

## Tools wrapped

APKaye use the following 3 tools to do it's analysis:

* Apktool
* dex2jar
* aapt

### Apktool

Apktool is used to pull appart the APK file. After the APK has been pulled appart, the service performs the following analysis:

* Check statically for network indicators
* Gather and analyse the different scripts and native binaries/libraries
* Validate signing certificate

### dev2jar

Dex2jar is optionally used for converting the .dex objects into JAR files to be analysed by the Assemblyline Espresso service.

### aapt

Aapt is used to analyse the metadata of the APK file. It performs the following tasks:

* Analyses the manifest for permissions used, SDK target, components used, ...
* Pull out and analyses the different strings in the APK
