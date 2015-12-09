import pytest
from click.testing import CliRunner
from tsplk import cli
import os
import yaml
import shutil

_root = os.path.abspath(os.path.dirname(__file__))

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def project(request):
    project_name = "test"

    def tear_down():

        project_path = os.path.join(_root, project_name)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

    request.addfinalizer(tear_down)
    return project_name

input_platform_menu = ["ubuntu1404x64", "centos7x64"]
structure_menu = ["indexer-cluster", "search-head-pooling"]



@pytest.mark.parametrize("os_system, structure",
                         [
                             ("ubuntu1404x64", "indexer-cluster")
                         ])
def test_wiz(runner, project, os_system, structure):
    p_idx = input_platform_menu.index(os_system) + 1
    s_idx = structure_menu.index(structure) + 1

    result = runner.invoke(cli.main, ['wiz'],
                           input='%s\n%d\n%d\n\n\n\n' % (project, p_idx, s_idx))
    assert not result.exception
    assert result.exit_code == 0
    print(result.output.strip())
    generated_file_name = 'splunk.yml'
    project_path = os.path.join(_root, project)
    generated_file_name = os.path.join(project_path, generated_file_name)

    assert os.path.isdir(project_path)
    assert os.path.isfile(generated_file_name)

    with open(generated_file_name, 'r') as f:
        data = yaml.load(f)

    if structure == "indexer-cluster":
        assert data["instances"]["cluster-master"]["platform"] == os_system
        assert "splunk-cluster-master" in \
               data["instances"]["cluster-master"]["grains"]["role"]

        assert data["instances"]["cluster-slave-0"]["platform"] == os_system
        assert data["instances"]["cluster-slave-1"]["platform"] == os_system

        searchhead_1 = data["instances"]["cluster-searchhead-0"]
        searchhead_2 = data["instances"]["cluster-searchhead-1"]

        assert searchhead_1["platform"] == os_system
        assert searchhead_2["platform"] == os_system



