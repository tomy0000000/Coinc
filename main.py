"""Script for Default keyword"""
import sys
import currency
from currency.workflow import Workflow3

def main(workflow):
    """The main workflow entry function"""
    # workflow.logger.info(sys.version)
    method = str(workflow.args.pop(0))
    if method in currency.__all__:
        workflow.run(getattr(currency, method))
    else:
        workflow.run(currency.help_me)

if __name__ == "__main__":
    WF = Workflow3(default_settings={
        "app_id": "",
        "precision": 2,
        "expire": 300,
        "base": "USD",
        "currencies": ["EUR", "CNY", "JPY", "GBP"]
    }, help_url="https://git.io/fjD6M")
    sys.exit(WF.run(main))
