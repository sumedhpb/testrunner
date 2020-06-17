#!/usr/bin/python3

import abc

class Provider(metaclass=abc.ABCMeta):
    def __init__(self, access_key_id, bucket, endpoint, region, secret_access_key, staging_directory):
        """Instantiate a new 'Provider' object. Should only be created by implementing super classes. Defines all the
        required shared functionality between cloud providers.
        """
        self.access_key_id = access_key_id
        self.bucket = bucket
        self.endpoint = endpoint
        self.region = region
        self.secret_access_key = secret_access_key
        self.staging_directory = staging_directory

    @abc.abstractmethod
    def setup(self):
        """Run any pre-testing setup. For most cloud providers this will mean ensuring the bucket exists and is ready
        for cbbackupmgr to use.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def teardown(self, info, remote_client):
        """Run any post-testing teardown operations. For most cloud providers this will mean removing any objects
        created by cbbackupgmr.

        Each cloud provider should ensure that they use the common '_remove_staging_directory' function to cleanup the
        staging directory.
        """
        raise NotImplementedError

    def _remove_staging_directory(self, info, remote_client):
        if info in ('linux', 'mac'):
            command = f"rm -rf {self.staging_directory}"
            output, error = remote_client.execute_command(command)
            remote_client.log_command_output(output, error)
        elif info == 'windows':
            remote_client.remove_directory_recursive(self.staging_directory)
