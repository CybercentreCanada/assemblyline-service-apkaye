import os
import time
from subprocess import Popen, PIPE, call

from static import ALL_ANDROID_PERMISSIONS, ISO_LOCALES

from assemblyline.common.identify import fileinfo
from assemblyline.common.net import is_valid_domain, is_valid_ip, is_valid_email
from assemblyline.common.str_utils import safe_str
from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.result import Result, ResultSection, BODY_FORMAT, Heuristic


class APKaye(ServiceBase):
    def __init__(self, config=None):
        super(APKaye, self).__init__(config)
        self.apktool = self.config.get("apktool_path", None)
        self.dex2jar = self.config.get("dex2jar_path", None)
        self.aapt = self.config.get("aapt_path", None)

    def start(self):
        if not os.path.isfile(self.apktool) or not os.path.isfile(self.dex2jar) or not os.path.isfile(self.aapt):
            self.log.error("One or more of the service tools (APKTOOL, AAPT2, DEX2JAR) are missing. "
                           "The service will most likely fail.")

    def get_tool_version(self):
        return "APKTOOL: 2.4.0 - D2J: 2.0 - AAPT2: 3.5.1-5435860"

    def execute(self, request):
        result = Result()
        request.set_service_context(self.get_tool_version())

        apk = request.file_path
        filename = os.path.basename(apk)
        d2j_out = os.path.join(self.working_directory, f'{filename}.jar')
        apktool_out = os.path.join(self.working_directory, f'{filename}_apktool')

        self.run_badging_analysis(apk, result)
        self.run_strings_analysis(apk, result)
        self.run_apktool(apk, apktool_out, result)
        if request.get_param('resubmit_apk_as_jar'):
            self.resubmit_dex2jar_output(apk, d2j_out, result, request)

        request.result = result

    @staticmethod
    def validate_certs(apktool_out_dir: str, result: Result):
        has_cert = False
        for root, _, files in os.walk(os.path.join(apktool_out_dir, "original", "META-INF")):
            for f in files:
                cur_file = os.path.join(root, f)
                stdout, stderr = Popen(["keytool", "-printcert", "-file", cur_file],
                                       stderr=PIPE, stdout=PIPE).communicate()
                if stdout:
                    if "keytool error" not in stdout:
                        has_cert = True
                        issuer = ""
                        owner = ""
                        country = ""
                        valid_from = ""
                        valid_to = ""
                        valid_year_end = 0
                        valid_year_start = 0
                        valid_until_date = time.time()
                        play_store_min = 'Sat Oct 22 00:00:00 2033'
                        play_store_min_valid_date = time.mktime(time.strptime(play_store_min, "%a %b %d %H:%M:%S %Y"))

                        for line in stdout.splitlines():
                            if "Owner:" in line:
                                owner = line.split(": ", 1)[1]
                                country = owner.split("C=")
                                if len(country) != 1:
                                    country = country[1]
                                else:
                                    country = ""

                            if "Issuer:" in line:
                                issuer = line.split(": ", 1)[1]

                            if "Valid from:" in line:
                                valid_from = line.split(": ", 1)[1].split(" until:")[0]
                                valid_to = line.rsplit(": ", 1)[1]

                                valid_from_splitted = valid_from.split(" ")
                                valid_to_splitted = valid_to.split(" ")

                                valid_year_start = int(valid_from_splitted[-1])
                                valid_year_end = int(valid_to_splitted[-1])

                                valid_until = " ".join(valid_to_splitted[:-2] + valid_to_splitted[-1:])
                                valid_until_date = time.mktime(time.strptime(valid_until, "%a %b %d %H:%M:%S %Y"))

                        res_cert = ResultSection("Certificate Analysis", body=safe_str(stdout),
                                                 parent=result, body_format=BODY_FORMAT.MEMORY_DUMP)

                        res_cert.add_tag('cert.valid.start', valid_from)
                        res_cert.add_tag('cert.valid.end', valid_to)
                        res_cert.add_tag('cert.issues', issuer)
                        res_cert.add_tag('cert.owner', owner)

                        if owner == issuer:
                            ResultSection("Certificate is self-signed", parent=res_cert,
                                          heuristic=Heuristic(10))

                        if not country:
                            ResultSection("Certificate owner has no country", parent=res_cert,
                                          heuristic=Heuristic(11))

                        if valid_year_start < 2008:
                            ResultSection("Certificate valid before first android release", parent=res_cert,
                                          heuristic=Heuristic(12))

                        if valid_year_start > valid_year_end:
                            ResultSection("Certificate expires before validity date starts", parent=res_cert,
                                          heuristic=Heuristic(16))

                        if (valid_year_end - valid_year_start) > 30:
                            ResultSection("Certificate valid more then 30 years", parent=res_cert,
                                          heuristic=Heuristic(13))

                        if valid_until_date < play_store_min_valid_date:
                            ResultSection("Certificate not valid until minimum valid playstore date", parent=res_cert,
                                          heuristic=Heuristic(20))

                        if country:
                            try:
                                int(country)
                                is_int_country = True
                            except Exception:
                                is_int_country = False

                            if len(country) != 2 or is_int_country:
                                ResultSection("Invalid country code in certificate owner", parent=res_cert,
                                              heuristic=Heuristic(14))

                        if f != "CERT.RSA":
                            ResultSection(f"Certificate name not using conventional name: {f}", parent=res_cert,
                                          heuristic=Heuristic(15))

        if not has_cert:
            ResultSection("This APK is not signed", parent=result, heuristic=Heuristic(9))

    @staticmethod
    def find_scripts_and_exes(apktool_out_dir: str, result: Result):
        scripts = []
        executables = []
        apks = []

        # We are gonna do the full apktool output dir here but in case we want to do less,
        # you can edit the test_path list
        test_paths = [apktool_out_dir]
        for path in test_paths:
            for root, _, files in os.walk(path):
                for f in files:
                    if f.endswith(".smali"):
                        continue
                    cur_file = os.path.join(root, f)
                    tag = fileinfo(cur_file)['tag']

                    if "code/sh" in tag:
                        scripts.append(cur_file.replace(apktool_out_dir, ''))
                    if "exectable/linux" in tag:
                        executables.append(cur_file.replace(apktool_out_dir, ''))
                    if "android/apk" in tag:
                        executables.append(cur_file.replace(apktool_out_dir, ''))

        if scripts:
            res_script = ResultSection("Shell script(s) found inside APK", parent=result,
                                       heuristic=Heuristic(1))
            for script in sorted(scripts)[:20]:
                res_script.add_line(script)
            if len(scripts) > 20:
                res_script.add_line(f"and {len(scripts) - 20} more...")

        if executables:
            res_exe = ResultSection("Executable(s) found inside APK", parent=result,
                                    heuristic=Heuristic(2))
            for exe in sorted(executables)[:20]:
                res_exe.add_line(exe)
            if len(executables) > 20:
                res_exe.add_line(f"and {len(executables) - 20} more...")

        if apks:
            res_apk = ResultSection("Other APKs where found inside the APK", parent=result,
                                    heuristic=Heuristic(19))
            for apk in sorted(apks)[:20]:
                res_apk.add_line(apk)
            if len(apks) > 20:
                res_apk.add_line(f"and {len(apks) - 20} more...")

    @staticmethod
    def find_network_indicators(apktool_out_dir: str, result: Result):
        # Whitelist
        skip_list = [
            "android.intent",
            "com.google",
            "com.android",
        ]

        indicator_whitelist = [
            'google.to',
            'google.ttl',
            'google.delay',
            'google_tagmanager.db',
            'gtm_urls.db',
            'gtm.url',
            'google_tagmanager.db',
            'google_analytics_v4.db',
            'Theme.Dialog.Alert',
            'popupLocationInfo.gravity',
            'popupLocationInfo.displayId',
            'popupLocationInfo.left',
            'popupLocationInfo.top',
            'popupLocationInfo.right',
            'popupLocationInfo.bottom',
            'googleads.g.doubleclick.net',
            'ad.doubleclick.net',
            '.doubleclick.net',
            '.googleadservices.com',
            '.googlesyndication.com',
            'android.hardware.type.watch',
            'mraid.js',
            'google_inapp_purchase.db',
            'mobileads.google.com',
            'mobileads.google.com',
            'share_history.xml',
            'share_history.xml',
            'activity_choser_model_history.xml',
            'FragmentPager.SavedState{',
            'android.remoteinput.results',
            'android.people',
            'android.picture',
            'android.icon',
            'android.text',
            'android.title',
            'android.title.big',
            'FragmentTabHost.SavedState{',
            'android.remoteinput.results',
            'android.remoteinput.results',
            'android.remoteinput.results',
            'libcore.icu.ICU',
        ]

        file_list = []

        # Indicators
        url_list = []
        domain_list = []
        ip_list = []
        email_list = []

        # Build dynamic whitelist
        smali_dir = os.path.join(apktool_out_dir, "smali")
        for root, dirs, files in os.walk(smali_dir):
            if not files:
                continue
            else:
                skip_list.append(root.replace(smali_dir + "/", "").replace("/", "."))

            for cdir in dirs:
                skip_list.append(os.path.join(root, cdir).replace(smali_dir + "/", "").replace("/", "."))

        asset_dir = os.path.join(apktool_out_dir, "assets")
        if os.path.exists(asset_dir):
            for root, dirs, files in os.walk(asset_dir):
                if not files:
                    continue
                else:
                    for asset_file in files:
                        file_list.append(asset_file)
        skip_list = list(set(skip_list))

        # Find indicators
        proc = Popen(['grep', '-ER', r'(([[:alpha:]](-?[[:alnum:]])*)\.)*[[:alpha:]](-?[[:alnum:]])+\.[[:alpha:]]{2,}',
                      smali_dir], stdout=PIPE, stderr=PIPE)
        grep, _ = proc.communicate()
        for line in grep.splitlines():
            file_path, line = line.split(":", 1)

            if "const-string" in line or "Ljava/lang/String;" in line:
                data = line.split("\"", 1)[1].split("\"")[0]
                data_low = data.lower()
                data_split = data.split(".")
                if data in file_list:
                    continue
                elif data in indicator_whitelist:
                    continue
                elif data.startswith("/"):
                    continue
                elif len(data_split[0]) < len(data_split[-1]) and len(data_split[-1]) > 3:
                    continue
                elif data_low.startswith("http://") or data_low.startswith('ftp://') or data_low.startswith('https://'):
                    url_list.append(data)
                elif data.startswith('android.') and data_low != data:
                    continue
                elif "/" in data and "." in data and data.index("/") < data.index("."):
                    continue
                elif " " in data:
                    continue
                elif data_split[0] in ['com', 'org', 'net', 'java']:
                    continue
                elif data_split[-1].lower() in ['so', 'properties', 'zip', 'read', 'id', 'store',
                                                'name', 'author', 'sh', 'soccer', 'fitness', 'news', 'video']:
                    continue
                elif data.endswith("."):
                    continue
                else:
                    do_skip = False
                    for skip in skip_list:
                        if data.startswith(skip):
                            do_skip = True
                            break

                    if do_skip:
                        continue

                    data = data.strip(".")

                    if is_valid_domain(data):
                        domain_list.append(data)
                    elif is_valid_ip(data):
                        ip_list.append(data)
                    elif is_valid_email(data):
                        email_list.append(data)

        url_list = list(set(url_list))
        for url in url_list:
            dom_ip = url.split("//")[1].split("/")[0]
            if ":" in dom_ip:
                dom_ip = dom_ip.split(":")[0]

            if is_valid_ip(dom_ip):
                ip_list.append(dom_ip)
            elif is_valid_domain(dom_ip):
                domain_list.append(dom_ip)

        ip_list = list(set(ip_list))
        domain_list = list(set(domain_list))
        email_list = list(set(email_list))

        if url_list or ip_list or domain_list or email_list:
            res_net = ResultSection("Network indicator(s) found", parent=result, heuristic=Heuristic(3))

            if url_list:
                res_url = ResultSection("Found urls in the decompiled code", parent=res_net)
                count = 0
                for url in url_list:
                    count += 1
                    if count <= 20:
                        res_url.add_line(url)
                    res_url.add_tag('network.uri', url)
                if count > 20:
                    res_url.add_line(f"and {count - 20} more...")

            if ip_list:
                res_ip = ResultSection("Found IPs in the decompiled code", parent=res_net)
                count = 0
                for ip in ip_list:
                    count += 1
                    if count <= 20:
                        res_ip.add_line(ip)
                    res_ip.add_tag('network.ip', ip)
                if count > 20:
                    res_ip.add_line(f"and {count - 20} more...")

            if domain_list:
                res_domain = ResultSection("Found domains in the decompiled code", parent=res_net)
                count = 0
                for domain in domain_list:
                    count += 1
                    if count <= 20:
                        res_domain.add_line(domain)
                    res_domain.add_tag('network.domain', domain)
                if count > 20:
                    res_domain.add_line(f"and {count - 20} more...")

            if email_list:
                res_email = ResultSection("Found email addresses in the decompiled code", parent=res_net)
                count = 0
                for email in email_list:
                    count += 1
                    if count <= 20:
                        res_email.add_line(email)
                    res_email.add_tag('network.email.address', email)
                if count > 20:
                    res_email.add_line(f"and {count - 20} more...")

    def analyse_apktool_output(self, apktool_out_dir: str, result: Result):
        self.find_network_indicators(apktool_out_dir, result)
        self.find_scripts_and_exes(apktool_out_dir, result)
        self.validate_certs(apktool_out_dir, result)

    def run_apktool(self, apk: str, target_dir: str, result: Result):
        apktool = Popen(["java", "-jar", self.apktool, "--output", target_dir, "d", apk],
                        stdout=PIPE, stderr=PIPE, shell=True)
        apktool.communicate()
        if os.path.exists(target_dir):
            self.analyse_apktool_output(target_dir, result)

    @staticmethod
    def get_dex(apk: str, target: str):
        call(["unzip", "-o", apk, os.path.basename(target)], cwd=os.path.dirname(target))

    def resubmit_dex2jar_output(self, apk_file: str, target: str, result: Result, request):
        dex = os.path.join(self.working_directory, "classes.dex")
        self.get_dex(apk_file, dex)
        if os.path.exists(dex):
            d2j = Popen([self.dex2jar, "--output", target, dex],
                        stdout=PIPE, stderr=PIPE)
            d2j.communicate()
            if os.path.exists(target):
                res_sec = ResultSection("Classes.dex file was recompiled as a JAR and re-submitted for analysis")
                res_sec.add_line(f"JAR file resubmitted as: {os.path.basename(target)}")
                request.add_extracted(target, "Dex2Jar output JAR file")
                result.add_section(res_sec)

    def run_appt(self, args):
        cmd_line = [self.aapt]
        cmd_line.extend(args)
        proc = Popen(cmd_line, stdout=PIPE, stderr=PIPE, encoding='ISO-8859-1')
        return proc.communicate()

    def run_badging_analysis(self, apk_file: str, result: Result):
        badging_args = ['d', 'badging', apk_file]
        badging, errors = self.run_appt(badging_args)
        if not badging:
            return
        res_badging = ResultSection("Android application details")
        libs = []
        permissions = []
        components = []
        features = []
        pkg_version = None
        for line in badging.splitlines():
            if line.startswith("package:"):
                pkg_name = line.split("name='")[1].split("'")[0]
                pkg_version = line.split("versionCode='")[1].split("'")[0]
                res_badging.add_line(f"Package: {pkg_name} v.{pkg_version}")
                res_badging.add_tag('file.apk.pkg_name', pkg_name)
                res_badging.add_tag('file.apk.app.version', pkg_version)

            if line.startswith("sdkVersion:"):
                min_sdk = line.split(":'")[1][:-1]
                res_badging.add_line(f"Min SDK: {min_sdk}")
                res_badging.add_tag('file.apk.sdk.min', min_sdk)

            if line.startswith("targetSdkVersion:"):
                target_sdk = line.split(":'")[1][:-1]
                res_badging.add_line(f"Target SDK: {target_sdk}")
                res_badging.add_tag('file.apk.sdk.target', target_sdk)

            if line.startswith("application-label:"):
                label = line.split(":'")[1][:-1]
                res_badging.add_line(f"Default Label: {label}")
                res_badging.add_tag('file.apk.app.label', label)

            if line.startswith("launchable-activity:"):
                launch = line.split("name='")[1].split("'")[0]
                res_badging.add_line(f"Launchable activity: {launch}")
                res_badging.add_tag('file.apk.activity', launch)

            if line.startswith("uses-library-not-required:"):
                lib = line.split(":'")[1][:-1]
                if lib not in libs:
                    libs.append(lib)

            if line.startswith("uses-permission:") or line.startswith("uses-implied-permission:"):
                perm = line.split("name='")[1].split("'")[0]
                if perm not in permissions:
                    permissions.append(perm)

            if line.startswith("provides-component:"):
                component = line.split(":'")[1][:-1]
                if component not in components:
                    components.append(component)

            if "uses-feature:" in line or "uses-implied-feature:" in line:
                feature = line.split("name='")[1].split("'")[0]
                if feature not in features:
                    features.append(feature)

        if pkg_version is not None:
            pkg_version = int(pkg_version)
            if pkg_version < 15:
                ResultSection("Package version is suspiciously low", parent=res_badging,
                              heuristic=Heuristic(17))
            elif pkg_version > 999999999:
                ResultSection("Package version is suspiciously high", parent=res_badging,
                              heuristic=Heuristic(17))

        if libs:
            res_lib = ResultSection("Libraries used", parent=res_badging)
            for lib in libs:
                res_lib.add_line(lib)
                res_lib.add_tag('file.apk.used_library', lib)

        if permissions:
            res_permissions = ResultSection("Permissions used", parent=res_badging)
            dangerous_permissions = []
            unknown_permissions = []
            for perm in permissions:
                if perm in ALL_ANDROID_PERMISSIONS:
                    if 'dangerous' in ALL_ANDROID_PERMISSIONS[perm]:
                        dangerous_permissions.append(perm)
                    else:
                        res_permissions.add_line(perm)
                        res_permissions.add_tag('file.apk.permission', perm)
                else:
                    unknown_permissions.append(perm)

            if len(set(permissions)) < len(permissions):
                ResultSection("Some permissions are defined more then once", parent=res_badging,
                              heuristic=Heuristic(18))

            if dangerous_permissions:
                res_dangerous_perm = ResultSection("Dangerous permissions used", parent=res_badging,
                                                   heuristic=Heuristic(4))
                for perm in dangerous_permissions:
                    res_dangerous_perm.add_line(perm)
                    res_dangerous_perm.add_tag('file.apk.permission', perm)

            if unknown_permissions:
                res_unknown_perm = ResultSection("Unknown permissions used", parent=res_badging,
                                                 heuristic=Heuristic(5))
                for perm in unknown_permissions:
                    res_unknown_perm.add_line(perm)
                    res_unknown_perm.add_tag('file.apk.permission', perm)

        if features:
            res_features = ResultSection("Features used", parent=res_badging)
            for feature in features:
                res_features.add_line(feature)
                res_features.add_tag('file.apk.feature', feature)

        if components:
            res_components = ResultSection("Components provided", parent=res_badging)
            for component in components:
                res_components.add_line(component)
                res_components.add_tag('file.apk.provides_component', component)

        result.add_section(res_badging)

    def run_strings_analysis(self, apk_file, result: Result):
        string_args = ['d', 'strings', apk_file]
        strings, _ = self.run_appt(string_args)
        if not strings or strings == "String pool is unitialized.\n":
            ResultSection("No strings found in APK", body="This is highly unlikely and most-likely malicious.",
                          parent=result, heuristic=Heuristic(6))
        else:
            res_strings = ResultSection("Strings Analysis", parent=result, heuristic=Heuristic(7))

            config_args = ['d', 'configurations', apk_file]
            configs, _ = self.run_appt(config_args)
            languages = []
            for line in configs.splitlines():
                config = line.upper()
                if config in ISO_LOCALES:
                    languages.append(config)
                    res_strings.add_tag('file.apk.locale', config)

            data_line = strings.split("\n", 1)[0]
            count = int(data_line.split(" entries")[0].rsplit(" ", 1)[1])
            styles = int(data_line.split(" styles")[0].rsplit(" ", 1)[1])
            if count < 50:
                ResultSection("Low volume of strings, this is suspicious.", parent=res_strings,
                              body_format=BODY_FORMAT.MEMORY_DUMP, body=safe_str(strings))

            if len(languages) < 2:
                ResultSection("This app is not built for multiple languages. This is unlikely.",
                              parent=res_strings, heuristic=Heuristic(8))

            res_strings.add_line(f"Total string count: {count}")
            res_strings.add_line(f"Total styles: {styles}")
            if languages:
                res_strings.add_line(f"Languages: {', '.join(languages)}")
