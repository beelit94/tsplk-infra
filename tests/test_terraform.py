from tsplk.terraform import Terraform
import pytest
import os


@pytest.fixture(scope="module")
def terraform_file(request):
    file_name = 'test.tf'

    data = \
        'provider "docker" {\n' \
        '  host = "tcp://192.168.99.100:2376/" \n' \
        '}\n' \
        '\n' \
        'resource "docker_image" "ubuntu" {\n' \
        '  name = "ubuntu:precise" \n' \
        '}\n' \
        '\n' \
        'resource "docker_container" "ubuntu" {\n' \
        '  name = "foo"\n' \
        '  image = "${docker_image.ubuntu.latest}"\n' \
        '  provisioner "local-exec" {\n' \
        '    command = "echo awesome"\n' \
        '  }\n' \
        '}\n' \
        '\n' \
        # 'resource "null-resource" "test-execute"{\n' \
        # '  provisioner "local-exec" {\n' \
        # '    command = "echo awesome"\n' \
        # '  }\n' \
        # '}\n'

    with open(file_name, 'w') as f:
        f.write(data)

    # def tear_down():
    #     os.remove(file_name)
    #
    # request.addfinalizer(tear_down)
    return file_name


class TestTerraform:

    def test_apply(self, terraform_file):
        t = Terraform()
        return_code, out, err = t.apply()
        assert return_code == 0, "%s %s" % (out, err)
        assert 'awesome' in out, "%s %s" % (out, err)

    def test_destroy(self):
        pass

    def test_refresh(self):
        pass

    def test_read_state(self):
        pass

    def test_is_any_aws_instance_alive(self):
        pass

    def test_get_aws_instances(self):
        pass

    def test_get_aws_instance(self):
        pass

    def test_get_output_value(self):
        pass