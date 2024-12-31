[![Discord](https://img.shields.io/badge/chat-on%20discord-7289da.svg?sanitize=true)](https://discord.gg/GUAy9wErNu)
[![](https://img.shields.io/discord/908084610158714900)](https://discord.gg/GUAy9wErNu)
[![Static Badge](https://img.shields.io/badge/github-assemblyline-blue?logo=github)](https://github.com/CybercentreCanada/assemblyline)
[![Static Badge](https://img.shields.io/badge/github-assemblyline\_service\_apkaye-blue?logo=github)](https://github.com/CybercentreCanada/assemblyline-service-apkaye)
[![GitHub Issues or Pull Requests by label](https://img.shields.io/github/issues/CybercentreCanada/assemblyline/service-apkaye)](https://github.com/CybercentreCanada/assemblyline/issues?q=is:issue+is:open+label:service-apkaye)
[![License](https://img.shields.io/github/license/CybercentreCanada/assemblyline-service-apkaye)](./LICENSE)
# APKaye Service

This Assemblyline service analyzes Android APKs by decompilation and inspection.

## Service Details
APKaye employs the following 3 tools to do its analysis:

* Apktool
* dex2jar
* aapt

### Apktool

Apktool is used to pull apart the APK file. After the APK has been pulled apart, the service performs the following analysis:

* Static check for network indicators
* Gathers and analyses the different scripts and native binaries/libraries
* Validates signing certificate

### dev2jar

Dex2jar is optionally used for converting the .dex objects into JAR files to be analysed by the Assemblyline Espresso service.

### aapt

Aapt is used to analyse the metadata of the APK file. It performs the following tasks:

* Analyses the manifest for permissions used, SDK target, components used, ...
* Pulls out and analyses the different strings in the APK

## Image variants and tags

Assemblyline services are built from the [Assemblyline service base image](https://hub.docker.com/r/cccs/assemblyline-v4-service-base),
which is based on Debian 11 with Python 3.11.

Assemblyline services use the following tag definitions:

| **Tag Type** | **Description**                                                                                  |      **Example Tag**       |
| :----------: | :----------------------------------------------------------------------------------------------- | :------------------------: |
|    latest    | The most recent build (can be unstable).                                                         |          `latest`          |
|  build_type  | The type of build used. `dev` is the latest unstable build. `stable` is the latest stable build. |     `stable` or `dev`      |
|    series    | Complete build details, including version and build type: `version.buildType`.                   | `4.5.stable`, `4.5.1.dev3` |

## Running this service

This is an Assemblyline service. It is designed to run as part of the Assemblyline framework.

If you would like to test this service locally, you can run the Docker image directly from the a shell:

    docker run \
        --name Apkaye \
        --env SERVICE_API_HOST=http://`ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -f1 -d"/"`:5003 \
        --network=host \
        cccs/assemblyline-service-apkaye

To add this service to your Assemblyline deployment, follow this
[guide](https://cybercentrecanada.github.io/assemblyline4_docs/developer_manual/services/run_your_service/#add-the-container-to-your-deployment).

## Documentation

General Assemblyline documentation can be found at: https://cybercentrecanada.github.io/assemblyline4_docs/

# Service APKaye

Ce service d'Assemblyline analyse les APK Android par décompilation et inspection.

## Détails du service
APKaye utilise les 3 outils suivants pour effectuer son analyse :

* Apktool
* dex2jar
* aapt

### Apktool

Apktool est utilisé pour décomposer le fichier APK. Une fois l'APK décomposé, le service effectue les analyses suivantes :

* Vérification statique des indicateurs de réseau
* Rassemble et analyse les différents scripts et les binaires/bibliothèques natifs.
* Validation du certificat de signature

### dev2jar

Dex2jar est optionnellement utilisé pour convertir les objets .dex en fichiers JAR à analyser par le service Assemblyline Espresso.

### aapt

Aapt est utilisé pour analyser les métadonnées du fichier APK. Il effectue les tâches suivantes :

* Analyse le manifeste pour les permissions utilisées, la cible SDK, les composants utilisés, ...
* Extrait et analyse les différentes chaînes de caractères dans l'APK

## Variantes et étiquettes d'image

Les services d'Assemblyline sont construits à partir de l'image de base [Assemblyline service](https://hub.docker.com/r/cccs/assemblyline-v4-service-base),
qui est basée sur Debian 11 avec Python 3.11.

Les services d'Assemblyline utilisent les définitions d'étiquettes suivantes:

| **Type d'étiquette** | **Description**                                                                                                |  **Exemple d'étiquette**   |
| :------------------: | :------------------------------------------------------------------------------------------------------------- | :------------------------: |
|   dernière version   | La version la plus récente (peut être instable).                                                               |          `latest`          |
|      build_type      | Type de construction utilisé. `dev` est la dernière version instable. `stable` est la dernière version stable. |     `stable` ou `dev`      |
|        série         | Détails de construction complets, comprenant la version et le type de build: `version.buildType`.              | `4.5.stable`, `4.5.1.dev3` |

## Exécution de ce service

Ce service est spécialement optimisé pour fonctionner dans le cadre d'un déploiement d'Assemblyline.

Si vous souhaitez tester ce service localement, vous pouvez exécuter l'image Docker directement à partir d'un terminal:

    docker run \
        --name Apkaye \
        --env SERVICE_API_HOST=http://`ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -f1 -d"/"`:5003 \
        --network=host \
        cccs/assemblyline-service-apkaye

Pour ajouter ce service à votre déploiement d'Assemblyline, suivez ceci
[guide](https://cybercentrecanada.github.io/assemblyline4_docs/fr/developer_manual/services/run_your_service/#add-the-container-to-your-deployment).

## Documentation

La documentation générale sur Assemblyline peut être consultée à l'adresse suivante: https://cybercentrecanada.github.io/assemblyline4_docs/
