"""Script for Default keyword"""
import sys
import currency
from currency.workflow import Workflow3

def main(workflow):
    """The main workflow entry function"""
    method = str(workflow.args.pop(0))
    if method in currency.__all__:
        workflow.run(getattr(currency, method))
    else:
        workflow.run(currency.help_me)

if __name__ == "__main__":
    WF = Workflow3(
        # update_settings={
        #     "github_slug": "tomy0000000/coon",
        #     "frequency": 7
        # },
        help_url="https://git.io/fjD6M")
    sys.exit(WF.run(main))
