from tsplk.saltmaster_deployer import TerraformSaltMaster
import pytest


class TestTerraformSaltMaster:
    def test_is_master_up(self):
        sm = TerraformSaltMaster(dict())
        is_up = sm.is_master_up()

        assert not is_up

    def test_is_minions_up(self):
        sm = TerraformSaltMaster(dict())
        is_up = sm.is_minions_up()

        assert not is_up

    def test_up(self):
        sm = TerraformSaltMaster(dict())
        sm.up()

    def test_up_master(self):
        sm = TerraformSaltMaster(dict())
        sm.up_master()

    def test_up_minions(self):
        sm = TerraformSaltMaster(dict())
        sm.up_minion()

    def test_destroy_master(self):
        sm = TerraformSaltMaster(dict())
        sm.destroy_master()

    def test_destroy_minion(self):
        sm = TerraformSaltMaster(dict())
        sm.destroy_minion()

    def test_detroy(self):
        sm = TerraformSaltMaster(dict())
        sm.destroy()

    def test_plan_minion(self):
        sm = TerraformSaltMaster(dict())
        sm.plan_minions()

    def test_get_minion_info(self):
        sm = TerraformSaltMaster(dict())
        sm.get_minions_info()

    def test_get_public_ip(self):
        sm = TerraformSaltMaster(dict())
        sm.get_public_ip()




