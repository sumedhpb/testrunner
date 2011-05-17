import unittest
import uuid
from TestInput import TestInputSingleton
import logger
import crc32
from mc_bin_client import MemcachedClient, MemcachedError
from membase.api.rest_client import RestConnection, RestHelper
from membase.helper.bucket_helper import BucketOperationHelper
from membase.helper.cluster_helper import ClusterOperationHelper
from membase.helper.rebalance_helper import RebalanceHelper
from memcached.helper.data_helper import MemcachedClientHelper

log = logger.Logger.get_logger()

class ReplicationTests(unittest.TestCase):
    servers = None
    keys = None
    clients = None
    bucket_name = None
    keys_updated = None
    log = None
    input = None


    def setUp(self):
        self.log = logger.Logger.get_logger()
        self.input = TestInputSingleton.input
        self.servers = self.input.servers
        #make sure the master node does not have any other node
        #loop through all nodes and remove those nodes left over
        #from previous test runs


    def test_failover_1_replica_0_1_percent(self):
        self._test_failover_body(fill_ram_percentage=0.1, number_of_replicas=1)

    def test_failover_1_replica_1_percent(self):
        self._test_failover_body(fill_ram_percentage=1, number_of_replicas=1)

    def test_failover_1_replica_10_percent(self):
        self._test_failover_body(fill_ram_percentage=10, number_of_replicas=1)

    def test_failover_1_replica_50_percent(self):
        self._test_failover_body(fill_ram_percentage=50, number_of_replicas=1)

    def test_failover_1_replica_99_percent(self):
        self._test_failover_body(fill_ram_percentage=99, number_of_replicas=1)


    def test_replication_1_replica_0_1_percent(self):
        self._test_body(fill_ram_percentage=0.1, number_of_replicas=1)

    def test_replication_1_replica_1_percent(self):
        self._test_body(fill_ram_percentage=1, number_of_replicas=1)

    def test_replication_1_replica_10_percent(self):
        self._test_body(fill_ram_percentage=10, number_of_replicas=1)

    def test_replication_1_replica_50_percent(self):
        self._test_body(fill_ram_percentage=50, number_of_replicas=1)

    def test_replication_1_replica_99_percent(self):
        self._test_body(fill_ram_percentage=99, number_of_replicas=1)


    def test_replication_2_replica_0_1_percent(self):
        self._test_body(fill_ram_percentage=0.1, number_of_replicas=2)

    def test_replication_2_replica_1_percent(self):
        self._test_body(fill_ram_percentage=1, number_of_replicas=2)

    def test_replication_2_replica_10_percent(self):
        self._test_body(fill_ram_percentage=10, number_of_replicas=2)

    def test_replication_2_replica_50_percent(self):
        self._test_body(fill_ram_percentage=50, number_of_replicas=2)

    def test_replication_2_replica_99_percent(self):
        self._test_body(fill_ram_percentage=99, number_of_replicas=2)


    def test_replication_3_replica_0_1_percent(self):
        self._test_body(fill_ram_percentage=0.1, number_of_replicas=3)

    def test_replication_3_replica_1_percent(self):
        self._test_body(fill_ram_percentage=1, number_of_replicas=3)

    def test_replication_3_replica_10_percent(self):
        self._test_body(fill_ram_percentage=10, number_of_replicas=3)

    def test_replication_3_replica_50_percent(self):
        self._test_body(fill_ram_percentage=50, number_of_replicas=3)

    def test_replication_3_replica_99_percent(self):
        self._test_body(fill_ram_percentage=99, number_of_replicas=3)

    def _check_vbuckets(self, number_of_replicas):
        #this method makes sure for each vbucket there is x number
        #of replicas
        #each vbucket should have x replicas
        rest = RestConnection(self.servers[0])
        buckets = rest.get_buckets()
        failed_verification = []
        for bucket in buckets:
            #get the vbuckets
            vbuckets = bucket.vbuckets
            index = 0
            for vbucket in vbuckets:
                if len(vbucket.replica) != number_of_replicas:
                    self.log.error("vbucket # {0} number of replicas : {1} vs expected : {2}".format(index,
                                                                                                     len(
                                                                                                         vbucket.replica)
                                                                                                     ,
                                                                                                     number_of_replicas))
                    failed_verification.append(index)
                index += 1
        if not failed_verification:
            self.fail("unable to verify number of replicas for {0} vbuckets".format(len(failed_verification)))

    #visit each node and get the data to verify the replication

    #update keys
    def _update_keys(self, version):
        client = MemcachedClient(self.servers[0].ip, 11220)
        rejected_keys = []
        #quit after updating max 100,000 keys
        self.updated_keys = []
        for key in self.keys:
            if len(self.updated_keys) > 10000:
                break
            vbucketId = crc32.crc32_hash(key) & 1023 # or & 0x3FF
            client.vbucketId = vbucketId
            value = '{0}'.format(version)
            try:
                client.append(key, value)
                self.updated_keys.append(key)
            except MemcachedError:
#                self.log.error(error)
#                self.log.error("unable to update key : {0} to bucket : {1}".format(key, client.vbucketId))
                rejected_keys.append(key)
        client.close()
        if len(rejected_keys) > 0:
            self.log.error("unable to update {0} keys".format(len(rejected_keys)))


    #verify

    def _verify_minimum_requirement(self, number_of_replicas):
        # we should at least have
        # x = ips.length
        #-
        self.assertTrue(len(self.servers) / (1 + number_of_replicas) >= 1,
                        "there are not enough number of nodes available")

    def _create_bucket(self, number_of_replicas=1,bucket_name = 'default'):
        self.bucket_name = bucket_name
        ip_rest = RestConnection(self.servers[0])
        info = ip_rest.get_nodes_self()
        bucket_ram = info.mcdMemoryReserved * 2 / 3
        self.log.info('creating bucket : {0}'.format(self.bucket_name))
        ip_rest.create_bucket(bucket=self.bucket_name,
                              ramQuotaMB=bucket_ram,
                              replicaNumber=number_of_replicas,
                              proxyPort=11220)
        msg = 'create_bucket succeeded but bucket {0} does not exist'.format(self.bucket_name)
        self.assertTrue(BucketOperationHelper.wait_for_bucket_creation(self.bucket_name,
                                                                       ip_rest), msg=msg)
        BucketOperationHelper.wait_till_memcached_is_ready_or_assert([self.servers[0]],
                                                                     bucket_port=11220,
                                                                     test=self)

    def _cleanup_cluster(self):
        BucketOperationHelper.delete_all_buckets_or_assert([self.servers[0]],test_case=self)
        ClusterOperationHelper.cleanup_cluster(self.servers)
        ClusterOperationHelper.wait_for_ns_servers_or_assert(self.servers,self)
        BucketOperationHelper.delete_all_buckets_or_assert(self.servers, self)

    def _verify_data(self, version):
        #verify all the keys
        master = self.servers[0]
        client = MemcachedClient(master.ip, 11220)
        index = 0
        all_verified = True
        keys_failed = []
        for key in self.updated_keys:
            try:
                index += 1
                vbucketId = crc32.crc32_hash(key) & 1023 # or & 0x3FF
                client.vbucketId = vbucketId
                flag, keyx, value = client.get(key=key)
                self.assertTrue(value.endswith(version),
                                msg='values do not match . key value should endwith {0}'.format(version))
                #                self.log.info("verified key #{0} : {1} value : {2}".format(index,key,value))
            except MemcachedError as error:
                self.log.error(error)
                self.log.error(
                    "memcachedError : {0} - unable to get a pre-inserted key : {0}".format(error.status, key))
                keys_failed.append(key)
                all_verified = False
                #            except :
                #                self.log.error("unknown errors unable to get a pre-inserted key : {0}".format(key))
                #                keys_failed.append(key)
                #                all_verified = False

        client.close()
        self.assertTrue(all_verified,
                        'unable to verify #{0} keys'.format(len(keys_failed)))


    def add_nodes_and_rebalance(self):
        master = self.servers[0]
        ClusterOperationHelper.add_all_nodes_or_assert(master,
                                                       self.servers,
                                                       self.input.membase_settings,
                                                       self)
        rest = RestConnection(master)
        nodes = rest.node_statuses()
        otpNodeIds = []
        for node in nodes:
            otpNodeIds.append(node.id)
        rebalanceStarted = rest.rebalance(otpNodeIds, [])
        self.assertTrue(rebalanceStarted,
                        "unable to start rebalance on master node {0}".format(master.ip))
        self.log.info('started rebalance operation on master node {0}'.format(master.ip))
        rebalanceSucceeded = rest.monitorRebalance()
        self.assertTrue(rebalanceSucceeded,
                        "rebalance operation for nodes: {0} was not successful".format(otpNodeIds))
        self.log.info('rebalance operaton succeeded for nodes: {0}'.format(otpNodeIds))
        #now remove the nodes
        #make sure its rebalanced and node statuses are healthy
        helper = RestHelper(rest)
        self.assertTrue(helper.is_cluster_healthy, "cluster status is not healthy")
        self.assertTrue(helper.is_cluster_rebalanced, "cluster is not balanced")


    #setup part1 : cleanup the clsuter
    #part 2: load data
    #part 3 : add nodes and rebalance
    #part 4 : update keys

    def _test_body(self, fill_ram_percentage=1, number_of_replicas=1):
        master = self.servers[0]
        self._verify_minimum_requirement(number_of_replicas)
        self._cleanup_cluster()
        self.log.info('cluster is setup')
        bucket_name = \
        'replica-{0}-ram-{1}-{2}'.format(number_of_replicas,
                                                                    fill_ram_percentage,
                                                                    uuid.uuid4())
        self._create_bucket(number_of_replicas=number_of_replicas,bucket_name=bucket_name)
        self.log.info('created the bucket')
        #let's use data_helper
        if fill_ram_percentage == 50:
            distribution = {1024: 0.4, 2 * 1024: 0.5, 10 * 1024: 0.1}
        elif fill_ram_percentage > 90:
            distribution = {5 * 1024: 0.4, 10 * 1024: 0.5, 20 * 1024: 0.1}
        else:
            distribution = {10: 0.2, 20: 0.5, 30: 0.25, 40: 0.05}
        MemcachedClientHelper.load_bucket(serverInfo=master,
                                          name=self.bucket_name,
                                          port=11220,
                                          ram_load_ratio=0.1,
                                          value_size_distribution=distribution,
                                          number_of_threads=40)
        self.add_nodes_and_rebalance()
        self.log.info('loading more data into the bucket')
        inserted_keys, rejected_keys =\
        MemcachedClientHelper.load_bucket_and_return_the_keys(serverInfo=master,
                                                              name=self.bucket_name,
                                                              port=11220,
                                                              ram_load_ratio=fill_ram_percentage,
                                                              value_size_distribution=distribution,
                                                              number_of_threads=40)
        self.keys = inserted_keys
        self.log.info('updating all keys by appending _20 to each value')
        self._update_keys('20')
        self.log.info('verifying keys now...._20')
        self._verify_data('20')
        rest = RestConnection(self.servers[0])
        self.assertTrue(RestHelper(rest).wait_for_replication(180),
                        msg="replication did not complete")
        self.assertTrue(RebalanceHelper.wait_till_total_numbers_match(master=master,
                                                                      servers=self.servers,
                                                                      bucket=self.bucket_name,
                                                                      port=11220,
                                                                      replica_factor=number_of_replicas,
                                                                      timeout_in_seconds=300),
                        msg="replication was completed but sum(curr_items) dont match the curr_items_total")
        self.log.info('updating all keys by appending _30 to each value')
        self._update_keys('30')
        self.log.info('verifying keys now...._20')
        self._verify_data('30')
        #flushing the node before cleaup
        MemcachedClientHelper.flush_bucket(self.servers[0].ip, self.bucket_name, 11220)

    def _test_failover_body(self, fill_ram_percentage=1, number_of_replicas=1):
        self._verify_minimum_requirement(number_of_replicas)
        self._cleanup_cluster()
        self.log.info('cluster is setup')
        bucket_name = \
        'failover-replica-count-{0}-ram-{1}-{2}'.format(number_of_replicas,
                                                                    fill_ram_percentage,
                                                                    uuid.uuid4())
        self._create_bucket(number_of_replicas=number_of_replicas,bucket_name=bucket_name)
        self.log.info('created the bucket')
        # tiny amount of data in the bucket
        distribution = {10: 0.2, 20: 0.5, 30: 0.25, 40: 0.05}
        MemcachedClientHelper.load_bucket(serverInfo=self.servers[0],
                                          name=self.bucket_name,
                                          port=11220,
                                          ram_load_ratio=0.1,
                                          value_size_distribution=distribution,
                                          number_of_threads=40)

        self.add_nodes_and_rebalance()
        self.log.info('loading more data into the bucket')
        distribution = {10: 0.2, 20: 0.5, 30: 0.25, 40: 0.05}
        inserted_keys, rejected_keys =\
        MemcachedClientHelper.load_bucket_and_return_the_keys(serverInfo=self.servers[0],
                                                              name=self.bucket_name,
                                                              port=11220,
                                                              ram_load_ratio=fill_ram_percentage,
                                                              value_size_distribution=distribution,
                                                              number_of_threads=40)

        self.keys = inserted_keys
        self.log.info('updating all keys by appending _20 to each value')
        self._update_keys('20')
        self.log.info('verifying keys now...._20')
        self._verify_data('20')
        rest = RestConnection(self.servers[0])
        self.assertTrue(RestHelper(rest).wait_for_replication(180),
                        msg="replication did not complete")
        self.log.info('updating all keys by appending _30 to each value')
        self._update_keys('30')
        self.log.info('verifying keys now...._20')
        self._verify_data('30')
        self.assertTrue(RestHelper(rest).wait_for_replication(180),
                        msg="replication did not complete")
        self.assertTrue(RebalanceHelper.wait_till_total_numbers_match(master=self.servers[0],
                                                                      servers=self.servers,
                                                                      bucket=self.bucket_name,
                                                                      port=11220,
                                                                      replica_factor=number_of_replicas,
                                                                      timeout_in_seconds=300),
                        msg="replication was completed but sum(curr_items) dont match the curr_items_total")
        #only remove one of the nodes
        
        second_node = self.servers[1]
        self.log.info('failing over node : {0} from the cluster'.format(second_node.ip))
        rest.fail_over('ns_1@{0}'.format(second_node.ip))
        self._verify_data('30')
        #flushing the node before cleaup
        MemcachedClientHelper.flush_bucket(self.servers[0].ip, self.bucket_name, 11220)

    def tearDown(self):
        self._cleanup_cluster()
        ClusterOperationHelper.wait_for_ns_servers_or_assert(self.servers,self)