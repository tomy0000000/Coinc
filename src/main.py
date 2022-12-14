# -*- coding: utf-8 -*-
"""Script for Default keyword"""
import sys

import coinc
from workflow import Workflow3
from workflow.util import reload_workflow


def main(workflow):
    """The main workflow entry function"""
    method = str(workflow.args.pop(0))
    if coinc.utils.manual_update_patch(workflow):
        reload_workflow()
        workflow.logger.info("Workflow Reloaded")
    if method in coinc.__all__:
        workflow.run(getattr(coinc, method))
    else:
        workflow.run(coinc.help_me)


if __name__ == "__main__":
    WF = Workflow3(
        default_settings={"favorites": ["EUR", "CNY", "JPY", "GBP"]},
        update_settings={"github_slug": "tomy0000000/Coinc", "frequency": 7},
        help_url="https://github.com/tomy0000000/Coinc/wiki/User-Guide",
    )
    sys.exit(WF.run(main))
