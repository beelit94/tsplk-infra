from python_terraform import *
import os
import logging

cwd = os.path.dirname(os.path.abspath(__file__))
tf_folder = os.path.dirname(cwd)
logging.basicConfig(level=logging.DEBUG)

vars = {
    ""
}

class TestTsplkInfra(object):
    def test_plan(self):
        tf = Terraform(working_dir=tf_folder, var_file='test_var_file.json')
        ret, out, err = tf.plan(input=False)
        assert ret == 0, err

    def test_ssh(self):
        pass


