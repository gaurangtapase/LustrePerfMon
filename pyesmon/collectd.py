# Copyright (c) 2017 DataDirect Networks, Inc.
# All Rights Reserved.
# Author: lixi@ddn.com
"""
Library for generating collectd config
"""
import collections

COLLECTD_CONFIG_TEMPLATE_FNAME = "collectd.conf.template"
COLLECTD_CONFIG_TEST_FNAME = "collectd.conf.test"
COLLECTD_CONFIG_FINAL_FNAME = "collectd.conf.final"
COLLECTD_INTERVAL_TEST = 1
COLLECTD_INTERVAL_FINAL = 60

class CollectdConfig(object):
    """
    Each collectd config has an object of this type
    """
    def __init__(self):
        self.cc_configs = collections.OrderedDict()
        self.cc_plugins = collections.OrderedDict()
        self.cc_checks = []
        self.cc_configs["Interval"] = COLLECTD_INTERVAL_FINAL
        self.cc_configs["WriteQueueLimitHigh"] = 1000000
        self.cc_configs["WriteQueueLimitLow"] = 800000
        self.cc_plugin_syslog("err")
        self.cc_plugin_memory()
        self.cc_plugin_cpu()
        self.cc_influxdb_host = None

    def cc_dump(self, fpath):
        """
        Dump the config to file
        """
        with open(fpath, "wt") as fout:
            fout.write("# Collectd config file generated automatcially by "
                       "ESMON\n# Please contact DDN Storage for information "
                       "and support\n\n")
            for config_name, config in self.cc_configs.iteritems():
                text = '%s %s\n' % (config_name, config)
                fout.write(text)
            fout.write("\n")

            for plugin_name, plugin_config in self.cc_plugins.iteritems():
                text = 'LoadPlugin %s\n' % plugin_name
                text += plugin_config + '\n'
                fout.write(text)

    def cc_plugin_syslog(self, log_level):
        """
        Config the syslog plugin
        """
        if log_level != "err" and log_level != "info" and log_level != "debug":
            return -1
        config = ('<Plugin "syslog">\n'
                  '    LogLevel %s\n'
                  '</Plugin>\n' % log_level)
        self.cc_plugins["syslog"] = config
        return 0

    def cc_plugin_memory_check(self):
        return 0

    def cc_plugin_memory(self):
        """
        Config the memory plugin
        """
        self.cc_plugins["memory"] = ""
        return 0

    def cc_plugin_write_tsdb(self, host):
        """
        Config the write TSDB plugin
        """
        config = ('<Plugin "write_tsdb">\n'
                  '    <Node>\n'
                  '        Host "%s\n'
                  '        Port "4232"\n'
                  '        DeriveRate true\n'
                  '    </Node>\n'
                  '</Plugin>\n' % host)
        self.cc_plugins["write_tsdb"] = config
        self.cc_influxdb_host = host
        self.cc_checks.append(self.cc_plugin_memory_check)
        return 0

    def cc_plugin_cpu(self):
        """
        Config the cpu plugin
        """
        config = """
LoadPlugin aggregation
<Plugin "aggregation">
    <Aggregation>
        Plugin "cpu"
        Type "cpu"
        GroupBy "Host"
        GroupBy "TypeInstance"
        CalculateAverage true
    </Aggregation>
</Plugin>

LoadPlugin match_regex
# Don't send "cpu-X" stats
<Chain "PostCache">
    <Rule>
        <Match regex>
            Plugin "^cpu$"
            PluginInstance "^[0-9]+$"
        </Match>
        <Target write>
            Plugin "aggregation"
        </Target>
        Target stop
    </Rule>
    Target "write"
</Chain>
"""
        self.cc_plugins["cpu"] = config
        return 0