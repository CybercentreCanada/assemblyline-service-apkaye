import os
import shutil

import pytest

# Getting absolute paths, names and regexes
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(TEST_DIR)
SERVICE_CONFIG_NAME = "service_manifest.yml"
SERVICE_CONFIG_PATH = os.path.join(ROOT_DIR, SERVICE_CONFIG_NAME)
TEMP_SERVICE_CONFIG_PATH = os.path.join("/tmp", SERVICE_CONFIG_NAME)

# Samples that we will be sending to the service
sample1 = dict(
    sid=1,
    metadata={},
    service_name="apkaye",
    service_config={},
    fileinfo=dict(
        magic="ASCII text, with no line terminators",
        md5="1f09ecbd362fa0dfff88d4788e6f5df0",
        mime="text/plain",
        sha1="a649bf201cde05724e48f2d397a615b201be34fb",
        sha256="dadc624d4454e10293dbd1b701b9ee9f99ef83b4cd07b695111d37eb95abcff8",
        size=19,
        type="unknown",
    ),
    filename="dadc624d4454e10293dbd1b701b9ee9f99ef83b4cd07b695111d37eb95abcff8",
    min_classification="TLP:WHITE",
    max_files=501,  # TODO: get the actual value
    ttl=3600,
    safelist_config={"enabled": False, "hash_types": ["sha1", "sha256"], "enforce_safelist_service": False},
)


@pytest.fixture
def class_instance():
    temp_service_config_path = os.path.join("/tmp", SERVICE_CONFIG_NAME)
    try:
        # Placing the service_manifest.yml in the tmp directory
        shutil.copyfile(SERVICE_CONFIG_PATH, temp_service_config_path)

        from apkaye.apkaye import APKaye

        yield APKaye()
    finally:
        # Delete the service_manifest.yml
        os.remove(temp_service_config_path)


class TestAPKaye:

    @classmethod
    def setup_class(cls):
        # Placing the samples in the tmp directory
        samples_path = os.path.join(TEST_DIR, "samples")
        for sample in os.listdir(samples_path):
            sample_path = os.path.join(samples_path, sample)
            shutil.copyfile(sample_path, os.path.join("/tmp", sample))

    @classmethod
    def teardown_class(cls):
        # Cleaning up the tmp directory
        samples_path = os.path.join(TEST_DIR, "samples")
        for sample in os.listdir(samples_path):
            temp_sample_path = os.path.join("/tmp", sample)
            os.remove(temp_sample_path)

    @staticmethod
    def test_init(class_instance):
        assert class_instance.apktool_version == os.environ.get("APKTOOL_VERSION")
        assert class_instance.dex2jar_version == os.environ.get("DEX2JAR_VERSION")
        # Build ID should match between AAPT version comparison
        assert class_instance.aapt2_version.split("-")[1] == os.environ.get("AAPT2_VERSION").split("-")[1]

    @staticmethod
    def test_start():
        # TODO: somehow check if error was logged in service.log
        # service.start()
        pass

    @staticmethod
    def test_get_tool_version(class_instance):
        assert (
            class_instance.get_tool_version()
            == f"APKTOOL: {class_instance.apktool_version} - D2J: {class_instance.dex2jar_version} - AAPT2: {class_instance.aapt2_version}"
        )

    @staticmethod
    @pytest.mark.parametrize("sample", [sample1])
    def test_execute(sample, class_instance):
        # Imports required to execute the sample
        from assemblyline.odm.messages.task import Task as ServiceTask
        from assemblyline_v4_service.common.request import ServiceRequest
        from assemblyline_v4_service.common.task import Task

        # Creating the required objects for execution
        service_task = ServiceTask(sample1)
        task = Task(service_task)
        class_instance._task = task
        service_request = ServiceRequest(task)

        # Actually executing the sample
        task.service_config = {"resubmit_apk_as_jar": False}
        class_instance.execute(service_request)

    @staticmethod
    @pytest.mark.parametrize("apktool_out_dir,result", [("", None)])
    def test_validate_certs(apktool_out_dir, result, class_instance):
        class_instance.validate_certs(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apktool_out_dir,result", [("", None)])
    def test_find_scripts_and_exes(apktool_out_dir, result, class_instance):
        class_instance.find_scripts_and_exes(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @pytest.mark.parametrize("apktool_out_dir,result", [("", None)])
    def test_find_network_indicators(self, apktool_out_dir, result, class_instance):
        class_instance.find_network_indicators(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apktool_out_dir,result", [("", None)])
    def test_analyse_apktool_output(apktool_out_dir, result, class_instance):
        class_instance.analyse_apktool_output(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk,target_dir,work_dir,result", [("", "", "", None)])
    def test_run_apktool(apk, target_dir, work_dir, result, class_instance):
        class_instance.run_apktool(apk=apk, target_dir=target_dir, work_dir=work_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk,target", [("", "")])
    def test_get_dex(apk, target, class_instance):
        class_instance.get_dex(apk=apk, target=target)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk_file,target,result,val", [("", "", None, None)])
    def test_resubmit_dex2jar_output(apk_file, target, result, val, class_instance):
        class_instance.resubmit_dex2jar_output(apk_file=apk_file, target=target, result=result, request=val)
        pass

    @staticmethod
    @pytest.mark.parametrize("args", [[]])
    def test_run_appt(args, class_instance):
        class_instance.run_appt(args=args)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk_file,result", [("", None)])
    def test_run_badging_analysis(apk_file, result, class_instance):
        class_instance.run_badging_analysis(apk_file=apk_file, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk_file,result", [("", None)])
    def test_run_strings_analysis(apk_file, result, class_instance):
        class_instance.run_strings_analysis(apk_file=apk_file, result=result)
        pass
