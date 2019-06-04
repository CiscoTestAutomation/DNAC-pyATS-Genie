import os

from ats.datastructures.logic import And, Not, Or
from genie.harness.main import gRun

def main():
    test_path = os.path.dirname(os.path.abspath(__file__))

    gRun(trigger_uids=['TriggerUnconfigConfigDescriptionInterface'],
         trigger_datafile='trigger_datafile.yaml', devices=['uut'])
