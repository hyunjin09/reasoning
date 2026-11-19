"""Named vLLM worker extension; no callable/pickle transport required."""
from scripts.stage14d.attention_technical_v1 import configure_worker,collect_worker


def control_message(config):
    return 'stage14d_configure',(config,)


class TechnicalExtension:
    def stage14d_configure(self,config):return configure_worker(self,config)
    def stage14d_collect(self):return collect_worker(self)
