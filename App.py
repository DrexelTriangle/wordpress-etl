import os
from Animator import Animator
from pathlib import Path
import json

class App:
    def __init__(self):
        self.animator = Animator()
        self.completedSteps = []

    def run(self, onLoad, onDone, func, *args, showDone: bool = True):
        result = self.animator.spinner(onLoad, onDone, func, *args, showDone=showDone)
        self.completedSteps.append(onDone)
        return result
    
    def printChecklist(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        checkmark = Animator.colorWrap('\033[32m', '✓')
        for step in self.completedSteps:
            text = Animator.colorWrap('\033[90m', step)
            print(f"{checkmark} {text}")
