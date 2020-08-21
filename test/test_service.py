import os
from subprocess import call
import json
import pytest
import shutil

from apkaye.apkaye import APKaye
from assemblyline_v4_service.common.request import ServiceRequest
from assemblyline_v4_service.common.task import Task
from assemblyline.odm.messages.task import Task as ServiceTask


service = APKaye()
sample1 = Task(
    ServiceTask(
        dict(
            sid=1,
            metadata={},
            service_name='apkaye',
            service_config={},
            fileinfo=dict(
                magic='ASCII text, with no line terminators',
                md5='1f09ecbd362fa0dfff88d4788e6f5df0',
                mime='text/plain',
                sha1='a649bf201cde05724e48f2d397a615b201be34fb',
                sha256='dadc624d4454e10293dbd1b701b9ee9f99ef83b4cd07b695111d37eb95abcff8',
                size=19,
                type='unknown',
            ),
            filename='dadc624d4454e10293dbd1b701b9ee9f99ef83b4cd07b695111d37eb95abcff8',
            min_classification='TLP:WHITE',
            max_files=501,  # TODO: get the actual value
            ttl=3600,
        )
    )
)


class TestAPKaye:
    @classmethod
    def setup_class(cls):
        # Dockerfile stuff
        call(["sudo", "apt-get", "install", "-y", "openjdk-8-jre-headless", "java-common", "libc6-i386", "lib32z1", "lib32gcc1", "unzip", "wget"])
        call(["sudo", "mkdir", "-p", "/opt/al_support"])
        call(["sudo", "wget", "-O", "/opt/al_support/apktool.jar", "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.4.0.jar"])
        call(["sudo", "wget", "-O", "/tmp/dex2jar.zip", "https://github.com/pxb1988/dex2jar/releases/download/2.0/dex-tools-2.0.zip"])
        call(["sudo", "wget", "-O", "/tmp/aapt2.jar", "https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/3.5.1-5435860/aapt2-3.5.1-5435860-linux.jar"])
        call(["sudo", "unzip", "-o", "/tmp/dex2jar.zip", "-d", "/opt/al_support"])
        # call(["sudo", "chmod", "+x", "/opt/al_support/dex2jar-2.0/*.sh"])
        call(["sudo", "unzip", "-o", "/tmp/aapt2.jar", "-d", "/opt/al_support/aapt2"])
        call(["rm", "-rf", "/tmp/*"])

        # Placing the samples in the tmp directory
        samples_path = "test/samples"
        for sample in os.listdir(samples_path):
            sample_path = os.path.join(samples_path, sample)
            shutil.copyfile(sample_path, os.path.join("/tmp", sample))

    @classmethod
    def teardown_class(cls):
        # Cleaning up the tmp directory
        samples_path = "test/samples"
        for sample in os.listdir(samples_path):
            temp_sample_path = os.path.join("/tmp", sample)
            os.remove(temp_sample_path)
        call(["sudo", "rm", "-rf", "/opt/al_support"])

    @staticmethod
    def test_init():
        assert service.apktool == "/opt/al_support/apktool.jar"
        assert service.dex2jar == "/opt/al_support/dex2jar-2.0/d2j-dex2jar.sh"
        assert service.aapt == "/opt/al_support/aapt2/aapt2"

    @staticmethod
    def test_start():
        # TODO: somehow check if error was logged in service.log
        # service.start()
        pass

    @staticmethod
    def test_get_tool_version():
        assert service.get_tool_version() == "APKTOOL: 2.4.0 - D2J: 2.0 - AAPT2: 3.5.1-5435860"

    @staticmethod
    @pytest.mark.parametrize("task", [
        sample1
    ])
    def test_execute(task):
        # Actually executing the sample
        task.service_config = {"resubmit_apk_as_jar": False}
        service._task = task
        service.execute(ServiceRequest(task))

        # Get the result of execute() from the test method
        test_result = task.get_service_result()

        # Get the assumed "correct" result of the sample
        correct_result_path = os.path.join("test/results", task.file_name + ".json")
        with open(correct_result_path, "r") as f:
            correct_result = json.loads(f.read())
        f.close()

        # Assert that the appropriate sections of the dict are equal

        # Avoiding date in the response
        test_result_response = test_result.pop("response")
        correct_result_response = correct_result.pop("response")
        assert test_result == correct_result

        # Comparing everything in the response except for the date
        test_result_response["milestones"].pop("service_completed")
        correct_result_response["milestones"].pop("service_completed")
        assert test_result_response == correct_result_response

    @staticmethod
    @pytest.mark.parametrize("apktool_out_dir,result", [
        ("", None)
    ])
    def test_validate_certs(apktool_out_dir, result):
        service.validate_certs(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apktool_out_dir,result", [
        ("", None)
    ])
    def test_find_scripts_and_exes(apktool_out_dir, result):
        service.find_scripts_and_exes(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @pytest.mark.parametrize("apktool_out_dir,result", [
        ("", None)
    ])
    def test_find_network_indicators(self, apktool_out_dir, result):
        service.find_network_indicators(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apktool_out_dir,result", [
        ("", None)
    ])
    def test_analyse_apktool_output(apktool_out_dir, result):
        service.analyse_apktool_output(apktool_out_dir=apktool_out_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk,target_dir,work_dir,result", [
        ("", "", "", None)
    ])
    def test_run_apktool(apk, target_dir, work_dir, result):
        service.run_apktool(apk=apk, target_dir=target_dir, work_dir=work_dir, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk,target", [
        ("", "")
    ])
    def test_get_dex(apk, target):
        service.get_dex(apk=apk, target=target)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk_file,target,result,val", [
        ("", "", None, None)
    ])
    def test_resubmit_dex2jar_output(apk_file, target, result, val):
        service.resubmit_dex2jar_output(apk_file=apk_file, target=target, result=result, request=val)
        pass

    @staticmethod
    @pytest.mark.parametrize("args", [
        []
    ])
    def test_run_appt(args):
        service.run_appt(args=args)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk_file,result", [
        ("", None)
    ])
    def test_run_badging_analysis(apk_file, result):
        service.run_badging_analysis(apk_file=apk_file, result=result)
        pass

    @staticmethod
    @pytest.mark.parametrize("apk_file,result", [
        ("", None)
    ])
    def test_run_strings_analysis(apk_file, result):
        service.run_strings_analysis(apk_file=apk_file, result=result)
        pass
